#!/usr/bin/env python3
"""
Run the FastAPI server.

Usage:
    python run_server.py

How it works:
    uvicorn.run("api.main:app") means:
    - Import module 'api.main' (api/main.py)
    - Get the 'app' variable from that module
    - This is the FastAPI application instance
"""
import uvicorn

if __name__ == "__main__":
    # String format: "module.path:variable_name"
    # "api.main:app" = from api.main import app
    uvicorn.run(
        "api.main:app",  # Import path to FastAPI app
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
