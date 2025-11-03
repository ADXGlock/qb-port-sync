import os
import json
import requests
import time

# ---------------------------
# Configuration via ENV vars
# ---------------------------

# Gluetun API endpoint (even with WireGuard, port forwarding is under "openvpn")

GLUETUN_API = os.getenv("GLUETUN_API", "http://localhost:8000/v1/openvpn/portforwarded")
GLUETUN_USER = os.getenv("GLUETUN_USER", "admin") # Username for Gluetun API auth
GLUETUN_PASS = os.getenv("GLUETUN_PASS", "password")  # Password for Gluetun API auth

# qBittorrent WebUI API endpoints

QBITTORRENT_HOST = os.getenv("QBITTORRENT_HOST", "http://localhost:9092")
QBITTORRENT_API = f"{QBITTORRENT_HOST}/api/v2/app/setPreferences"
QBITTORRENT_LOGIN = f"{QBITTORRENT_HOST}/api/v2/auth/login"
QBITTORRENT_USER = os.getenv("QBITTORRENT_USER", "admin") # WebUI username
QBITTORRENT_PASS = os.getenv("QBITTORRENT_PASS", "adminadmin") # WebUI password

# ---------------------------
# Get port forwarded by Gluetun (ProtonVPN)
# ---------------------------
def get_forwarded_port():
    try:
        response = requests.get(
            GLUETUN_API,
            auth=(GLUETUN_USER, GLUETUN_PASS),
            timeout=10
        )
        response.raise_for_status()
        print("[INFO] Gluetun API response:", response.text, flush=True)
        return int(response.json().get("port"))
    except Exception as e:
        print(f"[ERROR] Failed to get forwarded port from Gluetun: {e}", flush=True)
        return None

# ---------------------------
# Log in to qBittorrent and set the listening port
# ---------------------------
def set_qbittorrent_port(port):
    try:
        session = requests.Session()

        # Step 1: Login to qBittorrent Web UI
        login_response = session.post(QBITTORRENT_LOGIN, data={
            "username": QBITTORRENT_USER,
            "password": QBITTORRENT_PASS
        })

        if login_response.status_code != 200:
            print(f"[ERROR] Login to qBittorrent failed: {login_response.status_code} - {login_response.text}", flush=True)
            return

        # Step 2: Set new listening port using JSON payload
        prefs = {
            "listen_port": port
        }

        # Wrap the JSON object as a string under the 'json' key
        update_response = session.post(QBITTORRENT_API, data={"json": json.dumps(prefs)})
        print(f"[DEBUG] qBittorrent API response: {update_response.status_code} - {update_response.text}", flush=True)

        if update_response.status_code == 200:
            print(f"[INFO] Updated qBittorrent port to {port}", flush=True)
        else:
            print(f"[ERROR] Failed to update qBittorrent port: {update_response.status_code} - {update_response.text}", flush=True)

    except Exception as e:
        print(f"[ERROR] Exception updating qBittorrent port: {e}", flush=True)

# ---------------------------
# Main loop to poll Gluetun every 5 minutes
# ---------------------------
def main():
    last_port = None
    print("[INFO] qb-port-sync script started", flush=True)

    while True:
        port = get_forwarded_port()
        if port and port != last_port:
            print(f"[INFO] Detected new port: {port}", flush=True)
            set_qbittorrent_port(port)
            last_port = port
        else:
            print("[DEBUG] No new port or port unchanged.", flush=True)

        # Wait 5 minutes before checking again
        time.sleep(300)

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    main()
