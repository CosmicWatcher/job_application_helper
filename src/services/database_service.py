import os
import sqlite3
from datetime import datetime, timedelta

from config import DB_PATH


class Database:
    def __init__(self):
        self.connection = sqlite3.connect(DB_PATH)
        self.connection.row_factory = sqlite3.Row  # enable row access by column name
        self.cursor = self.connection.cursor()

        # Create database directory and table if they don't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS 
                    jobs 
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            external_id TEXT UNIQUE,
                            title TEXT,
                            company TEXT,
                            description TEXT,
                            posted_time DATETIME,
                            rating INTEGER,
                            applied BOOLEAN NOT NULL DEFAULT 0,
                            suggestions TEXT
                        )
            """
        )
        self.connection.commit()

    def __del__(self):
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "connection") and self.connection:
            self.connection.close()

    def get_unrated_jobs(self):
        """Get all jobs that haven't been rated yet"""
        self.cursor.execute("SELECT * FROM jobs WHERE rating IS NULL")
        return self.cursor.fetchall()

    def get_job_list(self, days_ago=4):
        """Get recent jobs that are rated, not applied, and have suggestions"""
        self.cursor.execute(
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
            (datetime.now() - timedelta(days=days_ago),),
        )
        return self.cursor.fetchall()

    def update_job_rating(self, job_id, rating):
        """Update the rating for a job"""
        self.cursor.execute("UPDATE jobs SET rating = ? WHERE id = ?", (rating, job_id))
        self.connection.commit()

    def update_job_suggestions(self, job_id, suggestions):
        """Update the suggestions for a job"""
        self.cursor.execute(
            "UPDATE jobs SET suggestions = ? WHERE id = ?", (suggestions, job_id)
        )
        self.connection.commit()

    def mark_job_applied(self, job_id):
        """Mark a job as applied"""
        self.cursor.execute("UPDATE jobs SET applied = 1 WHERE id = ?", (job_id,))
        self.connection.commit()

    def insert_job(self, external_id, description, posted_time, title, company):
        """Insert a new job into the database"""
        self.cursor.execute(
            "INSERT INTO jobs (external_id, description, posted_time, title, company) VALUES (?, ?, ?, ?, ?)",
            (external_id, description, posted_time, title, company),
        )
        self.connection.commit()
