from flask import Blueprint, jsonify, render_template, request

from services import job_service
from utils import logger

# Create a blueprint for job-related routes
job_bp = Blueprint("job", __name__)


@job_bp.route("/mark_applied/<int:job_id>", methods=["POST"])
def mark_job_applied(job_id):
    try:
        job_service.mark_applied(job_id)

        logger.info(f"Marked job {job_id} as applied")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error marking job {job_id} as applied: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@job_bp.route("/reject_job/<int:job_id>", methods=["POST"])
def reject_job(job_id):
    try:
        job_service.set_rating(job_id, 0)

        logger.info(f"Marked job {job_id} as rejected")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error rejecting job {job_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@job_bp.route("/jobs")
def show_jobs():
    days_ago = request.args.get("days_ago", default=4, type=int)
    logger.info(f"Showing jobs from {days_ago} days ago")
    try:
        jobs = job_service.get_job_list(days_ago=days_ago)
        return render_template("jobs.html", jobs=jobs)
    except Exception as e:
        logger.error(f"Error showing jobs: {str(e)}")
        return f"Error: {str(e)}", 500
