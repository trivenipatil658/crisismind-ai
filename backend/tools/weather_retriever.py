"""
Weather Retriever Tool for CrisisMind AI.
Provides vectorless RAG weather context for disaster response simulation.
Demo fallback logic - no API keys or internet required.
"""
from datetime import datetime, timezone


def get_weather_context(location: str, latitude: float | None = None, longitude: float | None = None, disaster_type: str | None = None, existing_weather: str | None = None) -> dict:
    """
    Retrieve structured weather context based on disaster type and existing weather.
    Demo logic only - safe fallback without internet/API dependency.
    """
    disaster_type = (disaster_type or "").lower()
    existing_weather = (existing_weather or "").lower()

    # Default values
    condition = existing_weather if existing_weather else "Moderate weather conditions"
    rainfall_mm = 5
    wind_speed_kmph = 16
    humidity_percent = 60
    visibility_km = 8
    risk_level = "Low"
    risk_note = "No major weather escalation detected from available context."

    # Flood-specific logic
    if "flood" in disaster_type or "rain" in existing_weather or "heavy rainfall" in existing_weather:
        condition = "Heavy rainfall expected"
        rainfall_mm = 28
        wind_speed_kmph = 32
        humidity_percent = 82
        visibility_km = 4
        risk_level = "High"
        risk_note = "Heavy rainfall may increase flood risk and reduce road safety."

    # Fire-specific logic
    elif "fire" in disaster_type:
        condition = "Dry and windy conditions"
        rainfall_mm = 0
        wind_speed_kmph = 38
        humidity_percent = 35
        visibility_km = 6
        risk_level = "Medium"
        risk_note = "Wind can increase fire spread risk and reduce safety near danger zones."

    # Earthquake-specific logic
    elif "earthquake" in disaster_type:
        condition = "Clear weather with dust risk"
        rainfall_mm = 0
        wind_speed_kmph = 18
        humidity_percent = 48
        visibility_km = 7
        risk_level = "Medium"
        risk_note = "Weather is not the main risk, but dust and damaged roads may reduce visibility."

    # Return structured context
    return {
        "source": "demo_weather_retriever",
        "location": location,
        "condition": condition,
        "rainfall_mm": rainfall_mm,
        "wind_speed_kmph": wind_speed_kmph,
        "humidity_percent": humidity_percent,
        "visibility_km": visibility_km,
        "forecast_hours": 6,
        "risk_level": risk_level,
        "risk_note": risk_note,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "is_live": False
    }


def weather_score_adjustment(weather_context: dict) -> dict:
    """
    Calculate score adjustments based on weather conditions.
    Returns deltas to apply to risk, safety, feasibility, and confidence scores.
    """
    rainfall = weather_context.get("rainfall_mm", 0)
    wind = weather_context.get("wind_speed_kmph", 0)
    visibility = weather_context.get("visibility_km", 10)

    risk_delta = 0
    route_safety_delta = 0
    travel_feasibility_delta = 0
    confidence_delta = 0

    # Heavy rainfall adjustment
    if rainfall >= 25:
        risk_delta += 12
        route_safety_delta -= 15
        travel_feasibility_delta -= 10
        confidence_delta -= 3

    # High wind adjustment
    if wind >= 35:
        risk_delta += 8
        route_safety_delta -= 6
        travel_feasibility_delta -= 5
        confidence_delta -= 2

    # Low visibility adjustment
    if visibility <= 5:
        risk_delta += 6
        route_safety_delta -= 5
        travel_feasibility_delta -= 5
        confidence_delta -= 2

    explanation = f"Weather impact: rainfall {rainfall}mm, wind {wind}km/h, visibility {visibility}km. Adjustments applied to reflect weather risks."

    return {
        "risk_delta": risk_delta,
        "route_safety_delta": route_safety_delta,
        "travel_feasibility_delta": travel_feasibility_delta,
        "confidence_delta": confidence_delta,
        "explanation": explanation
    }