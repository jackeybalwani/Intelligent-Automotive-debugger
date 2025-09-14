#!/usr/bin/env python3
"""
Startup script for the automotive debugger backend
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Ensure database directory exists
    db_dir = Path("database")
    db_dir.mkdir(exist_ok=True)

    # Ensure uploads directory exists
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    print("Starting Automotive Debugger Backend...")
    print("Backend will be available at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")

    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )