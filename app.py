import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.dashboard_app import app

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
