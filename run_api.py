"""
Run Transmission API Server

Quick start script for the FastAPI backend.
"""

from transmission.api.main import run_server

if __name__ == "__main__":
    print("Starting Transmission™ API Server...")
    print("API will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("WebSocket at: ws://localhost:8000/ws")
    print("\nPress Ctrl+C to stop\n")
    
    run_server(host="0.0.0.0", port=8000, reload=True)

