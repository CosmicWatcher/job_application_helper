import os

MODE = os.environ.get("MODE", "PROD")

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_PATH = os.path.join(ROOT_PATH, "resume/resume.tex")
DB_PATH = os.path.join(ROOT_PATH, f"models/jobs{'.test' if MODE == 'TEST' else ''}.db")
PROMPT_PATH = os.path.join(ROOT_PATH, "prompts.json")

JOB_RATING_THRESHOLD = 60
