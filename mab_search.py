# ****** READ THIS ******
# This script allows users to search for devices based on specific criteria (e.g., MAC address, device type, port, state) and then update their 
# segment and state in bulk.
# Dependencies: requests, python-dotenv, GET_seg.py, GET_MAB.py

import json
import requests
import GET_seg
import GET_MAB
from pprint import pp
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Setup logging
log_filename = "search_device_segment_changes.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Load API key
nile_apikey = os.getenv("NILE_API_TOKEN")

# Fetch segments and devices
segments = GET_seg.get_segments()
devices = GET_MAB.get_devices()

# Log the fetch of segments and devices
logging.info("Fetched segments and devices.")

if not segments:
    logging.error("No segments found. Check API call in GET_seg.")
    print("No segments found. Check API call in GET_seg.")
    exit(1)

if not devices:
    logging.error("No devices found. Check API call in GET_MAB.")
    print("No devices found. Check API call in GET_MAB.")
    exit(1)


# Function to filter devices based on search criteria
def search_devices(devices, search_term, search_field="macAddress"):
    """
    Filter devices by checking both clientInfo and clientConfig for the field.
    """
    filtered = []

    for device in devices:
        client_info = device.get("clientInfo") or {}
        client_config = device.get("clientConfig") or {}

        # Look in both sections
        value = client_info.get(search_field) or client_config.get(search_field)

        if value and search_term.lower() in str(value).lower():
            filtered.append(device)

    return filtered


# Ask user for a search term
search_term = input("Enter a search term to filter devices (e.g., MAC, device type, port, state): ").strip()

# Allow user to choose the field for search
search_field = input("Choose the field for search (options: macAddress, deviceType, port, state): ").strip()

# Validate the search field
valid_fields = ["macAddress", "deviceType", "port", "state"]
if search_field not in valid_fields:
    logging.error(f"Invalid search field: {search_field}")
    print(f"Invalid search field: {search_field}. Valid options are: {', '.join(valid_fields)}")
    exit(1)

# Filter the devices based on the search term and field
filtered_devices = search_devices(devices, search_term, search_field)

# Display the filtered devices or exit
if not filtered_devices:
    logging.error("No devices found matching the search criteria.")
    print("No devices found matching the search criteria.")
    exit(1)
else:
    print("Filtered Devices:")
    for i, device in enumerate(filtered_devices):
        client_info = device.get('clientInfo') or {}
        client_config = device.get('clientConfig') or {}
        device_type = client_info.get('deviceType', 'Unknown')
        port = client_config.get('port', 'Unknown')
        state = client_config.get('state', 'Unknown')
        mac = client_info.get('macAddress') or client_config.get('macAddress', 'Unknown')
        print(f"{i + 1}: DeviceType: {device_type}, Port: {port}, State: {state}, MAC: {mac}")


# User selects devices
device_indices = input(":arrow_right:  Select multiple devices by numbers (comma separated): ")
selected_device_indices = [int(idx.strip()) - 1 for idx in device_indices.split(",")]

# Validate and log selected devices
selected_devices = []
for idx in selected_device_indices:
    try:
        selected_device = filtered_devices[idx]
        selected_devices.append(selected_device)
        logging.info(f"User selected device: {selected_device['clientInfo']['macAddress']}")
    except IndexError:
        logging.error(f"Invalid device index: {idx + 1}")
        print(f"Invalid device index: {idx + 1}. Please check your input.")
        exit(1)

# Display segments
print("\nAvailable Segments:")
for i, seg in enumerate(segments):
    print(f"{i + 1}: {seg['Segment']} (ID: {seg['ID']})")

# User selects segment
segment_index = int(input("Select a segment by number: ")) - 1
selected_segment = segments[segment_index]

# Log segment selection
logging.info(f"User selected segment: {selected_segment['Segment']} (ID: {selected_segment['ID']})")

# Confirmation Summary
print("\n--- Summary ---")
print(f"Selected Devices: {[device['clientInfo']['macAddress'] for device in selected_devices]}")
print(f"New Segment: {selected_segment['Segment']} (ID: {selected_segment['ID']})")
print("State will be updated to: AUTH_OK")

# Log summary
logging.info(f"Selected Devices: {[device['clientInfo']['macAddress'] for device in selected_devices]}")
logging.info(f"Selected Segment: {selected_segment['Segment']} (ID: {selected_segment['ID']})")
logging.info("State will be updated to AUTH_OK.")

confirm = input("Confirm changes for all selected devices? (yes/no): ").strip().lower()

# Log confirmation
if confirm == 'yes':
    logging.info("User confirmed changes. Sending PATCH request.")

    # Prepare the list of devices to update
    macs_list = []
    for device in selected_devices:
        mac_address = device['clientInfo']['macAddress']
        macs_list.append({
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
        })

    # Send the PATCH request for bulk update
    url = "https://u1.nile-global.cloud/api/v1/client-configs"
    payload = {
        "macsList": macs_list
    }
    headers = {
        "Content-Type": "application/json",
        "x-nile-api-key": nile_apikey
    }

    response = requests.patch(url, headers=headers, json=payload)

    # Log the response
    if response.status_code in [200, 204]:
        logging.info(f"Bulk update successful. HTTP {response.status_code}")
        print(f"Bulk update successful (status: {response.status_code}).")
    else:
        logging.error(f"Bulk update failed. HTTP {response.status_code} - {response.text}")
        print(f"Bulk update failed: {response.status_code} - {response.text}")
else:
    logging.warning("User canceled the operation.")
    print("Operation cancelled.")
