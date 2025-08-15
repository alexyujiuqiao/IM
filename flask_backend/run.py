from app import create_app
from dotenv import load_dotenv
import os
import sys

# Load .env file variables
load_dotenv()

# --------------------------------------------------
# Optional command-line switch to disable authentication. Invoking
# `python run.py --no-auth` (or setting DISABLE_AUTH env var) will start
# the backend without JWT protection so that the front-end can interact
# without obtaining a token first.
# --------------------------------------------------

if "--no-auth" in sys.argv:
    os.environ["DISABLE_AUTH"] = "true"

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Print all registered routes for debugging
    # macOS often reserves port 5000 for AirPlay (AirTunes). If it's busy, we
    # default to 5050 but allow override via the PORT env var.
    port = int(os.getenv("PORT", "5050"))
    app.run(debug=True, port=port) 
