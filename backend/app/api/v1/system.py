"""SpaceLoop System Status and Telemetry API."""
from flask import Blueprint, jsonify, request
from backend.space_ai import get_system_connectivity_status, set_simulate_ai_failure, is_simulate_ai_failure

system_bp = Blueprint("system_api", __name__)


@system_bp.route("/status", methods=["GET"])
def system_status():
    """Return live system telemetry, external service connectivity, and operational health."""
    status_data = get_system_connectivity_status()
    return jsonify({
        "success": True,
        "status": "operational",
        "service": "SpaceLoop Physical Workspace Protocol",
        "version": "2.4.0",
        "connectivity": status_data,
        **status_data,
    }), 200


@system_bp.route("/connectivity", methods=["GET"])
def connectivity_status():
    """Return external integration connectivity health."""
    status_data = get_system_connectivity_status()
    return jsonify({
        "success": True,
        "status": "operational",
        "connectivity": status_data,
        **status_data,
    }), 200


@system_bp.route("/dev/toggle-ai-simulation", methods=["POST", "GET"])
def toggle_ai_simulation():
    """Toggle simulated AI failure to demonstrate deterministic fallback to judges."""
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        enable = payload.get("enabled", not is_simulate_ai_failure())
        set_simulate_ai_failure(enable)
    sim_val = is_simulate_ai_failure()
    return jsonify({
        "success": True,
        "simulate_ai_failure": sim_val,
        "ai_simulation_enabled": sim_val,
        "message": f"AI failure simulation is now {'ENABLED (Fallback active)' if sim_val else 'DISABLED (Live AI active)'}",
    }), 200
