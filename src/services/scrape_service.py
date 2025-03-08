import json
import os
import re
import time
from datetime import datetime, timedelta
from re import search

import requests
from bs4 import BeautifulSoup

from config import ROOT_PATH
from services.database_service import Database
from utils import print_error


def scrape_jobs(time_period, location, keywords, scraping_status=None):
    url_params = {}
    if time_period == "week":
        url_params["f_TPR"] = "r604800"
    else:
        url_params["f_TPR"] = "r86400"

    if location == "toronto":
        url_params["geoId"] = "100025096"
    elif location == "vancouver":
        url_params["geoId"] = "103366113"
        url_params["f_WT"] = "2"  # remote
    elif location == "canada":
        url_params["geoId"] = "101174742"
        url_params["f_WT"] = "2"  # remote

    url_params["keywords"] = requests.utils.quote(keywords)

    db = Database()

    search_url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    )

    query_params = "".join([f"&{key}={value}" for key, value in url_params.items()])
    list_url = f"{search_url}?{query_params[1:]}"  # Remove leading & from first param

    jobs = []
    for i in range(0, 100):
        # Check if scraping should be stopped
        if scraping_status and scraping_status.get("stop_scraping"):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{current_time} - Scraping stopped by user during job search")
            break

        res = requests.get(f"{list_url}&start={i * 10}")

        if res.status_code == 429:  # Too Many Requests
            retry_after = 1.05 * float(
                res.headers.get("Retry-After", 5)
            )  # Default to 5 seconds if header is missing
            print_error(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            res = requests.get(f"{list_url}&start={i * 10}")
        elif res.status_code != 200:
            print_error(f"Error: {res.status_code}")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        alljobs_on_this_page = soup.find_all("li")

        for x in range(0, len(alljobs_on_this_page)):
            try:
                jobid = (
                    alljobs_on_this_page[x]
                    .find("div", {"class": "base-card"})
                    .get("data-entity-urn")
                    .split(":")[3]
                )
                jobs.append(jobid)
                # Update the scraping status if provided
                if scraping_status is not None:
                    scraping_status["jobs_scraped"] = len(jobs)
            except Exception:
                pass

    total_jobs_to_scrape = len(jobs)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} - Found {len(jobs)} jobs")

    # Update total jobs to scrape in status
    if scraping_status is not None:
        scraping_status["total_jobs_to_scrape"] = total_jobs_to_scrape

    job_url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
    jobs_scraped_count = 0
    jobs_failed_count = 0
    for job_id in jobs:
        # Check if scraping should be stopped
        if scraping_status and scraping_status.get("stop_scraping"):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"{current_time} - Scraping stopped by user after {jobs_scraped_count} jobs"
            )
            break

        try:
            res = requests.get(job_url.format(job_id))

            if res.status_code == 429:  # Too Many Requests
                retry_after = 1.05 * float(
                    res.headers.get("Retry-After", 5)
                )  # Default to 5 seconds if header is missing
                print_error(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                res = requests.get(job_url.format(job_id))

            soup = BeautifulSoup(res.text, "html.parser")
            description_div = soup.find(
                "div",
                class_="show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden",
            )
            # Get the inner HTML content without the outer div
            description = (
                "".join(str(content) for content in description_div.contents)
                if description_div
                else ""
            )

            company = soup.find(
                "a",
                class_="topcard__org-name-link",
            ).get_text(strip=True)
            if is_blacklisted(company=company):
                raise Exception(f"Job:{job_id} blacklisted - Company: {company}")

            title = soup.find("h2", class_="top-card-layout__title").get_text(
                strip=True
            )
            if is_blacklisted(title=title):
                raise Exception(
                    f"Job:{job_id} blacklisted - Title: {title}, Company: {company}"
                )

            time_ago = soup.find("span", class_="posted-time-ago__text").get_text(
                strip=True
            )
            # Convert relative time to actual datetime
            current_time = datetime.now()

            # Extract number and unit from time_ago
            match = search(r"(\d+)\s+(\w+)", time_ago)
            posted_time = None
            if match:
                num = int(match.group(1))
                unit = match.group(2).lower().rstrip("s")  # Remove plural s

                if unit == "second":
                    posted_time = current_time - timedelta(seconds=num)
                elif unit == "minute":
                    posted_time = current_time - timedelta(minutes=num)
                elif unit == "hour":
                    posted_time = current_time - timedelta(hours=num)
                elif unit == "day" and num <= 3:
                    posted_time = current_time - timedelta(days=num)

            if posted_time:
                db.insert_job(job_id, description, posted_time, title, company)
                jobs_scraped_count += 1

                # Update the scraping status if provided
                if scraping_status is not None:
                    scraping_status["jobs_scraped"] = jobs_scraped_count

                # Log the current count
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"{current_time} - Scraped job {jobs_scraped_count}/{total_jobs_to_scrape}"
                )
        except Exception as e:
            jobs_failed_count += 1
            if scraping_status is not None:
                scraping_status["total_jobs_to_scrape"] = (
                    total_jobs_to_scrape - jobs_failed_count
                )
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print_error(f"{current_time} - Error inserting job {job_id}: {e}")

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if scraping_status and scraping_status.get("stop_scraping"):
        print(
            f"{current_time} - Scraping stopped by user. Scraped {jobs_scraped_count} jobs"
        )
    else:
        print(
            f"{current_time} - Completed scraping. Total jobs scraped: {jobs_scraped_count}"
        )

    return jobs_scraped_count


def is_blacklisted(company=None, title=None):
    with open(os.path.join(ROOT_PATH, "blacklists.json"), "r") as f:
        blacklists = json.load(f)

    if company:
        if company.lower() in [c.lower() for c in blacklists["companies"]]:
            return True
        else:
            return False

    if title:
        if any(
            re.search(r"\b" + fuzzy_title + r"\b", title, re.IGNORECASE) is not None
            for fuzzy_title in blacklists["titles"]
        ):
            return True
        else:
            return False
