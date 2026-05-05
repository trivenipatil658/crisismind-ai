def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def clamp_score(value):
    return max(0, min(100, round(value, 2)))


def get_risk_level(risk_score: float) -> str:
    if risk_score <= 30:
        return "Low"
    elif risk_score <= 60:
        return "Medium"
    elif risk_score <= 80:
        return "High"
    return "Critical"


def compute_risk_score(d: dict) -> float:
    severity = d["severity_level"]
    pop_exposure = min(100, d["affected_population"] / 500)
    vulnerability = min(100, (d["vulnerable_population"] / max(d["affected_population"], 1)) * 100)
    team_shortage = max(0, d["required_rescue_teams"] - d["available_rescue_teams"])
    resource_shortage = min(100, (team_shortage / max(d["required_rescue_teams"], 1)) * 100)
    delay_risk = min(100, (d["blocked_roads"] / 10) * 100)
    return clamp(
        0.30 * severity + 0.20 * pop_exposure + 0.20 * vulnerability
        + 0.15 * resource_shortage + 0.15 * delay_risk
    )


def compute_confidence_score(d: dict) -> float:
    data_completeness = 90.0
    known_types = ["flood", "earthquake", "fire", "cyclone", "landslide", "tsunami"]
    historical_similarity = 80.0 if d["disaster_type"].lower() in known_types else 60.0
    agent_agreement = 85.0
    model_certainty = 80.0
    return clamp(
        0.30 * data_completeness + 0.30 * historical_similarity
        + 0.20 * agent_agreement + 0.20 * model_certainty
    )


def score_path_a(d: dict, base_risk: float, confidence: float) -> dict:
    team_ratio = min(1.0, d["available_rescue_teams"] / max(d["required_rescue_teams"], 1))
    road_penalty = d["blocked_roads"] * 5
    hospital_overload = max(0, d["estimated_injured"] - d["hospital_capacity"])
    overload_penalty = min(40, (hospital_overload / max(d["hospital_capacity"], 1)) * 40)

    safety = clamp(55 + team_ratio * 20 - overload_penalty * 0.5)
    speed = clamp(85 - road_penalty)
    resource = clamp(50 - (1 - team_ratio) * 20)
    cost = clamp(40 - (d["budget_level"] == "Low") * 15)
    risk = clamp(base_risk + 5)
    conf = clamp(confidence - 5)
    success = clamp(0.30 * safety + 0.25 * resource + 0.20 * speed + 0.15 * conf + 0.10 * (100 - risk))
    final = clamp(0.35 * safety + 0.25 * resource + 0.20 * speed + 0.10 * cost + 0.10 * conf)

    return {
        "path_id": "A", "name": "Fast Mass Evacuation",
        "description": "Evacuate maximum people quickly using all available routes and teams.",
        "safety_score": round(safety, 1), "speed_score": round(speed, 1),
        "resource_score": round(resource, 1), "cost_score": round(cost, 1),
        "confidence_score": round(conf, 1), "risk_score": round(risk, 1),
        "success_probability": round(success, 1), "failure_probability": round(100 - success, 1),
        "final_decision_score": round(final, 1),
        "pros": ["Fast response", "Reduces immediate exposure", "Covers large population"],
        "cons": ["Can overload roads and hospitals", "Higher resource pressure", "Less focus on vulnerable groups"],
    }


def score_path_b(d: dict, base_risk: float, confidence: float) -> dict:
    team_ratio = min(1.0, d["available_rescue_teams"] / max(d["required_rescue_teams"], 1))
    hospital_overload = max(0, d["estimated_injured"] - d["hospital_capacity"])
    medical_bonus = min(20, (hospital_overload / max(d["hospital_capacity"], 1)) * 20)

    safety = clamp(70 + team_ratio * 15 + medical_bonus * 0.5)
    speed = clamp(70 - d["blocked_roads"] * 3)
    resource = clamp(65 - (1 - team_ratio) * 15)
    cost = clamp(50 - (d["budget_level"] == "Low") * 10)
    risk = clamp(base_risk - 10)
    conf = clamp(confidence + 5)
    success = clamp(0.30 * safety + 0.25 * resource + 0.20 * speed + 0.15 * conf + 0.10 * (100 - risk))
    final = clamp(0.35 * safety + 0.25 * resource + 0.20 * speed + 0.10 * cost + 0.10 * conf)

    return {
        "path_id": "B", "name": "Prioritized Evacuation + Medical Camp",
        "description": "Evacuate vulnerable people first, set up medical camp, use safe routes, move to shelters.",
        "safety_score": round(safety, 1), "speed_score": round(speed, 1),
        "resource_score": round(resource, 1), "cost_score": round(cost, 1),
        "confidence_score": round(conf, 1), "risk_score": round(risk, 1),
        "success_probability": round(success, 1), "failure_probability": round(100 - success, 1),
        "final_decision_score": round(final, 1),
        "pros": ["Best safety balance", "Reduces hospital overload", "Protects vulnerable people first"],
        "cons": ["Requires coordination", "Medium to high resource usage", "Slightly slower than Path A"],
    }


def score_path_c(d: dict, base_risk: float, confidence: float) -> dict:
    severity_penalty = d["severity_level"] * 0.3
    delay_penalty = (10 - d["response_time_limit"]) * 2 if d["response_time_limit"] < 10 else 0

    safety = clamp(45 - severity_penalty * 0.3 - delay_penalty)
    speed = clamp(40 - d["blocked_roads"] * 4)
    resource = clamp(75)
    cost = clamp(80 - (d["budget_level"] == "High") * 10)
    risk = clamp(base_risk + 15)
    conf = clamp(confidence - 15)
    success = clamp(0.30 * safety + 0.25 * resource + 0.20 * speed + 0.15 * conf + 0.10 * (100 - risk))
    final = clamp(0.35 * safety + 0.25 * resource + 0.20 * speed + 0.10 * cost + 0.10 * conf)

    return {
        "path_id": "C", "name": "Resource-Conservative Delayed Response",
        "description": "Use fewer teams initially, wait for conditions to stabilize, respond in phases.",
        "safety_score": round(safety, 1), "speed_score": round(speed, 1),
        "resource_score": round(resource, 1), "cost_score": round(cost, 1),
        "confidence_score": round(conf, 1), "risk_score": round(risk, 1),
        "success_probability": round(success, 1), "failure_probability": round(100 - success, 1),
        "final_decision_score": round(final, 1),
        "pros": ["Lower cost", "Less immediate resource pressure", "Preserves resources for later phases"],
        "cons": ["Higher casualty risk", "Delayed rescue", "Dangerous in severe disasters"],
    }


def score_all_paths(d: dict, weather_context: dict | None = None) -> list:
    base_risk = compute_risk_score(d)
    confidence = compute_confidence_score(d)
    paths = [score_path_a(d, base_risk, confidence), score_path_b(d, base_risk, confidence), score_path_c(d, base_risk, confidence)]

    # Apply weather adjustments if available
    if weather_context:
        from tools.weather_retriever import weather_score_adjustment
        weather_adj = weather_score_adjustment(weather_context)
        for path in paths:
            path["risk_score"] = clamp_score(path["risk_score"] + weather_adj["risk_delta"])
            path["safety_score"] = clamp_score(path["safety_score"] + weather_adj["route_safety_delta"])
            path["speed_score"] = clamp_score(path["speed_score"] + weather_adj["travel_feasibility_delta"])
            path["confidence_score"] = clamp_score(path["confidence_score"] + weather_adj["confidence_delta"])
            # Recalculate final score
            path["final_decision_score"] = clamp_score(
                0.35 * path["safety_score"] + 0.25 * path["resource_score"] +
                0.20 * path["speed_score"] + 0.10 * path["cost_score"] + 0.10 * path["confidence_score"]
            )
            # Recalculate success probability
            path["success_probability"] = clamp_score(
                0.30 * path["safety_score"] + 0.25 * path["resource_score"] +
                0.20 * path["speed_score"] + 0.15 * path["confidence_score"] + 0.10 * (100 - path["risk_score"])
            )
            path["failure_probability"] = clamp_score(100 - path["success_probability"])

    sorted_paths = sorted(paths, key=lambda p: p["final_decision_score"], reverse=True)
    for i, p in enumerate(sorted_paths):
        p["rank"] = i + 1
    path_map = {p["path_id"]: p for p in sorted_paths}
    return [path_map["A"], path_map["B"], path_map["C"]]


def get_score_breakdown(d: dict) -> list:
    """Return positive factors, negative factors, warnings for each path."""
    base_risk = compute_risk_score(d)
    confidence = compute_confidence_score(d)
    paths = score_all_paths(d)
    breakdowns = []
    for p in paths:
        positives, negatives, warnings = [], [], []
        if p["safety_score"] >= 75:
            positives.append(f"High Safety Score ({p['safety_score']}) — strong life protection")
        elif p["safety_score"] < 55:
            negatives.append(f"Low Safety Score ({p['safety_score']}) — higher casualty risk")
        if p["resource_score"] >= 65:
            positives.append(f"Good Resource Score ({p['resource_score']}) — adequate supplies")
        elif p["resource_score"] < 50:
            negatives.append(f"Low Resource Score ({p['resource_score']}) — resource pressure")
        if p["speed_score"] >= 65:
            positives.append(f"Good Speed Score ({p['speed_score']}) — timely response")
        elif p["speed_score"] < 45:
            negatives.append(f"Low Speed Score ({p['speed_score']}) — slow response risk")
        if p["confidence_score"] >= 80:
            positives.append(f"High Confidence ({p['confidence_score']}) — reliable prediction")
        if p["risk_score"] >= 65:
            warnings.append(f"High Risk Score ({p['risk_score']}) — dangerous conditions")
        if p["failure_probability"] >= 40:
            warnings.append(f"Failure Probability {p['failure_probability']}% — significant risk")
        if d["blocked_roads"] >= 3:
            warnings.append(f"{d['blocked_roads']} roads blocked — evacuation may be delayed")
        if d["estimated_injured"] > d["hospital_capacity"]:
            negatives.append(f"Hospital overload: {d['estimated_injured']} injured vs {d['hospital_capacity']} capacity")
        if d["available_rescue_teams"] < d["required_rescue_teams"]:
            negatives.append(f"Team shortage: {d['available_rescue_teams']} of {d['required_rescue_teams']} required")
        breakdowns.append({
            "path_id": p["path_id"],
            "name": p["name"],
            "final_score": p["final_decision_score"],
            "positives": positives,
            "negatives": negatives,
            "warnings": warnings,
        })
    return breakdowns
