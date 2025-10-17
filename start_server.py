#!/usr/bin/env python3
"""
Start the Flask development server
"""

from app import app
import os

if __name__ == '__main__':
    print("🚀 Starting PDF Merger Server...")
    print("📁 Upload folder:", app.config['UPLOAD_FOLDER'])
    print("📁 Output folder:", app.config['OUTPUT_FOLDER'])
    print("🌐 Server will be available at: http://localhost:5000")
    print("📋 Features available:")
    print("   - Upload multiple PDF files")
    print("   - Merge PDFs in custom order")
    print("   - Download merged PDF")
    print("   - View merge history")
    print("   - API endpoints for programmatic access")
    print("\n" + "="*50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )