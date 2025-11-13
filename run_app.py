# Placeholder for run_app.py
import subprocess
import sys
import time
import threading
import os
from app.core.config import settings

def run_backend():
    """Run FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", settings.api_host,
        "--port", str(settings.api_port),
        "--reload"
    ])

def run_frontend():
    """Run Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    time.sleep(3)  # Wait for backend to start
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app/frontend/smart_dashboard.py",
        "--server.port", str(settings.frontend_port),
        "--server.address", "localhost"
    ])

def main():
    """Launch both backend and frontend"""
    print("🏙️ Launching Sustainable Smart City Assistant...")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your API keys.")
        print("See .env.example for reference.")
        return
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Start frontend in main thread
        run_frontend()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down application...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()
