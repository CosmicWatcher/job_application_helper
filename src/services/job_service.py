import json
import os
from datetime import datetime

from google import genai

from config import PROMPT_PATH
from services.database_service import Database
from services.llm_service import get_rating, get_suggestions
from utils import print_error


def analyze_jobs(scraping_status=None):
    with open(PROMPT_PATH, "r") as f:
        prompt_data = json.loads(f.read())
        rating_instruct = (
            prompt_data["tasks"]["rating"] + " my resume is: " + prompt_data["resume"]
        )
        suggestions_instruct = (
            prompt_data["tasks"]["suggestions"]
            + " my resume is: "
            + prompt_data["resume"]
        )

    ai_client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"), http_options={"api_version": "v1alpha"}
    )

    db = Database()
    jobs = db.get_unrated_jobs()

    total_jobs_to_analyze = len(jobs)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} - Starting analysis of {total_jobs_to_analyze} jobs")

    # Update the total jobs to analyze in the status
    if scraping_status is not None:
        scraping_status["total_jobs_to_analyze"] = total_jobs_to_analyze

    jobs_analyzed_count = 0

    for job in jobs:
        # Check if analysis should be stopped
        if scraping_status and scraping_status.get("stop_analysis"):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"{current_time} - Analysis stopped by user after {jobs_analyzed_count} jobs"
            )
            break

        id = job["id"]
        description = job["description"]

        try:
            rating = get_rating(ai_client, rating_instruct, description)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{current_time} - Rating job {id}: {rating}")
            db.update_job_rating(id, rating)

            if rating >= 75 and job["suggestions"] is None:
                suggestions = get_suggestions(
                    ai_client, suggestions_instruct, description
                )
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time} - Got suggestions for job {id}")
                db.update_job_suggestions(id, suggestions)

            # Increment the analyzed count
            jobs_analyzed_count += 1

            # Update the scraping status if provided
            if scraping_status is not None:
                scraping_status["jobs_analyzed"] = jobs_analyzed_count

            # Log progress
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"{current_time} - Analyzed job {jobs_analyzed_count}/{total_jobs_to_analyze}"
            )

        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print_error(
                f"{current_time} - Error rating or getting suggestions for job {id}: {e}"
            )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if scraping_status and scraping_status.get("stop_analysis"):
        print(
            f"{current_time} - Analysis stopped by user. Analyzed {jobs_analyzed_count} jobs"
        )
    else:
        print(
            f"{current_time} - Completed analysis. Total jobs analyzed: {jobs_analyzed_count}"
        )

    return jobs_analyzed_count


def mark_applied(job_id):
    db = Database()
    db.mark_job_applied(job_id)


def get_job_list(days_ago=3):
    db = Database()
    return db.get_job_list(days_ago=days_ago)


def set_rating(job_id, rating):
    db = Database()
    db.update_job_rating(job_id, rating)
