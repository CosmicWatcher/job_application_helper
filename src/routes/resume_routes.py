import os
from datetime import datetime

from flask import Blueprint, jsonify, request, url_for

from config import RESUME_PATH
from services import resume_service
from utils import print_error

# Create a blueprint for resume-related routes
resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/get_resume_data")
def get_resume_data():
    """
    Return the resume job experience items as JSON for the modal dialog.
    """

    try:
        if not os.path.exists(RESUME_PATH):
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error: resume.tex file not found"
            )
            return jsonify(
                {
                    "success": False,
                    "error": "resume.tex file not found. Please make sure the file exists in the root resume directory.",
                }
            )

        jobs = resume_service.parse_resume_latex(RESUME_PATH)
        return jsonify({"success": True, "jobs": jobs})
    except Exception as e:
        print_error(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error getting resume data: {str(e)}"
        )
        return jsonify({"success": False, "error": str(e)})


@resume_bp.route("/generate_resume", methods=["POST"])
def generate_resume():
    """
    Generate a modified resume.tex file based on selected items and compile it to PDF.
    """
    try:
        if not os.path.exists(RESUME_PATH):
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error: resume.tex file not found"
            )
            return jsonify(
                {
                    "success": False,
                    "error": "resume.tex file not found. Please make sure the file exists in the root resume directory.",
                }
            )

        # Get selected items from form
        selected_items = request.form.getlist("selected_items[]")
        job_id = request.form.get("job_id")
        pdf_path = resume_service.generate_resume_pdf(
            RESUME_PATH, selected_items, job_id
        )

        # Create a URL for the PDF file
        pdf_url = url_for("static", filename="resume.pdf")

        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Generated PDF at: {pdf_path}, URL: {pdf_url}"
        )

        return jsonify({"success": True, "pdf_path": pdf_url})
    except Exception as e:
        print_error(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error generating resume: {str(e)}"
        )
        return jsonify({"success": False, "error": str(e)})
