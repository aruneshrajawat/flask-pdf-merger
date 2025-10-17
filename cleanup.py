#!/usr/bin/env python3
"""
Cleanup script to remove old uploaded and output files
Run this periodically to prevent disk space issues
"""

import os
import time
from datetime import datetime, timedelta

def cleanup_old_files(directory, max_age_hours=24):
    """Remove files older than max_age_hours"""
    if not os.path.exists(directory):
        return
    
    cutoff_time = time.time() - (max_age_hours * 3600)
    removed_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    removed_count += 1
                    print(f"Removed: {file_path}")
            except OSError as e:
                print(f"Error removing {file_path}: {e}")
        
        # Remove empty directories
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"Removed empty directory: {dir_path}")
            except OSError:
                pass
    
    return removed_count

if __name__ == "__main__":
    print(f"Starting cleanup at {datetime.now()}")
    
    # Clean uploads (24 hours)
    uploads_removed = cleanup_old_files('uploads', 24)
    print(f"Removed {uploads_removed} uploaded files")
    
    # Clean outputs (48 hours - give users more time to download)
    outputs_removed = cleanup_old_files('output', 48)
    print(f"Removed {outputs_removed} output files")
    
    print(f"Cleanup completed at {datetime.now()}")