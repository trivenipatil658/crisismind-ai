from typing import TypedDict, List, Any, Dict


class GraphState(TypedDict):
    input_data: Dict[str, Any]
    resource_data: Dict[str, Any]
    scenario_summary: str
    generated_scenarios: List[str]
    agent_suggestions: List[Dict[str, Any]]
    decision_paths: List[Dict[str, Any]]
    scored_paths: List[Dict[str, Any]]
    route_options: List[Dict[str, Any]]
    recommended_path: str
    recommended_route: str
    route_explanation: str
    explanation: str
    llm_used: bool
    workflow_trace: List[str]
    errors: List[str]
