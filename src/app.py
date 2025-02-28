import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template

from config import DB_PATH
from routes.job_routes import job_bp
from routes.resume_routes import resume_bp
from routes.scrape_routes import scrape_bp

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(job_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(scrape_bp)


# Home route
@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting Flask server...")
    app.run(debug=True)
