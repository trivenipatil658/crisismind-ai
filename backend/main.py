from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from schemas import DisasterInput, ResourceUpdate, ShelterUpdate
from simulator import run_simulation
from database import (
    init_db, get_all_simulations, get_simulation_by_id,
    save_resource_update, get_all_resources, save_shelter, get_all_shelters
)
from llm_service import is_ollama_available, llm_generate_report, OLLAMA_MODEL

app = FastAPI(title="CrisisMind AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
