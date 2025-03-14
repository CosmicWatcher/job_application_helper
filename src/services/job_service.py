import json
import os

from google import genai

from config import JOB_RATING_THRESHOLD, PROMPT_PATH
from services.database_service import Database
from services.llm_service import get_rating, get_suggestions
from utils import logger


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
    logger.info(f"Starting analysis of {total_jobs_to_analyze} jobs")

    # Update the total jobs to analyze in the status
    if scraping_status is not None:
        scraping_status["total_jobs_to_analyze"] = total_jobs_to_analyze

    jobs_analyzed_count = 0

    for job in jobs:
        # Check if analysis should be stopped
        if scraping_status and scraping_status.get("stop_analysis"):
            logger.info(f"Analysis stopped by user after {jobs_analyzed_count} jobs")
            break

        id = job["id"]
        description = job["description"]

        try:
            rating = get_rating(ai_client, rating_instruct, description)
            logger.info(f"Rating job {id} : {rating}")
            db.update_job_rating(id, rating)

            if rating >= JOB_RATING_THRESHOLD and job["suggestions"] is None:
                suggestions = get_suggestions(
                    ai_client, suggestions_instruct, description
                )
                logger.info(f"Got suggestions for job {id}")
                db.update_job_suggestions(id, suggestions)

            # Increment the analyzed count
            jobs_analyzed_count += 1

            # Update the scraping status if provided
            if scraping_status is not None:
                scraping_status["jobs_analyzed"] = jobs_analyzed_count

            # Log progress
            logger.info(f"Analyzed job {jobs_analyzed_count}/{total_jobs_to_analyze}")

        except Exception as e:
            logger.error(f"Error rating or getting suggestions for job {id} : {e}")

    if scraping_status and scraping_status.get("stop_analysis"):
        logger.info(f"Analysis stopped by user. Analyzed {jobs_analyzed_count} jobs")
    else:
        logger.info(f"Completed analysis. Total jobs analyzed : {jobs_analyzed_count}")

    return jobs_analyzed_count


def mark_applied(job_id):
    db = Database()
    db.mark_job_applied(job_id)


def get_job_list(days_ago=3):
    db = Database()
    return db.get_job_list(days_ago=days_ago)


def reject_job(job_id):
    db = Database()
    db.reject_job(job_id)
