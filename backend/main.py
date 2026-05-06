from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from schemas import DisasterInput, ResourceUpdate, ShelterUpdate
from simulator import run_simulation
from scoring import score_all_paths, get_risk_level, compute_risk_score, get_score_breakdown
from route_planner import score_routes
from database import (
    init_db, get_all_simulations, get_simulation_by_id,
    save_resource_update, get_all_resources, save_shelter, get_all_shelters,
    get_resources_dict
)
from llm_service import is_ollama_available, llm_generate_report, OLLAMA_MODEL
from services.email_service import send_email_alert, build_email_content
from services.sms_service import send_alerts, build_team_alert, build_public_alert, get_demo_recipients
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="CrisisMind AI", version="2.0.0")

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173"
).split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


@app.get("/")
def health_check():
    return {"message": "CrisisMind AI LangGraph backend is running"}


# ── LLM endpoints ─────────────────────────────────────────────────────────────

@app.get("/llm/status")
def llm_status():
    available = is_ollama_available()
    return {
        "ollama_available": available,
        "model": OLLAMA_MODEL if available else None,
        "mode": "LLM-Enhanced" if available else "Rule-Based Fallback",
    }


class ReportRequest(BaseModel):
    simulation_id: str


@app.post("/llm/report")
def generate_report(req: ReportRequest):
    result = get_simulation_by_id(req.simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    report, llm_used = llm_generate_report(result)
    return {
        "simulation_id": req.simulation_id,
        "report": report,
        "llm_used": llm_used,
        "model": OLLAMA_MODEL if llm_used else "rule-based",
    }


# ── Resource endpoints ─────────────────────────────────────────────────────────

@app.post("/resources/update")
def update_resources(data: ResourceUpdate):
    payload = {k: v for k, v in data.model_dump().items() if k not in ("role", "location") and v is not None}
    save_resource_update(data.role, data.location, payload)
    return {"message": "Resource update saved successfully", "role": data.role, "location": data.location}


@app.get("/resources")
def get_resources():
    return {"resources": get_all_resources(), "shelters": get_all_shelters()}


@app.post("/shelters/update")
def update_shelter(data: ShelterUpdate):
    save_shelter(data.model_dump())
    return {"message": "Shelter updated successfully", "name": data.name}


# ── Simulation endpoints ───────────────────────────────────────────────────────

@app.post("/simulate")
def simulate(data: DisasterInput):
    try:
        result = run_simulation(data.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
def history():
    return get_all_simulations()


@app.get("/simulation/{simulation_id}")
def get_simulation(simulation_id: str):
    result = get_simulation_by_id(simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return result


# ── Score Breakdown endpoint ──────────────────────────────────────────────────

class BreakdownRequest(BaseModel):
    simulation_id: str

@app.post("/score/breakdown")
def score_breakdown(req: BreakdownRequest):
    result = get_simulation_by_id(req.simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    # Reconstruct input from stored result
    input_data = result.get("decision_paths", [{}])
    # We need original input — store it in result during simulation
    orig_input = result.get("input_data", {})
    if not orig_input:
        raise HTTPException(status_code=400, detail="Input data not available for this simulation")
    return {"simulation_id": req.simulation_id, "breakdowns": get_score_breakdown(orig_input)}


# ── What-If endpoint ───────────────────────────────────────────────────────────

class WhatIfRequest(BaseModel):
    original_input: dict
    scenario: str  # one of the 6 scenario keys

WHATIF_SCENARIOS = {
    "increase_rainfall": {"severity_level": 15, "blocked_roads": 2},
    "remove_boats":      {},   # handled specially
    "reduce_hospital":   {"hospital_capacity_factor": 0.5},
    "shelter_full":      {},   # handled in route scoring
    "add_road_blockage": {"blocked_roads": 3},
    "delay_response":    {"response_time_limit": -2},
}

@app.post("/whatif")
def whatif_simulation(req: WhatIfRequest):
    original = dict(req.original_input)
    modified = dict(original)
    scenario = req.scenario

    if scenario == "increase_rainfall":
        modified["severity_level"] = min(100, original.get("severity_level", 50) + 15)
        modified["blocked_roads"]  = original.get("blocked_roads", 0) + 2
    elif scenario == "remove_boats":
        # Remove boats from resource context — handled via modified flag
        modified["_no_boats"] = True
    elif scenario == "reduce_hospital":
        modified["hospital_capacity"] = max(50, int(original.get("hospital_capacity", 500) * 0.5))
    elif scenario == "shelter_full":
        modified["_shelter_full"] = True
    elif scenario == "add_road_blockage":
        modified["blocked_roads"] = original.get("blocked_roads", 0) + 3
    elif scenario == "delay_response":
        modified["response_time_limit"] = max(1, original.get("response_time_limit", 6) - 2)
    else:
        raise HTTPException(status_code=400, detail="Unknown scenario")

    # Score paths for both original and modified
    orig_paths  = score_all_paths(original)
    mod_paths   = score_all_paths(modified)

    orig_best = max(orig_paths,  key=lambda p: p["final_decision_score"])
    mod_best  = max(mod_paths,   key=lambda p: p["final_decision_score"])

    # Score routes
    res = get_resources_dict()
    if modified.get("_no_boats"):
        res_mod = dict(res)
        if "Rescue Resource Officer" in res_mod:
            res_mod["Rescue Resource Officer"] = {**res_mod["Rescue Resource Officer"], "boats": 0, "life_jackets": 0}
    else:
        res_mod = res

    orig_routes = score_routes(original, res)
    mod_routes  = score_routes(modified, res_mod)
    orig_route  = next((r for r in orig_routes if r["selected"]), orig_routes[0])
    mod_route   = next((r for r in mod_routes  if r["selected"]), mod_routes[0])

    orig_risk = get_risk_level(compute_risk_score(original))
    mod_risk  = get_risk_level(compute_risk_score(modified))

    SCENARIO_LABELS = {
        "increase_rainfall":  "Rainfall Worsens (+15 severity, +2 blocked roads)",
        "remove_boats":       "Boats Removed (no water evacuation)",
        "reduce_hospital":    "Hospital Capacity Halved",
        "shelter_full":       "Nearest Shelter Marked Full",
        "add_road_blockage":  "3 More Roads Blocked",
        "delay_response":     "Response Delayed by 2 Hours",
    }

    return {
        "scenario": scenario,
        "scenario_label": SCENARIO_LABELS.get(scenario, scenario),
        "original": {
            "recommended_path": orig_best["path_id"],
            "path_name":        orig_best["name"],
            "recommended_route": orig_route["route_id"],
            "route_name":        orig_route["route_name"],
            "success_probability": orig_best["success_probability"],
            "risk_level":        orig_risk,
            "final_score":       orig_best["final_decision_score"],
            "safety_score":      orig_best["safety_score"],
        },
        "whatif": {
            "recommended_path": mod_best["path_id"],
            "path_name":        mod_best["name"],
            "recommended_route": mod_route["route_id"],
            "route_name":        mod_route["route_name"],
            "success_probability": mod_best["success_probability"],
            "risk_level":        mod_risk,
            "final_score":       mod_best["final_decision_score"],
            "safety_score":      mod_best["safety_score"],
        },
        "impact": {
            "score_change":   round(mod_best["final_decision_score"] - orig_best["final_decision_score"], 1),
            "success_change": round(mod_best["success_probability"]  - orig_best["success_probability"],  1),
            "path_changed":   orig_best["path_id"] != mod_best["path_id"],
            "route_changed":  orig_route["route_id"] != mod_route["route_id"],
            "risk_changed":   orig_risk != mod_risk,
        },
    }


# ── Human Approval endpoint ────────────────────────────────────────────────────

class ApprovalRequest(BaseModel):
    simulation_id: str
    action: str          # "approve" | "reject" | "re_simulate"
    officer_name: Optional[str] = "Crisis Admin"
    notes: Optional[str] = ""

@app.post("/approve")
def approve_plan(req: ApprovalRequest):
    result = get_simulation_by_id(req.simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if req.action not in ("approve", "reject", "re_simulate"):
        raise HTTPException(status_code=400, detail="Invalid action")

    best_path  = next((p for p in result["decision_paths"] if p["path_id"] == result["recommended_path"]), {})
    best_route = next((r for r in result.get("route_options", []) if r["route_id"] == result.get("recommended_route", "")), {})
    timestamp  = datetime.now(timezone.utc).isoformat()

    if req.action == "approve":
        # Generate department-wise action messages
        dtype  = result["disaster_type"]
        loc    = result["location"]
        route  = best_route.get("route_name", "recommended route")
        shelter = best_route.get("target_shelter", "nearest shelter")
        path_name = best_path.get("name", "recommended path")

        alerts = {
            "Rescue Team":    f"DEPLOY IMMEDIATELY to {loc}. Execute '{path_name}'. Prioritize vulnerable population. Use {route} for evacuation. Report to {shelter}.",
            "Medical Team":   f"SET UP temporary medical camp at {shelter}. Prepare for {result['decision_paths'][0].get('risk_score',0):.0f}% risk scenario. Ambulances to evacuation points.",
            "Transport Team": f"ACTIVATE {route}. Clear blocked roads. Deploy all available buses to evacuation corridors. Avoid flooded routes.",
            "Shelter Team":   f"OPEN {shelter} immediately. Prepare capacity for incoming evacuees. Ensure food, water, and medical supplies are ready.",
            "NGO Team":       f"DEPLOY volunteers to {loc}. Distribute food packets and water bottles at evacuation centers. Coordinate with Rescue Team.",
            "Fire/Safety Team": f"SECURE danger zones in {loc} before mass evacuation. Deploy safety teams to perimeter. Fire trucks on standby.",
        }
        result_to_return = {
            "status": "approved",
            "simulation_id": req.simulation_id,
            "approved_by": req.officer_name,
            "approved_at": timestamp,
            "notes": req.notes,
            "recommended_path": result["recommended_path"],
            "recommended_route": result.get("recommended_route", ""),
            "action_plan": f"Execute Path {result['recommended_path']} — {path_name} via {route} to {shelter}.",
            "department_alerts": alerts,
        }
        
        # Send email alert
        try:
            subject, body, html_body = build_email_content(result_to_return, req.officer_name)
            email_res = send_email_alert(subject, body, html_content=html_body)
            result_to_return["email_alert"] = email_res
        except Exception as e:
            print(f"Error sending email: {e}")
            result_to_return["email_alert"] = {"status": "error", "error": str(e)}
            
        return result_to_return
    elif req.action == "reject":
        return {"status": "rejected", "simulation_id": req.simulation_id, "rejected_by": req.officer_name, "rejected_at": timestamp, "notes": req.notes}
    else:
        return {"status": "re_simulate_requested", "simulation_id": req.simulation_id, "requested_by": req.officer_name, "requested_at": timestamp, "notes": req.notes}


# ── Resource Freshness endpoint ────────────────────────────────────────────────

@app.get("/resources/freshness")
def resource_freshness():
    resources = get_all_resources()
    now = datetime.now(timezone.utc)
    results = []
    for r in resources:
        try:
            updated = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
            age_min = (now - updated).total_seconds() / 60
            if age_min <= 15:
                status = "fresh"
            elif age_min <= 45:
                status = "warning"
            else:
                status = "outdated"
            results.append({"role": r["role"], "location": r["location"], "updated_at": r["updated_at"], "age_minutes": round(age_min, 1), "status": status})
        except Exception:
            results.append({"role": r["role"], "location": r["location"], "updated_at": r.get("updated_at", ""), "age_minutes": 999, "status": "outdated"})
    overall = "fresh"
    if any(r["status"] == "outdated" for r in results):
        overall = "outdated"
    elif any(r["status"] == "warning" for r in results):
        overall = "warning"
    return {"overall": overall, "details": results}


# ── Notification endpoints ─────────────────────────────────────────────────────

class NotificationPreviewRequest(BaseModel):
    simulation_id: str
    alert_target: Optional[str] = "both"  # "team", "public", or "both"
    region: Optional[str] = None

class NotificationSendRequest(BaseModel):
    simulation_id: str
    alert_target: Optional[str] = "both"  # "team", "public", or "both"
    region: Optional[str] = None
    approved_by: Optional[str] = "Crisis Admin"

@app.post("/notifications/preview")
def preview_notifications(req: NotificationPreviewRequest):
    result = get_simulation_by_id(req.simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Check if simulation is approved
    if not result.get("approved", False):
        raise HTTPException(status_code=400, detail="Simulation must be approved before sending notifications")

    preview = {}

    if req.alert_target in ["team", "both"]:
        team_message = build_team_alert(result)
        team_recipients = get_demo_recipients(req.region, "team")
        preview["team_alert"] = {
            "message": team_message,
            "recipient_count": len(team_recipients),
            "recipients": team_recipients
        }

    if req.alert_target in ["public", "both"]:
        public_message = build_public_alert(result)
        public_recipients = get_demo_recipients(req.region, "public")
        preview["public_alert"] = {
            "message": public_message,
            "recipient_count": len(public_recipients),
            "recipients": public_recipients
        }

    return {
        "simulation_id": req.simulation_id,
        "alert_target": req.alert_target,
        "region": req.region or "Zone A",
        "preview": preview
    }

@app.post("/notifications/send")
def send_notifications(req: NotificationSendRequest):
    result = get_simulation_by_id(req.simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Check if simulation is approved
    if not result.get("approved", False):
        raise HTTPException(status_code=400, detail="Simulation must be approved before sending notifications")

    # Send alerts
    alert_result = send_alerts(
        simulation=result,
        alert_target=req.alert_target,
        region=req.region,
        approved_by=req.approved_by
    )

    return {
        "simulation_id": req.simulation_id,
        "alert_target": req.alert_target,
        "region": req.region or "Zone A",
        "approved_by": req.approved_by,
        "result": alert_result
    }
