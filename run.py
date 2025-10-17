#!/usr/bin/env python3
"""
Production runner for PDF Merger Flask app
"""

from app import app
import os

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run in production mode
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )