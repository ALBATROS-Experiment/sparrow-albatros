#!/usr/bin/env python3
import os
import time
import datetime
from pathlib import Path
from lbtools_l import lb_set, lb_read, set_clock_lb

# Create logs directory if it doesn't exist
log_dir = Path.home() / "logs"
log_dir.mkdir(exist_ok=True)

# Log file path
log_file = log_dir / "set_gps_clock.log"

def log_message(message):
    """Write message to log file with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} - {message}\n")

def main():
    """Set system clock from GPS and log result"""
    log_message("Starting GPS clock synchronization attempt")
    
    # Current year for sanity check
    current_year = datetime.datetime.now().year
    
    try:
        # Try to set the system clock from the GPS
        success = set_clock_lb(current_year)
        
        if success:
            log_message("SUCCESS: System clock successfully set from GPS")
            print("System clock successfully synchronized with GPS time")
        else:
            log_message("FAILED: Could not set system clock from GPS")
            print("Failed to set system clock from GPS")
    
    except Exception as e:
        error_msg = f"ERROR: Exception occurred: {str(e)}"
        log_message(error_msg)
        print(error_msg)

if __name__ == "__main__":
    main()