#!/usr/bin/env python3
"""
System Health and Availability Monitoring Tool (Version 1)
Designed for the Nourish & Share project to monitor:
https://beacon-food-network.web.app

This script checks the status of the target website by sending an HTTP GET request,
measures the response time, handles network/connection errors, and generates
a simple report file.
"""

import datetime
import time
import requests

# Target site configuration
TARGET_URL = "https://beacon-food-network.web.app"
REQUEST_TIMEOUT = 10  # Seconds to wait before timing out the request
REPORT_FILE = "health_report.txt"

def run_health_check():
    """
    Performs a single HTTP GET request to the target URL, captures metrics and errors,
    displays results to the terminal, and writes a health report.
    """
    # 1. Capture current date and time
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Initialize variables for metrics and status
    status = "OFFLINE"
    status_code = None
    response_time_ms = None
    error_detail = None

    # 2. Perform the HTTP GET check with timing
    start_time = time.perf_counter()
    try:
        # Send HTTP GET request with a reasonable timeout
        response = requests.get(TARGET_URL, timeout=REQUEST_TIMEOUT)
        
        # Measure response time in milliseconds
        response_time_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        # Check if the status code indicates success (2xx or 3xx)
        if 200 <= response.status_code < 400:
            status = "ONLINE"
        else:
            status = "OFFLINE"
            error_detail = f"Unsuccessful HTTP response status code: {response.status_code}"

    except requests.exceptions.ConnectionError:
        status = "OFFLINE"
        error_detail = "Connection Error: Failed to resolve DNS or establish a connection."
    except requests.exceptions.Timeout:
        status = "OFFLINE"
        error_detail = f"Timeout Error: Request exceeded the {REQUEST_TIMEOUT}-second limit."
    except requests.exceptions.RequestException as e:
        status = "OFFLINE"
        error_detail = f"Network/HTTP Error: {str(e)}"
    except Exception as e:
        status = "OFFLINE"
        error_detail = f"Unexpected Error: {str(e)}"

    # 3. Format response time (if available)
    response_time_display = f"{response_time_ms:.2f} ms" if response_time_ms is not None else "N/A"
    status_code_display = str(status_code) if status_code is not None else "N/A"

    # 4. Display a clear result in the terminal
    print("=" * 60)
    print("              IT SYSTEM HEALTH MONITOR - RESULT")
    print("=" * 60)
    print(f"Date:          {date_str}")
    print(f"Time:          {time_str}")
    print(f"URL:           {TARGET_URL}")
    print(f"Status:        {status}")
    print(f"Status Code:   {status_code_display}")
    print(f"Response Time: {response_time_display}")
    if error_detail:
        print(f"Error Detail:  {error_detail}")
    print("=" * 60)

    # 5. Generate a simple text health report
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as report:
            report.write("=" * 60 + "\n")
            report.write("                   IT SYSTEM HEALTH REPORT\n")
            report.write("=" * 60 + "\n")
            report.write(f"Generated On:  {date_str} at {time_str}\n")
            report.write(f"Target URL:    {TARGET_URL}\n")
            report.write(f"Site Status:   {status}\n")
            report.write(f"Status Code:   {status_code_display}\n")
            report.write(f"Response Time: {response_time_display}\n")
            if error_detail:
                report.write(f"Error Detail:  {error_detail}\n")
            report.write("=" * 60 + "\n")
        print(f"\n[INFO] Health report successfully generated: {REPORT_FILE}")
    except IOError as e:
        print(f"\n[ERROR] Could not write report file: {e}")

if __name__ == "__main__":
    run_health_check()
