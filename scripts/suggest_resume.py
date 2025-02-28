import json
import os
import sqlite3
import time

from dotenv import load_dotenv
from google import genai

from config import DB_PATH, PROMPT_PATH
from services.llm_service import get_suggestions

if __name__ == "__main__":
    load_dotenv()
    with open(PROMPT_PATH, "r") as f:
        prompt_data = json.loads(f.read())
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

    cursor.execute("SELECT * FROM jobs WHERE suggestions IS NULL ORDER BY rating DESC")
    jobs = cursor.fetchmany(10)

    for job in jobs:
        id = job["id"]
        description = job["description"]

        try:
            suggestions = get_suggestions(ai_client, suggestions_instruct, description)
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Got suggestions for job {id}")
            cursor.execute(
                "UPDATE jobs SET suggestions = ? WHERE id = ?", (suggestions, id)
            )
            connection.commit()
        except Exception as e:
            print(f"Error getting suggestions for job {id}: {e}")

    cursor.close()
    connection.close()
