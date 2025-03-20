import json
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Literal

import requests
from bs4 import BeautifulSoup

from config import ROOT_PATH
from services.database_service import Database
from utils import logger


class JobBoardScraper(ABC):
    """Abstract base class for job board scrapers"""

    def __init__(self, db=None):
        self.db = db or Database()

    @abstractmethod
    def build_search_url(self, time_period, location, keywords):
        """Build the search URL for the job board"""
        pass

    @abstractmethod
    def extract_job_ids(self, soup):
        """Extract job IDs from search results page"""
        pass

    @abstractmethod
    def get_job_details(self, job_id):
        """Get details for a specific job"""
        pass

    @abstractmethod
    def parse_posted_time(self, time_text):
        """Parse the posted time from job details"""
        pass

    def scrape_jobs(self, time_period, location, keywords, scraping_status=None):
        """Common scraping workflow"""
        list_url = self.build_search_url(time_period, location, keywords)

        jobs = []
        for i in range(0, 100):
            # Check if scraping should be stopped
            if scraping_status and scraping_status.get("stop_scraping"):
                logger.info("Scraping stopped by user during job search")
                break

            res = self._make_request(f"{list_url}&start={i * 10}")
            if not res:
                break

            soup = BeautifulSoup(res.text, "html.parser")
            page_job_ids = self.extract_job_ids(soup)

            if not page_job_ids:
                break  # No more jobs found

            jobs.extend(page_job_ids)

            # Update the scraping status if provided
            if scraping_status is not None:
                scraping_status["jobs_scraped"] = len(jobs)

        logger.info(f"Found {len(jobs)} jobs")

        # Update total jobs to scrape in status
        if scraping_status is not None:
            scraping_status["total_jobs_to_scrape"] = len(jobs)

        jobs_scraped_count = 0
        jobs_failed_count = 0
        for job_id in jobs:
            # Check if scraping should be stopped
            if scraping_status and scraping_status.get("stop_scraping"):
                logger.info(f"Scraping stopped by user after {jobs_scraped_count} jobs")
                break

            try:
                job_details = self.get_job_details(job_id)
                self.db.insert_job(
                    job_id,
                    job_details["description"],
                    job_details["posted_time"],
                    job_details["title"],
                    job_details["company"],
                )
                jobs_scraped_count += 1
                if scraping_status is not None:
                    scraping_status["jobs_scraped"] = jobs_scraped_count
                logger.info(f"Scraped job {jobs_scraped_count}/{len(jobs)}")
            except Exception as e:
                logger.error(f"Error saving job {job_id} : {e}")
                jobs_failed_count += 1
                if scraping_status is not None:
                    scraping_status["total_jobs_to_scrape"] = (
                        len(jobs) - jobs_failed_count
                    )

        logger.info(f"Completed scraping. Total jobs scraped : {jobs_scraped_count}")
        return jobs_scraped_count

    def _make_request(self, url):
        """Make HTTP request with rate limiting handling"""
        try:
            res = requests.get(url)
            if res.status_code == 429:  # Too Many Requests
                retry_after = 1.05 * float(res.headers.get("Retry-After", 5))
                logger.error(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                res = requests.get(url)

            if res.status_code != 200:
                logger.error(f"Error : {res.status_code}")
                return None

            return res
        except Exception as e:
            logger.error(f"Request error : {e}")
            return None


class LinkedInScraper(JobBoardScraper):
    def __init__(self):
        super().__init__()
        self.search_url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        )
        self.job_url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"

    def build_search_url(self, time_period, location, keywords):
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

        query_params = "".join([f"&{key}={value}" for key, value in url_params.items()])
        return (
            f"{self.search_url}?{query_params[1:]}"  # Remove leading & from first param
        )

    def extract_job_ids(self, soup):
        job_ids = []
        alljobs_on_this_page = soup.find_all("li")

        for job_element in alljobs_on_this_page:
            try:
                base_card = job_element.find("div", {"class": "base-card"})
                if base_card and base_card.get("data-entity-urn"):
                    jobid = base_card.get("data-entity-urn").split(":")[3]
                    job_ids.append(jobid)
            except Exception:
                pass

        return job_ids

    def get_job_details(self, job_id):
        res = self._make_request(self.job_url.format(job_id))
        if not res:
            raise Exception("Failed to get job details")

        soup = BeautifulSoup(res.text, "html.parser")

        # Extract job details
        description_div = soup.find(
            "div",
            class_="show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden",
        )
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
            raise Exception(f"blacklisted - Company: {company}")

        title = soup.find("h2", class_="top-card-layout__title").get_text(strip=True)
        if is_blacklisted(title=title):
            raise Exception(f"blacklisted - Title: {title}, Company: {company}")

        time_ago = soup.find("span", class_="posted-time-ago__text").get_text(
            strip=True
        )
        posted_time = self.parse_posted_time(time_ago)
        if posted_time is None:
            raise Exception("Failed to parse posted time")

        return {
            "description": description,
            "company": company,
            "title": title,
            "posted_time": posted_time,
        }

    def parse_posted_time(self, time_text):
        # Convert relative time to actual datetime
        current_time = datetime.now()

        # Extract number and unit from time_ago
        match = re.search(r"(\d+)\s+(\w+)", time_text)
        if match:
            num = int(match.group(1))
            unit = match.group(2).lower().rstrip("s")  # Remove plural s

            if unit == "second":
                return current_time - timedelta(seconds=num)
            elif unit == "minute":
                return current_time - timedelta(minutes=num)
            elif unit == "hour":
                return current_time - timedelta(hours=num)
            elif unit == "day" and num <= 3:
                return current_time - timedelta(days=num)

        return None


# Factory function to get the appropriate scraper
def get_scraper(job_board_name: Literal["linkedin", "wellfound"]):
    if job_board_name.lower() == "linkedin":
        return LinkedInScraper()
    # elif job_board_name.lower() == "wellfound":
    #     return WellfoundScraper()
    else:
        raise ValueError(f"Unsupportedzz job board: {job_board_name}")


# Main function that would be called by your application
def scrape_jobs(
    job_board: Literal["linkedin", "wellfound"],
    time_period,
    location,
    keywords,
    scraping_status=None,
):
    scraper = get_scraper(job_board)
    return scraper.scrape_jobs(time_period, location, keywords, scraping_status)


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
