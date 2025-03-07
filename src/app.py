import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template

# Parse command line arguments
if "--test" in sys.argv:
    os.environ["MODE"] = "TEST"
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running in test mode")
else:
    os.environ["MODE"] = "DEV"
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running in dev mode")

from routes.job_routes import job_bp
from routes.profile_routes import profile_bp
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
app.register_blueprint(profile_bp)


# Home route
@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting Flask server...")
    app.run(debug=True)
