"""Main entry point for running the FastAPI server."""
import uvicorn
import os
from config import settings

if __name__ == "__main__":
    # Disable reload in production or if RELOAD env var is not set
    # Reload can cause port conflicts when processes aren't killed properly
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    # Get port from environment or config (env takes precedence)
    # IMPORTANT: Port 8080 is for frontend, backend should use 8001
    env_port = os.getenv("API_PORT")
    if env_port:
        port = int(env_port)
        if port == 8080:
            print("⚠️  WARNING: API_PORT=8080 conflicts with frontend port!")
            print("   Auto-changing to 8001 (backend port)")
            port = 8001
    else:
        port = settings.api_port
    
    host = os.getenv("API_HOST", settings.api_host)
    
    print(f"🚀 Starting server on {host}:{port}")
    print(f"   Reload mode: {reload}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,  # Only reload if RELOAD=true is set
    )

