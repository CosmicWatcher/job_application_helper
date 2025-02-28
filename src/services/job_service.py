import json
import os
import sqlite3
from datetime import datetime, timedelta

from google import genai

from config import DB_PATH, PROMPT_PATH
from services.llm_service import get_rating, get_suggestions


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
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # enable row access by column name
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM jobs WHERE rating IS NULL")
    jobs = cursor.fetchall()

    total_jobs_to_analyze = len(jobs)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} - Starting analysis of {total_jobs_to_analyze} jobs")

    # Update the total jobs to analyze in the status
    if scraping_status is not None:
        scraping_status["total_jobs_to_analyze"] = total_jobs_to_analyze

    jobs_analyzed_count = 0
    jobs_failed_count = 0

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
            cursor.execute("UPDATE jobs SET rating = ? WHERE id = ?", (rating, id))

            if rating >= 60 and job["suggestions"] is None:
                suggestions = get_suggestions(
                    ai_client, suggestions_instruct, description
                )
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time} - Got suggestions for job {id}")
                cursor.execute(
                    "UPDATE jobs SET suggestions = ? WHERE id = ?", (suggestions, id)
                )

            connection.commit()

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
            jobs_failed_count += 1
            # Update the total jobs to analyze if a job fails
            if scraping_status is not None and jobs_failed_count > 0:
                scraping_status["total_jobs_to_analyze"] = (
                    total_jobs_to_analyze - jobs_failed_count
                )

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"{current_time} - Error rating or getting suggestions for job {id}: {e}"
            )

    cursor.close()
    connection.close()

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
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Update job as applied
    cursor.execute("UPDATE jobs SET applied = 1 WHERE id = ?", (job_id,))
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def get_job_list():
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # enable row access by column name
    cursor = conn.cursor()

    # Get all jobs
    cursor.execute(
        """
            SELECT * FROM jobs 
                WHERE 
                    rating IS NOT NULL
                    AND posted_time > ?
                    AND applied = 0
                    AND suggestions IS NOT NULL
                    AND rating > 0
                ORDER BY rating DESC
        """,
        (datetime.now() - timedelta(days=4),),  # 4 days ago
    )
    jobs = cursor.fetchall()

    # Close connection
    cursor.close()
    conn.close()

    return jobs


def set_rating(job_id, rating):
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Update job rating
    cursor.execute("UPDATE jobs SET rating = ? WHERE id = ?", (rating, job_id))
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()
