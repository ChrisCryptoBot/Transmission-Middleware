"""
Run Transmission Streamlit Dashboard

Quick start script for the Streamlit dashboard.
"""

import subprocess
import sys

if __name__ == "__main__":
    print("Starting Transmission™ Dashboard...")
    print("Dashboard will be available at: http://localhost:8501")
    print("Make sure the API is running at: http://localhost:8000")
    print("\nPress Ctrl+C to stop\n")
    
    # Get the project root (parent of startup folder)
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(project_root, "transmission", "dashboard", "main.py")
    
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        dashboard_path,
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])

