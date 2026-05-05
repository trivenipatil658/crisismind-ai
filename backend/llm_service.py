"""
Ollama local LLM service for CrisisMind AI.
- Checks if Ollama is running
- Calls Ollama /api/generate endpoint
- Generates enriched explanations for agents, routes, decisions, and reports
- Falls back to deterministic text if Ollama is unavailable
- Never crashes the app if Ollama is offline
"""
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
USE_OLLAMA      = os.getenv("USE_OLLAMA", "true").lower() == "true"


def is_ollama_available() -> bool:
    """Check if Ollama server is reachable."""
    if not USE_OLLAMA:
        return False
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _call_ollama(prompt: str, max_tokens: int = 400) -> str:
    """
    Call Ollama /api/generate with stream=False.
    Returns generated text or raises exception.
    """
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.3}
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("response", "").strip()


def llm_explain_decision(
    disaster_type: str,
    location: str,
    recommended_path: str,
    path_name: str,
    final_score: float,
    safety_score: float,
    resource_score: float,
    risk_level: str,
    warnings: list,
    route_name: str,
    route_status: str,
    route_score: float,
) -> tuple[str, bool]:
    """
    Generate LLM explanation for the recommended decision path and route.
    Returns (explanation_text, llm_used: bool)
    """
    if not is_ollama_available():
        return _fallback_decision_explanation(
            recommended_path, path_name, final_score, safety_score,
            risk_level, warnings, route_name, route_status, route_score
        ), False

    warnings_text = "\n".join(warnings) if warnings else "No critical warnings."
    prompt = f"""You are a disaster management AI assistant. Based on the following simulation results, write a clear, concise explanation (5-7 sentences) for why this decision was recommended. Do not recalculate scores. Only explain the reasoning.

Disaster: {disaster_type} in {location}
Recommended Decision Path: Path {recommended_path} - {path_name}
Final Decision Score: {final_score}/100
Safety Score: {safety_score}/100
Resource Score: {resource_score}/100
Risk Level: {risk_level}
Warnings: {warnings_text}
Recommended Route: {route_name} (Status: {route_status}, Score: {route_score}/100)

Write the explanation in plain English for a crisis officer. Start with "Path {recommended_path} is recommended because..."
"""
    try:
        text = _call_ollama(prompt, max_tokens=350)
        return text, True
    except Exception:
        return _fallback_decision_explanation(
            recommended_path, path_name, final_score, safety_score,
            risk_level, warnings, route_name, route_status, route_score
        ), False


def llm_enrich_agent_suggestion(agent_name: str, base_suggestion: str, context: dict) -> tuple[str, bool]:
    """
    Enrich a single agent's suggestion with LLM reasoning.
    Returns (enriched_suggestion, llm_used: bool)
    """
    if not is_ollama_available():
        return base_suggestion, False

    prompt = f"""You are the {agent_name} in a disaster response system. Enrich the following suggestion with 1-2 additional actionable sentences. Keep it practical and concise. Do not repeat the original suggestion word for word.

Disaster Type: {context.get('disaster_type', 'Unknown')}
Severity: {context.get('severity_level', 0)}/100
Original Suggestion: {base_suggestion}

Write only the enriched suggestion (2-3 sentences total):"""

    try:
        text = _call_ollama(prompt, max_tokens=150)
        return text if text else base_suggestion, True
    except Exception:
        return base_suggestion, False


def llm_generate_report(result: dict) -> tuple[str, bool]:
    """
    Generate a full crisis response report from simulation result.
    Returns (report_text, llm_used: bool)
    """
    if not is_ollama_available():
        return _fallback_report(result), False

    best_path = next(
        (p for p in result.get("decision_paths", []) if p["path_id"] == result.get("recommended_path")), {}
    )
    best_route = next(
        (r for r in result.get("route_options", []) if r["route_id"] == result.get("recommended_route")), {}
    )

    prompt = f"""You are a senior disaster management coordinator. Write a professional crisis response report (8-10 sentences) based on the following simulation data. The report should cover: situation summary, recommended action, evacuation route, resource status, risk assessment, and human approval requirement.

--- SIMULATION DATA ---
Disaster: {result.get('disaster_type')} at {result.get('location')}
Severity: {result.get('decision_paths', [{}])[0].get('risk_score', 'N/A')}/100
Risk Level: {result.get('risk_level')}
Recommended Path: Path {result.get('recommended_path')} - {best_path.get('name', '')}
Final Score: {best_path.get('final_decision_score', 0)}/100
Success Probability: {best_path.get('success_probability', 0)}%
Recommended Route: {best_route.get('route_name', '')} ({best_route.get('route_status', '')})
Route Target: {best_route.get('target_shelter', '')}
Scenario: {result.get('scenario_summary', '')}
--- END DATA ---

Write the report with sections: SITUATION, RECOMMENDED ACTION, EVACUATION ROUTE, RISK ASSESSMENT, APPROVAL REQUIRED.
"""
    try:
        text = _call_ollama(prompt, max_tokens=600)
        return text if text else _fallback_report(result), True
    except Exception:
        return _fallback_report(result), False


def llm_explain_route(route_name: str, route_status: str, distance: float,
                      time_min: int, shelter: str, shelter_cap: int,
                      available_resources: list, missing_resources: list,
                      route_score: float) -> tuple[str, bool]:
    """
    Generate LLM explanation for why a specific route was selected.
    Returns (explanation, llm_used: bool)
    """
    if not is_ollama_available():
        return _fallback_route_explanation(
            route_name, route_status, distance, time_min,
            shelter, shelter_cap, route_score
        ), False

    res_text = ", ".join(available_resources) if available_resources else "standard vehicles"
    missing_text = ", ".join(missing_resources) if missing_resources else "none"

    prompt = f"""You are a disaster evacuation route planner. Explain in 3-4 sentences why this evacuation route was selected. Be practical and clear.

Route: {route_name}
Status: {route_status}
Distance: {distance} km
Estimated Time: {time_min} minutes
Target Shelter: {shelter} ({shelter_cap} spaces available)
Available Resources: {res_text}
Missing Resources: {missing_text}
Route Score: {route_score}/100

Write only the explanation starting with "This route was selected because..."
"""
    try:
        text = _call_ollama(prompt, max_tokens=200)
        return text if text else _fallback_route_explanation(
            route_name, route_status, distance, time_min, shelter, shelter_cap, route_score
        ), True
    except Exception:
        return _fallback_route_explanation(
            route_name, route_status, distance, time_min, shelter, shelter_cap, route_score
        ), False


# ── Fallback functions (deterministic) ────────────────────────────────────────

def _fallback_decision_explanation(path_id, path_name, final_score, safety_score,
                                    risk_level, warnings, route_name, route_status, route_score) -> str:
    lines = [
        f"Path {path_id} -- '{path_name}' is recommended with a Final Decision Score of {final_score}/100.",
        f"The Safety Score of {safety_score}/100 ensures maximum protection for the affected population.",
        f"Overall risk level is {risk_level}. The scoring model weighted safety at 35%, resources at 25%, speed at 20%, cost at 10%, and confidence at 10%.",
        f"Evacuation Route '{route_name}' (Status: {route_status}) was selected with a Route Score of {route_score}/100.",
    ]
    if warnings:
        lines.append("Risk warnings: " + " | ".join(warnings))
    lines.append("[HUMAN APPROVAL REQUIRED] Crisis Admin must review and approve before execution.")
    return "\n".join(lines)


def _fallback_route_explanation(route_name, route_status, distance, time_min,
                                 shelter, shelter_cap, route_score) -> str:
    return (
        f"This route was selected because '{route_name}' achieved the highest Route Score of {route_score}/100. "
        f"Status: {route_status}. Distance: {distance} km, estimated time: {time_min} minutes. "
        f"Target shelter '{shelter}' has {shelter_cap} available spaces. "
        f"Route selection prioritized safety (35%), feasibility (25%), resource compatibility (20%), distance (10%), and time (10%)."
    )


def _fallback_report(result: dict) -> str:
    best_path = next(
        (p for p in result.get("decision_paths", []) if p["path_id"] == result.get("recommended_path")), {}
    )
    best_route = next(
        (r for r in result.get("route_options", []) if r["route_id"] == result.get("recommended_route")), {}
    )
    return f"""CRISIS RESPONSE REPORT
======================
Simulation ID: {result.get('simulation_id', 'N/A')}
Generated: {result.get('created_at', 'N/A')}

SITUATION:
{result.get('scenario_summary', 'N/A')}

RECOMMENDED ACTION:
Path {result.get('recommended_path')} - {best_path.get('name', 'N/A')}
Final Decision Score: {best_path.get('final_decision_score', 0)}/100
Success Probability: {best_path.get('success_probability', 0)}%
Risk Level: {result.get('risk_level', 'N/A')}

EVACUATION ROUTE:
Route {result.get('recommended_route')} - {best_route.get('route_name', 'N/A')}
Status: {best_route.get('route_status', 'N/A')}
Distance: {best_route.get('distance_km', 0)} km | Time: {best_route.get('estimated_time_min', 0)} min
Target Shelter: {best_route.get('target_shelter', 'N/A')} ({best_route.get('shelter_capacity', 0)} spaces)
Route Score: {best_route.get('route_score', 0)}/100

RISK ASSESSMENT:
Safety Score: {best_path.get('safety_score', 0)}/100
Resource Score: {best_path.get('resource_score', 0)}/100
Failure Probability: {best_path.get('failure_probability', 0)}%

APPROVAL REQUIRED:
This report must be reviewed and approved by the Crisis Admin before execution.
All field teams must be briefed before deployment.

--- Generated by CrisisMind AI | Hack Fusion 2025 ---"""
