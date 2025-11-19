"""Entry point for the Chatbot Testbed Platform backend."""

import sys
import os
import asyncio

# Fix for Windows: Set event loop policy BEFORE any asyncio usage
# This is critical for Playwright to work on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

    # On Windows, use direct app object to ensure event loop policy is preserved
    # On other platforms, use string-based import for better reload support
    if sys.platform == 'win32':
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_level="info"
        )
    else:
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level="info"
        )
