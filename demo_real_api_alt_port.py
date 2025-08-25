#!/usr/bin/env python3
"""
FMCSA Demo API with REAL carrier data - Alternative Port Version
This version tries port 8000, and if busy, uses port 8001
"""

import uvicorn
import socket
import sys
from demo_real_api import app

def is_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except:
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("FMCSA API with REAL DATA")
    print("=" * 60)
    print("")
    
    # Try to find an available port
    port = 8000
    if not is_port_available(port):
        print(f"Port {port} is already in use!")
        port = 8001
        if not is_port_available(port):
            print(f"Port {port} is also in use!")
            port = 8002
            if not is_port_available(port):
                print("Ports 8000, 8001, and 8002 are all in use!")
                print("Please free up one of these ports or use kill_port_8000.ps1")
                sys.exit(1)
    
    print(f"Starting server on port {port}")
    print(f"API will be available at: http://localhost:{port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print("")
    print("Loading real carrier data...")
    print("-" * 60)
    
    # Update CORS in the app to include the alternative port
    from fastapi.middleware.cors import CORSMiddleware
    
    # Remove existing CORS middleware and add new one with current port
    app.middleware_stack = None
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000", 
            "http://localhost:3002", 
            "http://localhost:5173",
            f"http://localhost:{port}"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    uvicorn.run(app, host="0.0.0.0", port=port)