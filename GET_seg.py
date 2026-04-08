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
url = f'https://u1.nile-global.cloud/api/v1/settings/segments/'
payload = ''
headers = {
    'Content-Type': 'application/json',
    'x-nile-api-key': nile_apikey
           }
response = requests.get(url, headers=headers, data=payload)
#print(response.status_code)
api_output = response.json()
#pp(api_output)

def get_segments():
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching segments: {response.status_code} - {response.text}")
        return []

    try:
        data = response.json()
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return []

    # Extract segment list from nested JSON
    try:
        content_list = data["data"]["content"]
    except KeyError as e:
        print(f"Unexpected response structure: missing key {e}")
        pp(data)
        return []

    segments = []
    for item in content_list:
        seg_id = item.get("id")
        name = item.get("instanceName") or item.get("segment", {}).get("name")
        if seg_id and name:
            segments.append({"ID": seg_id, "Segment": name})
        else:
            print("Skipping segment due to missing ID or name:")
            pp(item)

    return segments


if __name__ == "__main__":
    segments = get_segments()
    pp(segments)