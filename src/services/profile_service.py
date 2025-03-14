from collections import Counter, defaultdict
from datetime import datetime, timedelta

from services.database_service import Database


def get_application_stats():
    """Get statistics about job applications"""

    db = Database()
    applied_jobs = db.get_applied_jobs()

    # Calculate total applications
    total_applications = len(applied_jobs)

    # Applications by company
    company_counter = Counter()
    for job in applied_jobs:
        company_counter[job["company"]] += 1

    companies = [
        {"name": company, "count": count}
        for company, count in company_counter.most_common()
    ]

    # Applications by day
    daily_applications = defaultdict(int)
    for job in applied_jobs:
        if job["time_applied"]:
            app_date = datetime.fromisoformat(job["time_applied"]).date().isoformat()
            daily_applications[app_date] += 1

    # Fill in missing dates with zero counts
    today = datetime.now().date()
    # If we have applications, find the earliest date, otherwise use 14 days ago
    if daily_applications:
        earliest_date = min(
            datetime.fromisoformat(date).date() for date in daily_applications.keys()
        )
    else:
        earliest_date = today - timedelta(days=14)

    # Create a complete date range
    all_dates = {}
    current_date = earliest_date
    while current_date <= today:
        date_str = current_date.isoformat()
        all_dates[date_str] = daily_applications.get(date_str, 0)
        current_date += timedelta(days=1)

    # Convert to sorted list of dicts
    daily_apps_list = [
        {"date": date, "count": count}
        for date, count in sorted(all_dates.items(), reverse=True)
    ]

    # Recent applications (last 10)
    recent_applications = [dict(job) for job in applied_jobs[:10]]

    # Calculate application rate (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).date()
    recent_count = sum(
        1
        for job in applied_jobs
        if job["time_applied"]
        and datetime.fromisoformat(job["time_applied"]).date() > seven_days_ago
    )

    application_rate = round(recent_count / 7, 2)  # Average applications per day

    return {
        "total_applications": total_applications,
        "companies": companies,
        "daily_applications": daily_apps_list,
        "recent_applications": recent_applications,
        "application_rate": application_rate,
    }
