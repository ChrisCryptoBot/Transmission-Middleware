"""
Run Transmission Streamlit Dashboard

Quick start script for the Streamlit dashboard.
"""

from pathlib import Path
import os
import subprocess
import sys

# Ensure we're running from project root
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

# Get absolute path to dashboard
app_path = ROOT / "transmission" / "dashboard" / "main.py"

if __name__ == "__main__":
    print("Starting Transmission™ Dashboard...")
    print(f"Working directory: {ROOT}")
    print(f"Dashboard path: {app_path}")
    print("Dashboard will be available at: http://localhost:8501")
    print("Make sure the API is running at: http://localhost:8000")
    print("\nPress Ctrl+C to stop\n")
    
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])

