from datetime import datetime

from flask import Blueprint, jsonify, render_template

from services import job_service

# Create a blueprint for job-related routes
job_bp = Blueprint("job", __name__)


@job_bp.route("/mark_applied/<int:job_id>", methods=["POST"])
def mark_job_applied(job_id):
    try:
        job_service.mark_applied(job_id)

        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Marked job {job_id} as applied"
        )
        return jsonify({"success": True})
    except Exception as e:
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error marking job {job_id} as applied: {str(e)}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


@job_bp.route("/jobs")
def show_jobs():
    try:
        jobs = job_service.get_job_list()
        return render_template("jobs.html", jobs=jobs)
    except Exception as e:
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error showing jobs: {str(e)}"
        )
        return f"Error: {str(e)}", 500
