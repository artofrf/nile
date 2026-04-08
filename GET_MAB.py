import json
import sys
import requests
from pprint import pp
from dotenv import load_dotenv
import os
# Load environment variables
load_dotenv()
nile_apikey = os.getenv("NILE_API_TOKEN")
#requested_data = input('Enter Data Requested:'  )
url = f'https://u1.nile-global.cloud/api/v1/client-configs-list'

payload = ''
headers = {
    'Content-Type': 'application/json',
    'x-nile-api-key': nile_apikey
           }
response = requests.get(url, headers=headers, data=payload)
#pp(response.status_code)
api_output = response.json()
#pp(api_output)

def get_devices():
    response = requests.get(url, headers=headers, data=payload)
    if response.status_code != 200:
        print(f"Error Fetching: {response.status_code} - {response.text}")
        return []
    try:
        api_output = response.json()
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return []

        # Validate structure
    if not isinstance(api_output, list):
        print("Unexpected response format — expected a list of devices.")
        pp(api_output)
        return []

    return api_output

if __name__ == "__main__":
    devices = get_devices()
    pp(devices)

if __name__ == "__main__":
    devices = get_devices()
    from pprint import pprint
    pprint(devices)

print(response.status_code)
# def get_mab():
#     rows = []
#     for item in api_output:
#         # Ensure 'clientInfo' and 'clientConfig' are valid
#         client_info = item.get('clientInfo', None)
#         client_config = item.get('clientConfig', None)
#
#         if not client_info or not isinstance(client_info, dict):
#             client_info = {}
#         if not client_config or not isinstance(client_config, dict):
#             client_config = {}
#
#         row = {
#             'Device Type': client_info.get('deviceType', ''),
#             'Device Mfg': client_info.get('deviceManufacturer', ''),
#             'Serial No': client_config.get('serialNo', ''),
#             'Authenticated By': client_config.get('authenticatedBy', ''),
#             'Port Number': client_config.get('port', ''),
#             'State': client_config.get('state', ''),
#             'Segment ID': client_config.get('segmentID', '')
#         }
#         rows.append(row)
#
#     pp(rows)
