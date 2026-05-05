import uuid
from datetime import datetime
from langgraph_workflow import workflow
from scoring import get_risk_level, compute_risk_score
from database import init_db, save_simulation

init_db()


def run_simulation(input_data: dict) -> dict:
    sim_id = str(uuid.uuid4())[:8]
    created_at = datetime.utcnow().isoformat() + "Z"

    initial_state = {
        "input_data": input_data,
        "resource_data": {},
        "scenario_summary": "",
        "generated_scenarios": [],
        "agent_suggestions": [],
        "decision_paths": [],
        "scored_paths": [],
        "route_options": [],
        "recommended_path": "",
        "recommended_route": "",
        "route_explanation": "",
        "explanation": "",
        "llm_used": False,
        "workflow_trace": [],
        "errors": [],
    }

    final_state = workflow.invoke(initial_state)

    risk_score = compute_risk_score(input_data)
    risk_level = get_risk_level(risk_score)

    result = {
        "simulation_id": sim_id,
        "disaster_type": input_data["disaster_type"],
        "location": input_data["location"],
        "latitude": input_data.get("latitude", 15.3647),
        "longitude": input_data.get("longitude", 75.1240),
        "scenario_summary": final_state["scenario_summary"],
        "generated_scenarios": final_state["generated_scenarios"],
        "resource_summary": final_state["resource_data"],
        "agent_suggestions": final_state["agent_suggestions"],
        "decision_paths": final_state["scored_paths"],
        "recommended_path": final_state["recommended_path"],
        "route_options": final_state["route_options"],
        "recommended_route": final_state["recommended_route"],
        "route_explanation": final_state["route_explanation"],
        "explanation": final_state["explanation"],
        "llm_used": final_state.get("llm_used", False),
        "risk_level": risk_level,
        "workflow_trace": final_state["workflow_trace"],
        "created_at": created_at,
    }

    save_simulation(sim_id, result)
    return result
