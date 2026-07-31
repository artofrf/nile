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

# Portal ID
portal_id = f"b531a73e-6996-4279-88d5-468b3ddec22e"

# URLs for API calls
portal_url = f'https://u1.nile-global.cloud/api/v2/portalconfig/{portal_id}/access-codes'

    #payload = []
headers = {
    "Content-Type": "application/json",
    "x-nile-api-key": nile_apikey
    }

response = requests.get(portal_url, headers=headers)
data = response.json()
print(json.dumps(data, indent=4))
