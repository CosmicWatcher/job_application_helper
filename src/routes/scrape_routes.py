import threading

from flask import Blueprint, jsonify, render_template, request

from services import job_service, scrape_service
from utils import logger

# Create a blueprint for scraping routes
scrape_bp = Blueprint("scrape", __name__)

# Global variable to track scraping status
scraping_status = {
    "is_running": False,
    "scrape_complete": False,
    "analysis_complete": False,
    "error": None,
    "jobs_scraped": 0,
    "jobs_analyzed": 0,
    "total_jobs_to_scrape": 0,
    "total_jobs_to_analyze": 0,
    "stop_scraping": False,
    "stop_analysis": False,
}


@scrape_bp.route("/scrape")
def scrape_page():
    return render_template("scraper.html")


@scrape_bp.route("/api/start_scrape", methods=["POST"])
def start_scrape():
    global scraping_status

    data = request.json
    time_period = data.get("time_period")
    location = data.get("location")
    keywords = data.get("keywords")

    # If scraping is already running, return status
    if scraping_status["is_running"]:
        return jsonify(scraping_status)

    # Reset status
    scraping_status = {
        "is_running": True,
        "scrape_complete": False,
        "analysis_complete": False,
        "error": None,
        "jobs_scraped": 0,
        "jobs_analyzed": 0,
        "total_jobs_to_scrape": 0,
        "total_jobs_to_analyze": 0,
        "stop_scraping": False,
        "stop_analysis": False,
    }

    # Start scraping in a separate thread
    thread = threading.Thread(
        target=run_scraping_process, args=(time_period, location, keywords)
    )
    thread.daemon = True
    thread.start()

    return jsonify(scraping_status)


@scrape_bp.route("/api/stop_scrape", methods=["POST"])
def stop_scrape():
    global scraping_status

    # Only set the flag if scraping is running and not already complete
    if scraping_status["is_running"] and not scraping_status["scrape_complete"]:
        logger.info("User requested to stop scraping")
        scraping_status["stop_scraping"] = True

    return jsonify(scraping_status)


@scrape_bp.route("/api/stop_analysis", methods=["POST"])
def stop_analysis():
    global scraping_status

    # Only set the flag if analysis is running and not already complete
    if (
        scraping_status["is_running"]
        and scraping_status["scrape_complete"]
        and not scraping_status["analysis_complete"]
    ):
        logger.info("User requested to stop analysis")
        scraping_status["stop_analysis"] = True

    return jsonify(scraping_status)


@scrape_bp.route("/api/scrape_status")
def get_scrape_status():
    # No need to query the database, the counts are updated directly
    # by the scrape_jobs and analyze_jobs functions
    return jsonify(scraping_status)


def run_scraping_process(time_period, location, keywords):
    global scraping_status

    try:
        # Step 1: Save jobs to database
        # Pass the scraping_status to the scrape_jobs function
        scrape_service.scrape_jobs(
            "linkedin", time_period, location, keywords, scraping_status
        )
        scraping_status["scrape_complete"] = True

        # Step 2: Analyze jobs
        # Pass the scraping_status to the analyze_jobs function
        job_service.analyze_jobs(scraping_status)
        scraping_status["analysis_complete"] = True

        # All done
        scraping_status["is_running"] = False
    except Exception as e:
        logger.error(f"Error in scrape process : {str(e)}")
        scraping_status["error"] = str(e)
        scraping_status["is_running"] = False
