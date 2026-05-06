"""
SMS Notification Service for CrisisMind AI.
Supports demo mode and real SMS providers (Twilio, Fast2SMS, MSG91).
Human-approved SMS alerts for disaster response coordination.
"""
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


# SMS Mode Configuration
SMS_MODE = os.getenv("SMS_MODE", "demo").lower()
ALLOWED_MODES = ["demo", "twilio", "fast2sms", "msg91"]

if SMS_MODE not in ALLOWED_MODES:
    SMS_MODE = "demo"

# Provider Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")
FAST2SMS_SENDER_ID = os.getenv("FAST2SMS_SENDER_ID", "CRISIM")

MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY")
MSG91_SENDER_ID = os.getenv("MSG91_SENDER_ID")
MSG91_TEMPLATE_ID = os.getenv("MSG91_TEMPLATE_ID")


# Demo Recipients Data
DEMO_TEAM_RECIPIENTS = [
    {
        "name": "NGO Coordinator",
        "phone": "+910000000001",
        "role": "NGO",
        "region": "Zone A",
        "recipient_type": "team"
    },
    {
        "name": "Rescue Team Lead",
        "phone": "+910000000002",
        "role": "Rescue",
        "region": "Zone A",
        "recipient_type": "team"
    },
    {
        "name": "Medical Officer",
        "phone": "+910000000003",
        "role": "Medical",
        "region": "Zone A",
        "recipient_type": "team"
    },
    {
        "name": "Fire Safety Officer",
        "phone": "+910000000004",
        "role": "Fire",
        "region": "Zone A",
        "recipient_type": "team"
    }
]

DEMO_PUBLIC_RECIPIENTS = [
    {
        "name": "Zone A Resident 1",
        "phone": "+910000000101",
        "role": "Resident",
        "region": "Zone A",
        "recipient_type": "public"
    },
    {
        "name": "Zone A Resident 2",
        "phone": "+910000000102",
        "role": "Resident",
        "region": "Zone A",
        "recipient_type": "public"
    },
    {
        "name": "Zone A Resident 3",
        "phone": "+910000000103",
        "role": "Resident",
        "region": "Zone A",
        "recipient_type": "public"
    }
]


def build_team_alert(simulation: Dict[str, Any], approved_by: Optional[str] = None) -> str:
    """
    Build action-focused team alert message.
    """
    disaster_type = simulation.get("disaster_type", "Emergency").upper()
    location = simulation.get("location", "Affected Area")
    recommended_route = simulation.get("recommended_route", "B")
    recommended_path = simulation.get("recommended_path", "B")

    # Find route details
    route_details = ""
    route_options = simulation.get("route_options", [])
    for route in route_options:
        if route.get("route_id") == recommended_route:
            route_name = route.get("route_name", f"Route {recommended_route}")
            shelter = route.get("target_shelter", "Designated Shelter")
            route_details = f"{route_name} to {shelter}"
            break

    if not route_details:
        route_details = f"Route {recommended_route} to Designated Shelter"

    risk_level = simulation.get("risk_level", "High")
    weather_note = ""
    weather_context = simulation.get("weather_context")
    if weather_context and weather_context.get("risk_level") == "High":
        weather_note = f" Weather: {weather_context.get('condition', '')}"

    approved_text = f" Approved by {approved_by}." if approved_by else ""

    message = f"""CRISISMIND TEAM ALERT:
{disaster_type} emergency in {location}.
Approved route: {route_details}.
Priority: vulnerable citizens first.
Risk level: {risk_level}.{weather_note}{approved_text}"""

    return message.strip()


def build_public_alert(simulation: Dict[str, Any], approved_by: Optional[str] = None) -> str:
    """
    Build calm, simple public alert message.
    """
    disaster_type = simulation.get("disaster_type", "emergency").lower()
    location = simulation.get("location", "affected area")

    # Find route details
    route_details = ""
    recommended_route = simulation.get("recommended_route", "B")
    route_options = simulation.get("route_options", [])
    for route in route_options:
        if route.get("route_id") == recommended_route:
            route_name = route.get("route_name", f"Route {recommended_route}")
            shelter = route.get("target_shelter", "designated shelter")
            route_details = f"Use {route_name} to {shelter}."
            break

    if not route_details:
        route_details = f"Use Route {recommended_route} to designated shelter."

    weather_note = ""
    weather_context = simulation.get("weather_context")
    if weather_context and weather_context.get("risk_level") == "High":
        weather_note = f" {weather_context.get('risk_note', '')}"

    message = f"""CRISISMIND PUBLIC ALERT:
{disaster_type.title()} risk in {location}.
{route_details}
Avoid unsafe roads.{weather_note}
Follow rescue team instructions.
Do not panic."""

    return message.strip()


def get_demo_recipients(region: Optional[str] = None, recipient_type: str = "both") -> List[Dict[str, Any]]:
    """
    Get demo recipients filtered by region and type.
    """
    all_recipients = []

    if recipient_type in ["team", "both"]:
        team_recipients = DEMO_TEAM_RECIPIENTS
        if region:
            team_recipients = [r for r in team_recipients if r.get("region") == region]
        all_recipients.extend(team_recipients)

    if recipient_type in ["public", "both"]:
        public_recipients = DEMO_PUBLIC_RECIPIENTS
        if region:
            public_recipients = [r for r in public_recipients if r.get("region") == region]
        all_recipients.extend(public_recipients)

    return all_recipients


def send_sms(recipients: List[Dict[str, Any]], message: str, alert_type: str) -> Dict[str, Any]:
    """
    Send SMS using configured provider or demo mode.
    """
    sent_at = datetime.now(timezone.utc).isoformat()

    if SMS_MODE == "demo":
        return {
            "mode": "demo",
            "status": "simulated",
            "alert_type": alert_type,
            "sent_count": len(recipients),
            "failed_count": 0,
            "recipients": recipients,
            "message": message,
            "provider_response": "Demo SMS simulated successfully",
            "sent_at": sent_at
        }

    # Real SMS providers - placeholder implementations
    if SMS_MODE == "twilio":
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
            return {
                "mode": "demo",
                "status": "fallback",
                "alert_type": alert_type,
                "sent_count": len(recipients),
                "failed_count": 0,
                "recipients": recipients,
                "message": message,
                "provider_response": "Twilio credentials missing - using demo fallback",
                "sent_at": sent_at
            }

        try:
            # Placeholder for Twilio integration
            # import twilio if available
            return {
                "mode": "twilio",
                "status": "ready",
                "alert_type": alert_type,
                "sent_count": 0,
                "failed_count": len(recipients),
                "recipients": recipients,
                "message": message,
                "provider_response": "Twilio integration placeholder - not implemented",
                "sent_at": sent_at
            }
        except Exception as e:
            return {
                "mode": "demo",
                "status": "error",
                "alert_type": alert_type,
                "sent_count": 0,
                "failed_count": len(recipients),
                "recipients": recipients,
                "message": message,
                "provider_response": f"Twilio error: {str(e)}",
                "sent_at": sent_at
            }

    elif SMS_MODE == "fast2sms":
        if not FAST2SMS_API_KEY:
            return {
                "mode": "demo",
                "status": "fallback",
                "alert_type": alert_type,
                "sent_count": len(recipients),
                "failed_count": 0,
                "recipients": recipients,
                "message": message,
                "provider_response": "Fast2SMS API key missing - using demo fallback",
                "sent_at": sent_at
            }

        try:
            # Placeholder for Fast2SMS integration
            return {
                "mode": "fast2sms",
                "status": "ready",
                "alert_type": alert_type,
                "sent_count": 0,
                "failed_count": len(recipients),
                "recipients": recipients,
                "message": message,
                "provider_response": "Fast2SMS integration placeholder - not implemented",
                "sent_at": sent_at
            }
        except Exception as e:
            return {
                "mode": "demo",
                "status": "error",
                "alert_type": alert_type,
                "sent_count": 0,
                "failed_count": len(recipients),
                "recipients": recipients,
                "message": message,
                "provider_response": f"Fast2SMS error: {str(e)}",
                "sent_at": sent_at
            }

    elif SMS_MODE == "msg91":
        if not MSG91_AUTH_KEY:
            return {
                "mode": "demo",
                "status": "fallback",
                "alert_type": alert_type,
                "sent_count": len(recipients),
                "failed_count": 0,
                "recipients": recipients,
                "message": message,
                "provider_response": "MSG91 auth key missing - using demo fallback",
                "sent_at": sent_at
            }

        try:
            # Placeholder for MSG91 integration
            return {
                "mode": "msg91",
                "status": "ready",
                "alert_type": alert_type,
                "sent_count": 0,
                "failed_count": len(recipients),
                "recipients": recipients,
                "message": message,
                "provider_response": "MSG91 integration placeholder - not implemented",
                "sent_at": sent_at
            }
        except Exception as e:
            return {
                "mode": "demo",
                "status": "error",
                "alert_type": alert_type,
                "sent_count": 0,
                "failed_count": len(recipients),
                "recipients": recipients,
                "message": message,
                "provider_response": f"MSG91 error: {str(e)}",
                "sent_at": sent_at
            }

    # Fallback to demo
    return {
        "mode": "demo",
        "status": "fallback",
        "alert_type": alert_type,
        "sent_count": len(recipients),
        "failed_count": 0,
        "recipients": recipients,
        "message": message,
        "provider_response": f"Unknown SMS mode '{SMS_MODE}' - using demo fallback",
        "sent_at": sent_at
    }


def send_alerts(
    simulation: Dict[str, Any],
    alert_target: str = "both",
    region: Optional[str] = None,
    approved_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main handler for sending emergency alerts.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    simulation_id = simulation.get("simulation_id", "unknown")

    result = {
        "status": "success",
        "mode": SMS_MODE,
        "simulation_id": simulation_id,
        "region": region or "Zone A",
        "approved_by": approved_by,
        "created_at": created_at
    }

    # Build messages
    if alert_target in ["team", "both"]:
        team_message = build_team_alert(simulation, approved_by)
        team_recipients = get_demo_recipients(region, "team")
        team_result = send_sms(team_recipients, team_message, "team")
        result["team_alert"] = team_result

    if alert_target in ["public", "both"]:
        public_message = build_public_alert(simulation, approved_by)
        public_recipients = get_demo_recipients(region, "public")
        public_result = send_sms(public_recipients, public_message, "public")
        result["public_alert"] = public_result

    return result