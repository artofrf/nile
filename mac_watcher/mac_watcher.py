import json
import time
import requests
import GET_seg
import GET_MAB
from pprint import pp
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
nile_apikey = os.getenv("NILE_API_KEY")

# === Logging Setup ===
log_filename = "mac_segment_updates.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === State Storage for Previously Seen MACs ===
STATE_FILE = "seen_macs.json"

def load_seen_macs():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_macs(mac_set):
    with open(STATE_FILE, "w") as f:
        json.dump(list(mac_set), f)

# === API Setup ===
url = "https://u1.nile-global.cloud/api/v1/client-configs"
headers = {
    "Content-Type": "application/json",
    "x-nile-api-key": nile_apikey
}

# === Loop every 1 minutes ===
print("⏳ Starting MAC watcher (checks every 1 minute). Ctrl+C to exit.")
seen_macs = load_seen_macs()

while True:
    try:
        logging.info("🔄 Checking for new MAC addresses...")
        devices = GET_MAB.get_devices()
        segments = GET_seg.get_segments()

        if not devices:
            logging.warning("⚠️ No devices found.")
            time.sleep(60)
            continue

        # Collect all MACs currently seen
        current_macs = set()
        mac_to_device = {}

        for device in devices:
            mac = device.get('clientInfo', {}).get('macAddress')
            if mac:
                current_macs.add(mac)
                mac_to_device[mac] = device

        # Find new MACs
        new_macs = current_macs - seen_macs

        if not new_macs:
            logging.info("✅ No new MAC addresses found.")
            time.sleep(60)
            continue

        logging.info(f"📡 Detected new MACs: {new_macs}")

        # Prompt user for each new MAC
        for mac in new_macs:
            device = mac_to_device[mac]
            device_type = device.get('clientInfo', {}).get('deviceType', 'Unknown')
            port = device.get('clientConfig', {}).get('port', 'Unknown')
            state = device.get('clientConfig', {}).get('state', 'Unknown')

            print(f"\n🆕 New Device Detected:")
            print(f"MAC: {mac}, Type: {device_type}, Port: {port}, State: {state}")
            choice = input("❓ Would you like to assign this MAC to a segment? (yes/no): ").strip().lower()

            if choice != 'yes':
                logging.info(f"User skipped MAC: {mac}")
                seen_macs.add(mac)
                continue

            # Show segments
            print("\n📂 Available Segments:")
            for i, seg in enumerate(segments):
                print(f"{i + 1}: {seg['Segment']} (ID: {seg['ID']})")

            seg_choice = int(input("➡️ Select a segment by number: ")) - 1
            selected_segment = segments[seg_choice]

            payload = {
                "macsList": [
                    {
                        "macAddress": mac,
                        "description": None,
                        "rule": "",
                        "ruleType": "INDIVIDUAL",
                        "segmentId": selected_segment['ID'],
                        "state": "AUTH_OK",
                        "geoScope": {
                            "siteIds": [],
                            "buildingIds": [],
                            "floorIds": []
                        },
                        "staticIp": None,
                        "silentIp": None,
                        "ipAddress": ""
                    }
                ]
            }

            response = requests.patch(url, headers=headers, json=payload)
            if response.status_code in [200, 204]:
                print(f"✅ Successfully updated segment for MAC: {mac}")
                logging.info(f"Segment update success for {mac} to {selected_segment['Segment']}")
                seen_macs.add(mac)
            else:
                print(f"❌ Failed to update MAC: {mac} - {response.status_code}: {response.text}")
                logging.error(f"Segment update failed for {mac}: {response.status_code} - {response.text}")

        # Save updated seen list
        save_seen_macs(seen_macs)
        print("⏳ Waiting 1 minutes before next check...\n")
        time.sleep(60)

    except KeyboardInterrupt:
        print("🛑 Exiting watcher.")
        break
    except Exception as e:
        logging.exception(f"❌ Exception occurred: {e}")
        time.sleep(60)
