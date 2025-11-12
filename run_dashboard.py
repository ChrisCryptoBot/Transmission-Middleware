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
    
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "transmission/dashboard/main.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])

