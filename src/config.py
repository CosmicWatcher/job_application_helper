import os


ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_PATH = os.path.join(ROOT_PATH, "resume/resume.tex")
DB_PATH = os.path.join(ROOT_PATH, "models/jobs.db")
PROMPT_PATH = os.path.join(ROOT_PATH, "prompts.json")
