"""
SprintWise - Application Entry Point
Run: python app.py  OR  flask run
"""
import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    print(f"""
╔══════════════════════════════════════════╗
║        SprintWise Backend API            ║
║  Running on http://localhost:{port}         ║
║  Swagger UI: /api/v1/docs (if enabled)   ║
╚══════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=port, debug=debug)
