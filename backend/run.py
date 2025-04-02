"""
Entry point for the Hadith Similarity Search API
"""
import os
import argparse
import uvicorn
from app.core.config import settings

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run the Hadith Similarity Search API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    return parser.parse_args()

def main():
    """Main entry point for the API server"""
    args = parse_args()
    
    # Override debug setting from arguments if provided
    debug = args.debug or settings.DEBUG
    
    print(f"Starting server in {'debug' if debug else 'production'} mode")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if debug else "info",
    )

if __name__ == "__main__":
    main()
