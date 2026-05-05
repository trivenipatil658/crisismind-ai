# -*- coding: utf-8 -*-
"""
LangGraph multi-agent workflow for CrisisMind AI.
19 nodes: 18 original + ollama_explanation_node.
Deterministic scoring + optional Ollama LLM explanation.
"""
from langgraph.graph import StateGraph, START, END
from graph_state import GraphState
from agents import (
    medical_agent, rescue_agent, transport_agent, shelter_agent,
    ngo_agent, fire_safety_agent, resource_agent, safety_agent, scenario_generator
)
from scoring import score_all_paths, get_risk_level, compute_risk_score
from route_planner import score_routes
from database import get_resources_dict
from llm_service import (
    llm_explain_decision, llm_enrich_agent_suggestion,
    llm_explain_route, is_ollama_available
)

OK = "[OK]"


def validate_input_node(state: GraphState) -> GraphState:
    d = state["input_data"]
    errors = []
    if d.get("severity_level", 0) < 0 or d.get("severity_level", 0) > 100:
        errors.append("severity_level must be 0-100")
    if d.get("affected_population", 0) <= 0:
        errors.append("affected_population must be positive")
    return {**state, "errors": errors, "llm_used": False, "workflow_trace": [f"validate_input {OK}"]}


def resource_context_node(state: GraphState) -> GraphState:
    res = get_resources_dict()
    return {
        **state,
        "resource_data": res,
        "workflow_trace": state["workflow_trace"] + [f"resource_context {OK}"],
    }


def scenario_generator_node(state: GraphState) -> GraphState:
    summary, scenarios = scenario_generator(state["input_data"])
    return {
        **state,
        "scenario_summary": summary,
        "generated_scenarios": scenarios,
        "workflow_trace": state["workflow_trace"] + [f"scenario_generator {OK}"],
    }


def medical_agent_node(state: GraphState) -> GraphState:
    result = medical_agent(state["input_data"], state["resource_data"])
    return {
        **state,
        "agent_suggestions": state.get("agent_suggestions", []) + [result],
        "workflow_trace": state["workflow_trace"] + [f"medical_agent {OK}"],
    }


def rescue_agent_node(state: GraphState) -> GraphState:
    result = rescue_agent(state["input_data"], state["resource_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"rescue_agent {OK}"],
    }


def transport_agent_node(state: GraphState) -> GraphState:
    result = transport_agent(state["input_data"], state["resource_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"transport_agent {OK}"],
    }


def shelter_agent_node(state: GraphState) -> GraphState:
    result = shelter_agent(state["resource_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"shelter_agent {OK}"],
    }


def ngo_agent_node(state: GraphState) -> GraphState:
    result = ngo_agent(state["resource_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"ngo_agent {OK}"],
    }


def fire_safety_agent_node(state: GraphState) -> GraphState:
    result = fire_safety_agent(state["input_data"], state["resource_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"fire_safety_agent {OK}"],
    }


def resource_agent_node(state: GraphState) -> GraphState:
    result = resource_agent(state["input_data"], state["resource_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"resource_agent {OK}"],
    }


def safety_agent_node(state: GraphState) -> GraphState:
    result = safety_agent(state["input_data"])
    return {
        **state,
        "agent_suggestions": state["agent_suggestions"] + [result],
        "workflow_trace": state["workflow_trace"] + [f"safety_agent {OK}"],
    }


def decision_path_node(state: GraphState) -> GraphState:
    return {
        **state,
        "workflow_trace": state["workflow_trace"] + [f"decision_path {OK}"],
    }


def scoring_node(state: GraphState) -> GraphState:
    paths = score_all_paths(state["input_data"])
    return {
        **state,
        "scored_paths": paths,
        "workflow_trace": state["workflow_trace"] + [f"scoring {OK}"],
    }


def route_planner_node(state: GraphState) -> GraphState:
    routes = score_routes(state["input_data"], state["resource_data"])
    best = next((r for r in routes if r["selected"]), routes[0])
    return {
        **state,
        "route_options": routes,
        "recommended_route": best["route_id"],
        "route_explanation": best["explanation"],
        "workflow_trace": state["workflow_trace"] + [f"route_planner {OK}"],
    }


def coordinator_node(state: GraphState) -> GraphState:
    best = max(state["scored_paths"], key=lambda p: p["final_decision_score"])
    return {
        **state,
        "recommended_path": best["path_id"],
        "workflow_trace": state["workflow_trace"] + [f"coordinator {OK}"],
    }


def ollama_explanation_node(state: GraphState) -> GraphState:
    """
    Uses Ollama LLM if available to:
    1. Enrich each agent suggestion
    2. Generate route explanation
    3. Generate final decision explanation
    Falls back to deterministic text if Ollama is offline.
    """
    d = state["input_data"]
    best_id = state["recommended_path"]
    best = next(p for p in state["scored_paths"] if p["path_id"] == best_id)
    risk_score = compute_risk_score(d)
    risk_level = get_risk_level(risk_score)

    best_route_id = state.get("recommended_route", "B")
    routes = state.get("route_options", [])
    best_route = next((r for r in routes if r["route_id"] == best_route_id), None)

    # Build warnings list
    warnings = []
    if d["blocked_roads"] >= 3:
        warnings.append(f"{d['blocked_roads']} roads blocked -- alternate routes activated.")
    if d["estimated_injured"] > d["hospital_capacity"]:
        warnings.append(f"Hospital overload: {d['estimated_injured']} injured vs {d['hospital_capacity']} capacity.")
    if d["available_rescue_teams"] < d["required_rescue_teams"]:
        warnings.append(f"Rescue team shortage: {d['available_rescue_teams']} available vs {d['required_rescue_teams']} required.")
    if risk_level in ("High", "Critical"):
        warnings.append(f"Overall risk level is {risk_level} -- immediate action required.")

    ollama_online = is_ollama_available()

    # 1. Enrich agent suggestions with LLM (only if Ollama available)
    enriched_suggestions = []
    for suggestion in state["agent_suggestions"]:
        if ollama_online:
            enriched_text, used = llm_enrich_agent_suggestion(
                suggestion["agent"],
                suggestion["suggestion"],
                {"disaster_type": d["disaster_type"], "severity_level": d["severity_level"]}
            )
            enriched_suggestions.append({
                **suggestion,
                "suggestion": enriched_text,
                "llm_enriched": used,
            })
        else:
            enriched_suggestions.append({**suggestion, "llm_enriched": False})

    # 2. Generate route explanation
    route_explanation = state.get("route_explanation", "")
    if best_route:
        route_exp, _ = llm_explain_route(
            route_name=best_route["route_name"],
            route_status=best_route["route_status"],
            distance=best_route["distance_km"],
            time_min=best_route["estimated_time_min"],
            shelter=best_route["target_shelter"],
            shelter_cap=best_route.get("shelter_capacity", 0),
            available_resources=best_route.get("available_resources", []),
            missing_resources=best_route.get("missing_resources", []),
            route_score=best_route["route_score"],
        )
        route_explanation = route_exp

    # 3. Generate final decision explanation
    explanation, llm_used = llm_explain_decision(
        disaster_type=d["disaster_type"],
        location=d["location"],
        recommended_path=best_id,
        path_name=best["name"],
        final_score=best["final_decision_score"],
        safety_score=best["safety_score"],
        resource_score=best["resource_score"],
        risk_level=risk_level,
        warnings=warnings,
        route_name=best_route["route_name"] if best_route else "N/A",
        route_status=best_route["route_status"] if best_route else "N/A",
        route_score=best_route["route_score"] if best_route else 0,
    )

    # Append human approval note
    explanation += "\n\n[HUMAN APPROVAL REQUIRED] Crisis Admin must review and approve before execution."

    llm_tag = "[LLM-Enhanced]" if llm_used else "[Rule-Based]"
    return {
        **state,
        "agent_suggestions": enriched_suggestions,
        "route_explanation": route_explanation,
        "explanation": explanation,
        "llm_used": llm_used,
        "workflow_trace": state["workflow_trace"] + [f"ollama_explanation {llm_tag} {OK}"],
    }


def persistence_node(state: GraphState) -> GraphState:
    return {**state, "workflow_trace": state["workflow_trace"] + [f"persistence {OK}"]}


def response_node(state: GraphState) -> GraphState:
    return {**state, "workflow_trace": state["workflow_trace"] + [f"response {OK}"]}


def build_workflow():
    graph = StateGraph(GraphState)

    nodes = [
        ("validate_input",      validate_input_node),
        ("resource_context",    resource_context_node),
        ("scenario_generator",  scenario_generator_node),
        ("medical_agent",       medical_agent_node),
        ("rescue_agent",        rescue_agent_node),
        ("transport_agent",     transport_agent_node),
        ("shelter_agent",       shelter_agent_node),
        ("ngo_agent",           ngo_agent_node),
        ("fire_safety_agent",   fire_safety_agent_node),
        ("resource_agent",      resource_agent_node),
        ("safety_agent",        safety_agent_node),
        ("decision_path",       decision_path_node),
        ("scoring",             scoring_node),
        ("route_planner",       route_planner_node),
        ("coordinator",         coordinator_node),
        ("ollama_explanation",  ollama_explanation_node),   # NEW
        ("persistence",         persistence_node),
        ("response",            response_node),
    ]

    for name, fn in nodes:
        graph.add_node(name, fn)

    sequence = [n[0] for n in nodes]
    graph.add_edge(START, sequence[0])
    for i in range(len(sequence) - 1):
        graph.add_edge(sequence[i], sequence[i + 1])
    graph.add_edge(sequence[-1], END)

    return graph.compile()


workflow = build_workflow()
