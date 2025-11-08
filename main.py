"""Main entry point for running the FastAPI server."""
import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Set to False in production
    )

