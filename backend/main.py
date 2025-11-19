"""Entry point for the Chatbot Testbed Platform backend."""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app, settings
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Chatbot Safety Testbed Platform - Backend Server")
    print("=" * 60)
    print(f"Starting server at http://{settings.host}:{settings.port}")
    print(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Browser Mode: {'Headless' if settings.browser_headless else 'Headed'}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
