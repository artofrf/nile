import json
import sys
import requests
from pprint import pp
import pandas as pd
from tabulate import tabulate

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API key from environment variables
nile_apikey = os.getenv("NILE_API_TOKEN")

#requested_data = input('Enter Data Requested:'  )
url = f'https://u1.nile-global.cloud/api/v1/public/client-list-paginated-details?endTime=2025-06-23T17%3A46%3A14Z&startTime=2025-06-20T17%3A46%3A14Z&pageNumber=0&pageSize=99999'

payload = ''
headers = {
    'Content-Type': 'application/json',
    'x-nile-api-key': nile_apikey
           }
response = requests.get(url, headers=headers, data=payload)

if response.status_code != 200:
    sys.exit(f"Error fetching devices: HTTP {response.status_code} - {response.text}")

if 'application/json' not in response.headers.get('Content-Type', ''):
    sys.exit(
        "Error fetching devices: API did not return JSON (got "
        f"{response.headers.get('Content-Type', 'unknown')}). This usually means "
        "the API key was rejected and Nile returned a login page instead."
    )

try:
    api_output = response.json()
except json.JSONDecodeError as e:
    sys.exit(f"Error fetching devices: failed to parse JSON response - {e}")



def get_devices():
    rows = []
    client_list = api_output.get('clientList', [])
    for client_info in client_list:
        if not isinstance(client_info, dict):
            continue
        if client_info.get('connectionType') == 'wireless':
            continue
        if client_info.get('clientStatus') not in ('ONLINE', 'OFFLINE'):
            continue #SKIP THE REST - NOT USING "IN" BECAUSE I WAN TO EXCLUDE A LONG LIST OF STATUSES

        row = {
            'Switch Name': client_info.get('serialName', ''),
            'Segment': client_info.get('segment', ''),
            'MAC Address': client_info.get('macAddress', ''),
            'Device Type': client_info.get('deviceType', ''),
            'Site Name': client_info.get('siteName', ''),
            'Port Number': client_info.get('port', ''),
            'IP Address': client_info.get('ipAddress', ''),
            'Client Status': client_info.get('clientStatus', '')
        }
        rows.append(row)
    return rows

if __name__ == "__main__":
    devices = get_devices()
    df = pd.DataFrame(devices)
    df.to_excel("jcsu_devices.xlsx", index=False)
    print(f"✅ Exported {len(devices)} device(s) to 'jcsu_devices.xlsx'")

