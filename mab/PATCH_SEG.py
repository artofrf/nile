import json
import requests
import GET_seg
import GET_MAB
from pprint import pp
from dotenv import load_dotenv
import os
nile_apikey = os.getenv("NILE_API_KEY")
import logging
from datetime import datetime

# Setup logging
log_filename = "device_segment_changes.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Fetch segments and devices
segments = GET_seg.get_segments()
devices = GET_MAB.get_devices()

# Log the fetch of segments and devices
logging.info("Fetched segments and devices.")

if not segments:
    logging.error("❌ No segments found. Check API call in GET_seg.")
    print("❌ No segments found. Check API call in GET_seg.")
    exit(1)

if not devices:
    logging.error("❌ No devices found. Check API call in GET_MAB.")
    print("❌ No devices found. Check API call in GET_MAB.")
    exit(1)

# Display available devices
print("📱 Available Devices:")
for i, device in enumerate(devices):
    client_info = device.get('clientInfo', {})
    client_config = device.get('clientConfig', {})
    device_type = client_config.get('deviceType', 'Unknown')
    port = client_config.get('port', 'Unknown')
    state = client_config.get('state', 'Unknown')
    mac = client_config.get('macAddress', 'Unknown')
    print(f"{i + 1}: DeviceType: {device_type}, Port: {port}, State: {state}, MAC: {mac}")

# Log device selection
try:
    device_index = int(input("➡️  Select a device by number: ")) - 1
    selected_device = devices[device_index]
    logging.info(f"User selected device: {selected_device['clientInfo']['macAddress']}")
except (IndexError, ValueError):
    logging.error("❌ Invalid device selection.")
    print("❌ Invalid device selection.")
    exit(1)

mac_address = selected_device['clientInfo']['macAddress']

# Display segments
print("\n🌐 Available Segments:")
for i, seg in enumerate(segments):
    print(f"{i + 1}: {seg['Segment']} (ID: {seg['ID']})")

# Log segment selection
try:
    segment_index = int(input("➡️  Select a segment by number: ")) - 1
    selected_segment = segments[segment_index]
    logging.info(f"User selected segment: {selected_segment['Segment']} (ID: {selected_segment['ID']})")
except (IndexError, ValueError):
    logging.error("❌ Invalid segment selection.")
    print("❌ Invalid segment selection.")
    exit(1)

# Confirmation Summary
print("\n--- Summary ---")
print(f"MAC Address: {mac_address}")
print(f"New Segment: {selected_segment['Segment']} (ID: {selected_segment['ID']})")
print("State will be updated to: AUTH_OK")

# Log summary
logging.info(f"MAC Address: {mac_address}")
logging.info(f"Selected Segment: {selected_segment['Segment']} (ID: {selected_segment['ID']})")
logging.info("State will be updated to AUTH_OK.")

confirm = input("✅ Confirm changes? (yes/no): ").strip().lower()

# Log confirmation
if confirm == 'yes':
    logging.info("User confirmed changes. Sending PATCH request.")

    url = "https://u1.nile-global.cloud/api/v1/client-configs"
    payload = {
        "macsList": [
            {
                "macAddress": mac_address,
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
    headers = {
        "Content-Type": "application/json",
        "x-nile-api-key": nile_apikey
    }

    response = requests.patch(url, headers=headers, json=payload)

    # Log the response
    if response.status_code in [200, 204]:
        logging.info(f"Update successful. HTTP {response.status_code}")
        print(f"✅ Update successful (status: {response.status_code}).")
    else:
        logging.error(f"Update failed. HTTP {response.status_code} - {response.text}")
        print(f"❌ Update failed: {response.status_code} - {response.text}")
else:
    logging.warning("User canceled the operation.")
    print("🚫 Operation cancelled.")
