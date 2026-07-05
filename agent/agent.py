import os
import socket
import time

import psutil
import requests

# --- Configuration ---
# Change this to the IP address of your Central Server
SERVER_URL = "http://localhost:8000/report"
# How often to report (in seconds)
REPORT_INTERVAL = 10


def get_metrics():
    """Collects system metrics using psutil."""
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent,
    }


def run_agent():
    # Get the hostname so the server knows which machine this is
    hostname = socket.gethostname()
    print(f"[*] Starting Monitor Agent for: {hostname}")
    print(f"[*] Reporting to: {SERVER_URL}")
    print(f"[*] Interval: {REPORT_INTERVAL}s")

    while True:
        try:
            # 1. Collect metrics
            metrics = get_metrics()

            # 2. Prepare payload
            payload = {
                "hostname": hostname,
                "cpu_usage": metrics["cpu_usage"],
                "memory_usage": metrics["memory_usage"],
                "disk_usage": metrics["disk_usage"],
            }

            # 3. Send to server
            response = requests.post(SERVER_URL, json=payload, timeout=5)

            if response.status_code == 200:
                print(f"[+] Successfully reported: {metrics}")
            else:
                print(
                    f"[!] Server returned error: {response.status_code} - {response.text}"
                )

        except requests.exceptions.ConnectionError:
            print("[!] Error: Could not connect to the Central Server. Is it running?")
        except Exception as e:
            print(f"[!] Unexpected error: {e}")

        # 4. Wait for the next interval
        time.sleep(REPORT_INTERVAL)


if __name__ == "__main__":
    run_agent()
