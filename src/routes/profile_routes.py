from flask import Blueprint, jsonify, render_template

from services import profile_service
from utils import logger

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
def profile_page():
    """Render the profile page"""
    return render_template("profile.html")


@profile_bp.route("/api/profile/stats")
def get_profile_stats():
    """Get profile statistics as JSON"""
    try:
        stats = profile_service.get_application_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching profile stats : {str(e)}")
        return jsonify({"error": str(e)}), 500
