"""
All deterministic expert agents for CrisisMind AI.
Each agent reads disaster input + live resource data and returns a structured suggestion.
"""


def medical_agent(d: dict, res: dict, weather_context: dict | None = None) -> dict:
    med = res.get("Medical Resource Officer", {})
    overload = d["estimated_injured"] - d["hospital_capacity"]
    beds = med.get("hospital_beds", d["hospital_capacity"])
    ambulances = med.get("ambulances", 0)
    camps = med.get("medical_camps", 0)

    if overload > 0:
        suggestion = (
            f"Hospital capacity exceeded by {overload} patients. "
            f"Available beds from resource update: {beds}. "
            f"Set up {max(1, camps)} temporary medical camp(s) immediately. "
            f"Deploy {ambulances} ambulances for critical patient transport."
        )
        pros = ["Reduces hospital overload", "Faster triage on-site", "Saves critical patients"]
        cons = ["Requires additional medical staff", "Temporary camps need supplies"]
    else:
        suggestion = (
            f"Hospital capacity is sufficient ({beds} beds available). "
            f"Pre-position {ambulances} ambulances at evacuation points and monitor for surge."
        )
        pros = ["Hospitals can absorb injured", "Stable medical response"]
        cons = ["Capacity may be strained if situation worsens"]

    # Weather integration
    if weather_context and weather_context.get("rainfall_mm", 0) >= 25:
        suggestion += f" Weather alert: Heavy rainfall ({weather_context['rainfall_mm']}mm) may delay ambulance response and increase infection risk in camps."
        cons.append("Heavy rainfall may complicate medical evacuation")

    return {"agent": "Medical Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def rescue_agent(d: dict, res: dict, weather_context: dict | None = None) -> dict:
    resc = res.get("Rescue Resource Officer", {})
    shortage = d["required_rescue_teams"] - d["available_rescue_teams"]
    vuln_pct = round((d["vulnerable_population"] / max(d["affected_population"], 1)) * 100, 1)
    boats = resc.get("boats", 0)
    life_jackets = resc.get("life_jackets", 0)
    divers = resc.get("divers", 0)

    if shortage > 0:
        boat_note = f" Boat-assisted evacuation possible with {boats} boats and {life_jackets} life jackets." if boats > 0 else " No boats available — road evacuation only."
        suggestion = (
            f"Rescue team shortage of {shortage} teams. "
            f"Prioritize vulnerable population ({vuln_pct}% of affected).{boat_note} "
            f"{divers} divers available for water rescue."
        )
        pros = ["Focuses limited resources on highest need", "Boat option available if roads flooded"]
        cons = ["General population evacuation delayed", "Requires clear zone prioritization"]
    else:
        suggestion = (
            f"Sufficient rescue teams. Deploy across all zones. "
            f"Boats: {boats}, Life jackets: {life_jackets}, Divers: {divers} available for water rescue."
        )
        pros = ["Full coverage possible", "Water rescue capability available"]
        cons = ["Coordination complexity increases with more teams"]

    # Weather integration
    if weather_context:
        rainfall = weather_context.get("rainfall_mm", 0)
        if rainfall >= 25 and boats > 0:
            suggestion += f" Weather alert: Heavy rainfall ({rainfall}mm) increases flood risk — prioritize boats and life jackets for vulnerable groups."
            pros.append("Weather conditions favor boat evacuation")
        elif weather_context.get("risk_level") == "High":
            suggestion += f" Weather risk level {weather_context['risk_level']} — {weather_context['risk_note']}"
            cons.append("Weather may complicate rescue operations")

    return {"agent": "Rescue Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def transport_agent(d: dict, res: dict, weather_context: dict | None = None) -> dict:
    trans = res.get("Transport Officer", {})
    blocked = d["blocked_roads"]
    safe_roads = trans.get("safe_roads", 0)
    buses = trans.get("available_buses", 0)
    bridges = trans.get("damaged_bridges", 0)

    if blocked >= 3:
        suggestion = (
            f"{blocked} roads blocked, {bridges} bridges damaged. "
            f"{safe_roads} safe roads available. "
            f"Activate alternate evacuation routes. Deploy {buses} available buses on safe corridors."
        )
        pros = ["Prevents evacuation bottlenecks", "Reduces accident risk"]
        cons = ["Alternate routes may be longer", "Requires real-time route monitoring"]
    else:
        suggestion = (
            f"{blocked} road(s) blocked — manageable. {safe_roads} safe roads available. "
            f"Deploy {buses} buses on primary routes with traffic management."
        )
        pros = ["Primary routes mostly usable", "Faster evacuation possible"]
        cons = ["Remaining blockages can cause delays if worsened"]

    # Weather integration
    if weather_context:
        rainfall = weather_context.get("rainfall_mm", 0)
        visibility = weather_context.get("visibility_km", 10)
        if rainfall >= 25:
            suggestion += f" Weather alert: Heavy rainfall ({rainfall}mm) may cause additional road flooding — avoid low-lying routes."
            cons.append("Rainfall may create new road blockages")
        if visibility <= 5:
            suggestion += f" Low visibility ({visibility}km) — reduce speed and increase convoy spacing."
            cons.append("Poor visibility increases accident risk")

    return {"agent": "Transport Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def shelter_agent(res: dict) -> dict:
    from database import get_all_shelters
    shelters = get_all_shelters()
    if not shelters:
        # Use demo shelters if none in DB
        shelters = [
            {"name": "AGM College Shelter", "available_capacity": 350, "food_available": True, "water_available": True},
            {"name": "Government School Shelter", "available_capacity": 600, "food_available": True, "water_available": True},
            {"name": "Community Hall Shelter", "available_capacity": 180, "food_available": False, "water_available": True},
        ]
    total_available = sum(s["available_capacity"] for s in shelters)
    best = max(shelters, key=lambda s: s["available_capacity"])
    suggestion = (
        f"{len(shelters)} shelters available with total capacity of {total_available} people. "
        f"Best option: {best['name']} with {best['available_capacity']} available spaces. "
        f"Food available: {best.get('food_available', False)}, Water: {best.get('water_available', False)}."
    )
    pros = ["Multiple shelter options available", "Distributed capacity reduces overload"]
    cons = ["Shelter capacity may reduce if more evacuees arrive", "Some shelters lack medical support"]
    return {"agent": "Shelter Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def ngo_agent(res: dict) -> dict:
    ngo = res.get("NGO / Volunteer Coordinator", {})
    volunteers = ngo.get("volunteers", 0)
    food = ngo.get("food_packets", 0)
    water = ngo.get("water_bottles", 0)
    blankets = ngo.get("blankets", 0)

    if volunteers > 50 and food > 500:
        suggestion = (
            f"NGO resources are strong: {volunteers} volunteers, {food} food packets, "
            f"{water} water bottles, {blankets} blankets. "
            "Deploy volunteers to evacuation centers and distribute relief supplies."
        )
        pros = ["Strong volunteer force", "Adequate relief supplies for initial phase"]
        cons = ["Coordination with official teams required", "Supplies may deplete in extended disaster"]
    else:
        suggestion = (
            f"NGO resources are limited: {volunteers} volunteers, {food} food packets. "
            "Request additional NGO support and coordinate with government relief teams."
        )
        pros = ["Some relief support available", "Volunteers can assist official teams"]
        cons = ["Insufficient for large-scale relief", "Additional procurement needed"]
    return {"agent": "NGO Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def fire_safety_agent(d: dict, res: dict, weather_context: dict | None = None) -> dict:
    fire = res.get("Fire and Safety Officer", {})
    firefighters = fire.get("firefighters", 0)
    fire_trucks = fire.get("fire_trucks", 0)
    safety_teams = fire.get("safety_teams", 0)
    danger_zones = fire.get("danger_zones", 0)
    severity = d["severity_level"]

    if severity >= 70 or danger_zones > 2:
        suggestion = (
            f"HIGH severity with {danger_zones} danger zones identified. "
            f"Deploy {safety_teams} safety teams to secure perimeter before mass evacuation. "
            f"{firefighters} firefighters and {fire_trucks} fire trucks on standby."
        )
        pros = ["Danger zones secured before evacuation", "Reduces secondary casualties"]
        cons = ["Delays mass evacuation slightly", "Requires coordination with rescue teams"]
    else:
        suggestion = (
            f"{danger_zones} danger zone(s) identified. {safety_teams} safety teams deployed. "
            f"{firefighters} firefighters on standby. Situation manageable."
        )
        pros = ["Safety perimeter manageable", "Fire risk under control"]
        cons = ["Situation can escalate if severity increases"]

    # Weather integration
    if weather_context and weather_context.get("risk_level") == "High":
        suggestion += f" Weather risk level {weather_context['risk_level']} — {weather_context['risk_note']}"
        cons.append("Weather conditions may worsen evacuation safety")

    return {"agent": "Fire & Safety Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def resource_agent(d: dict, res: dict) -> dict:
    budget_map = {"Low": 0, "Medium": 1, "High": 2}
    budget_score = budget_map.get(d["budget_level"], 1)
    shortage = max(0, d["required_rescue_teams"] - d["available_rescue_teams"])
    total_roles_updated = len(res)

    if budget_score == 0 or shortage > 3:
        suggestion = (
            f"Resource pressure is HIGH. {total_roles_updated} resource roles have submitted updates. "
            "Prioritize food, water, medicine, and shelter for high-risk zones. "
            "Activate emergency procurement and seek NGO/government support."
        )
        pros = ["Focused allocation maximizes impact", "Prevents waste"]
        cons = ["Some zones may receive delayed supplies", "Procurement takes time"]
    else:
        suggestion = (
            f"Resources are adequate. {total_roles_updated} resource roles updated. "
            "Pre-position supplies at evacuation centers. Maintain reserve for secondary phase."
        )
        pros = ["Sufficient supplies for initial response", "Reserve available for escalation"]
        cons = ["Situation may escalate requiring more resources"]
    return {"agent": "Resource Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def safety_agent(d: dict, weather_context: dict | None = None) -> dict:
    vuln = d["vulnerable_population"]
    severity = d["severity_level"]
    if severity >= 70 or vuln > 3000:
        suggestion = (
            f"HIGH severity ({severity}/100) with {vuln:,} vulnerable people. "
            "Immediately move elderly, children, injured, and mobility-impaired individuals. "
            "Establish safe zones away from disaster impact area."
        )
        pros = ["Protects highest-risk individuals first", "Reduces preventable casualties"]
        cons = ["Requires dedicated teams for vulnerable groups", "Slows general evacuation slightly"]
    else:
        suggestion = (
            f"Moderate severity ({severity}/100). Conduct orderly evacuation. "
            "Assign dedicated support for vulnerable population."
        )
        pros = ["Controlled evacuation reduces panic", "Manageable safety risk"]
        cons = ["Situation can escalate if severity increases"]

    # Weather integration
    if weather_context and weather_context.get("risk_level") in ["High", "Medium"]:
        suggestion += f" Weather risk level {weather_context['risk_level']} — {weather_context['risk_note']}"
        if weather_context.get("rainfall_mm", 0) >= 25:
            cons.append("Heavy rainfall may increase safety risks during evacuation")

    return {"agent": "Safety Agent", "suggestion": suggestion, "pros": pros, "cons": cons}


def scenario_generator(d: dict) -> tuple:
    dtype = d["disaster_type"]
    loc = d["location"]
    sev = d["severity_level"]
    summary = (
        f"A {dtype} event has been reported in {loc} with severity level {sev}/100. "
        f"Approximately {d['affected_population']:,} people are affected, including "
        f"{d['vulnerable_population']:,} vulnerable individuals. "
        f"{d['available_rescue_teams']} rescue teams available vs {d['required_rescue_teams']} required. "
        f"Hospital capacity: {d['hospital_capacity']} with {d['estimated_injured']} estimated injured. "
        f"{d['blocked_roads']} road(s) blocked. "
        f"Weather: {d['weather_condition']}. Response window: {d['response_time_limit']} hours. "
        f"Budget: {d['budget_level']}."
    )
    scenarios = [
        f"{dtype} intensity may worsen — severity could rise to {min(100, sev + 15)}/100 within 2 hours.",
        f"Road blockages may increase from {d['blocked_roads']} to {d['blocked_roads'] + 2} if weather deteriorates.",
        f"Hospital load may reach {d['estimated_injured'] + 200} if secondary injuries occur.",
        f"Rescue delay risk increases if teams not deployed within {max(1, d['response_time_limit'] - 2)} hours.",
        "Shelter capacity may reduce if more evacuees arrive than estimated.",
        "Rescue resource shortage may occur if disaster spreads to adjacent zones.",
    ]
    return summary, scenarios
