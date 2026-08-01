# ****** READ THIS ******
# This script lists your Nile guest portals by name, lets you choose one, and then
# lets you view, create, edit, or delete the access codes configured for that portal.
# Dependencies: requests, python-dotenv, tabulate

import requests
from dotenv import load_dotenv
from tabulate import tabulate
from datetime import datetime
import os

# Load environment variables
load_dotenv()
nile_apikey = os.getenv("NILE_GUESTAPI_TOKEN")

headers = {
    "Content-Type": "application/json",
    "x-nile-api-key": nile_apikey
}


def get_portals():
    url = "https://u1.nile-global.cloud/api/v1/portalconfig/summary"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching portal summary: {response.status_code} - {response.text}")
        exit(1)

    return response.json().get("content", [])


def portal_type_label(portal):
    if portal["portalType"] == "Email-Approval":
        return "Email Approval"
    if portal["genericAccessCode"]:
        return "Generic Access Code"
    return "Guest Specific Access Code"


def choose_portal(portals):
    while True:
        print("Which Portal you want to work with?")
        for i, portal in enumerate(portals):
            print(f"{i + 1}: {portal['name']} ({portal_type_label(portal)})")

        choice = input("Select a portal by number: ").strip()
        try:
            index = int(choice) - 1
            if index < 0:
                raise IndexError
            portal = portals[index]
        except (ValueError, IndexError):
            print(f"Invalid selection: {choice}\n")
            continue

        if portal["portalType"] == "Email-Approval":
            print("Invalid Portal Type - Please choose an Access Code Portal Type\n")
            continue

        print(f"'{portal['name']}' is a {portal_type_label(portal)} Portal.")

        return portal


def get_access_codes(portal_id):
    portal_url = f"https://u1.nile-global.cloud/api/v2/portalconfig/{portal_id}/access-codes"
    response = requests.get(portal_url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching access codes: {response.status_code} - {response.text}")
        exit(1)

    return response.json()


def display_access_codes(access_codes):
    codes = access_codes.get("content", [])
    if not codes:
        print("No access codes found for this portal.")
        return

    rows = []
    for code in codes:
        rows.append({
            "Access Code": code.get("accessCode", ""),
            "Guest Name": code.get("guestName") or "-",
            "Guest Email": code.get("guestEmail") or "-",
            "Start Time": code.get("startTime", ""),
            "End Time": code.get("endTime", ""),
            "Expires": code.get("expires", ""),
        })

    print(tabulate(rows, headers="keys", tablefmt="grid"))


def ask_yes_no(prompt):
    while True:
        answer = input(f"{prompt} (yes/no): ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please enter 'yes' or 'no'.")


def ask_datetime(label):
    while True:
        value = input(f"Enter {label} (MM/DD/YYYY HH:MM, 24-hour): ").strip()
        try:
            dt = datetime.strptime(value, "%m/%d/%Y %H:%M")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            print("Invalid format. Please use MM/DD/YYYY HH:MM (e.g. 01/16/2026 09:00).\n")


def confirm_access_code_value():
    value = input("Enter the Access Code value: ").strip()
    confirm_value = input("Re-enter the Access Code value to confirm: ").strip()
    if value != confirm_value:
        print("The values you entered do not match.\n")
        return None
    return value


def find_access_code(portal_id, value):
    access_codes = get_access_codes(portal_id)
    for code in access_codes.get("content", []):
        if code.get("accessCode") == value:
            return code
    return None


def confirm_guest_email():
    email = input("Enter the guest's email: ").strip()
    confirm_email = input("Re-enter the guest's email to confirm: ").strip()
    if email.lower() != confirm_email.lower():
        print("The values you entered do not match.\n")
        return None
    return email


def find_access_code_by_guest_email(portal_id, email):
    access_codes = get_access_codes(portal_id)
    for code in access_codes.get("content", []):
        if (code.get("guestEmail") or "").lower() == email.lower():
            return code
    return None


def ask_count(prompt):
    while True:
        value = input(f"{prompt} ").strip()
        try:
            count = int(value)
            if count < 1:
                raise ValueError
            return count
        except ValueError:
            print("Please enter a whole number greater than 0.")


def post_access_codes(portal, payload):
    url = f"https://u1.nile-global.cloud/api/v2/portalconfig/{portal['id']}/access-codes"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in (200, 201, 204):
        message = response.json().get("data", {}).get("message", "Access code(s) created successfully.")
        print(message)
    else:
        print(f"Error creating access code(s): {response.status_code} - {response.text}")


def create_generic_access_code(portal):
    print("\n--- Create Access Code ---")
    expires = ask_yes_no("Should this access code expire?")
    start_time = ask_datetime("start date/time") if expires else None
    end_time = ask_datetime("end date/time") if expires else None
    access_code_value = input("Enter the access code value: ").strip()

    payload = {
        "expires": expires,
        "generatePerGuest": False,
        "startTime": start_time,
        "endTime": end_time,
        "sendEmail": False,
        "useTags": False,
        "targets": [
            {"accessCode": access_code_value}
        ]
    }

    post_access_codes(portal, payload)


def create_guest_specific_codes(portal):
    print("\n--- Create Guest Specific Access Codes ---")
    expires = ask_yes_no("Should these access codes expire?")
    start_time = ask_datetime("start date/time") if expires else None
    end_time = ask_datetime("end date/time") if expires else None
    count = ask_count("How many guests do you want to create codes for?")

    targets = []
    for i in range(count):
        print(f"\nGuest {i + 1}:")
        access_code_value = input("  Enter the access code value: ").strip()
        guest_name = input("  Enter the guest name: ").strip()
        guest_email = input("  Enter the guest email: ").strip()
        targets.append({
            "accessCode": access_code_value,
            "guestName": guest_name,
            "guestEmail": guest_email
        })

    payload = {
        "expires": expires,
        "generatePerGuest": False,
        "startTime": start_time,
        "endTime": end_time,
        "sendEmail": False,
        "useTags": False,
        "targets": targets
    }

    post_access_codes(portal, payload)


def create_system_generated_codes(portal):
    print("\n--- Create System Generated Access Codes ---")
    expires = ask_yes_no("Should these access codes expire?")
    start_time = ask_datetime("start date/time") if expires else None
    end_time = ask_datetime("end date/time") if expires else None
    count = ask_count("How many guests do you want to create codes for?")

    targets = []
    for i in range(count):
        print(f"\nGuest {i + 1}:")
        guest_name = input("  Enter the guest name: ").strip()
        guest_email = input("  Enter the guest email: ").strip()
        targets.append({
            "guestName": guest_name,
            "guestEmail": guest_email
        })

    payload = {
        "expires": expires,
        "generatePerGuest": True,
        "startTime": start_time,
        "endTime": end_time,
        "sendEmail": False,
        "useTags": False,
        "targets": targets
    }

    post_access_codes(portal, payload)


def create_shared_event_code(portal):
    print("\n--- Create Shared Event Access Code ---")
    expires = ask_yes_no("Should this access code expire?")
    start_time = ask_datetime("start date/time") if expires else None
    end_time = ask_datetime("end date/time") if expires else None
    shared_access_code = input("Enter the shared access code value: ").strip()
    count = ask_count("How many guests do you want to add to this shared code?")

    targets = []
    for i in range(count):
        print(f"\nGuest {i + 1}:")
        guest_name = input("  Enter the guest name: ").strip()
        guest_email = input("  Enter the guest email: ").strip()
        targets.append({
            "guestName": guest_name,
            "guestEmail": guest_email
        })

    payload = {
        "expires": expires,
        "sharedAccessCode": shared_access_code,
        "generatePerGuest": False,
        "startTime": start_time,
        "endTime": end_time,
        "sendEmail": False,
        "useTags": False,
        "targets": targets
    }

    post_access_codes(portal, payload)


def create_access_code(portal):
    if portal["genericAccessCode"]:
        create_generic_access_code(portal)
        return

    while True:
        print("\nWhich type of Guest Specific access code do you want to create?")
        print("1: Guest Specific (you provide each guest's code)")
        print("2: System Generated (system generates a unique code per guest)")
        print("3: Shared Event (one shared code for multiple guests)")
        print("4: Back")
        print("5: Quit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            create_guest_specific_codes(portal)
            return
        elif choice == "2":
            create_system_generated_codes(portal)
            return
        elif choice == "3":
            create_shared_event_code(portal)
            return
        elif choice == "4":
            return
        elif choice == "5":
            print("Exiting.")
            exit(0)
        else:
            print(f"Invalid selection: {choice}\n")


def edit_generic_access_code(portal):
    print("\n--- Edit Access Code ---")
    value = confirm_access_code_value()
    if value is None:
        return

    code = find_access_code(portal["id"], value)
    if not code:
        print(f"No access code matching '{value}' was found in this portal.\n")
        return

    print(f"Editing access code '{value}' (ID: {code['id']})")
    expires = ask_yes_no("Should this access code expire?")
    start_time = ask_datetime("start date/time") if expires else None
    end_time = ask_datetime("end date/time") if expires else None

    payload = {
        "expires": expires,
        "generatePerGuest": code.get("generated", False),
        "startTime": start_time,
        "endTime": end_time,
        "sendEmail": False,
        "useTags": False,
        "targets": [
            {"id": code["id"], "accessCode": value}
        ]
    }

    url = f"https://u1.nile-global.cloud/api/v2/portalconfig/{portal['id']}/access-codes"
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code in (200, 204):
        print(f"Access code '{value}' updated successfully.")
    else:
        print(f"Error updating access code: {response.status_code} - {response.text}")


def edit_guest_access_code(portal):
    print("\n--- Edit Access Code (Guest Specific) ---")
    email = confirm_guest_email()
    if email is None:
        return

    code = find_access_code_by_guest_email(portal["id"], email)
    if not code:
        print(f"No access code matching guest email '{email}' was found in this portal.\n")
        return

    print(f"Editing access code for {code.get('guestName') or email} (ID: {code['id']})")
    expires = ask_yes_no("Should this access code expire?")
    start_time = ask_datetime("start date/time") if expires else None
    end_time = ask_datetime("end date/time") if expires else None

    payload = {
        "expires": expires,
        "generatePerGuest": code.get("generated", False),
        "startTime": start_time,
        "endTime": end_time,
        "sendEmail": False,
        "useTags": False,
        "targets": [
            {"id": code["id"]}
        ]
    }

    url = f"https://u1.nile-global.cloud/api/v2/portalconfig/{portal['id']}/access-codes"
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code in (200, 204):
        print(f"Access code for {email} updated successfully.")
    else:
        print(f"Error updating access code: {response.status_code} - {response.text}")


def edit_access_code(portal):
    if portal["genericAccessCode"]:
        edit_generic_access_code(portal)
    else:
        edit_guest_access_code(portal)


def delete_generic_access_code(portal):
    print("\n--- Delete Access Code ---")
    value = confirm_access_code_value()
    if value is None:
        return

    code = find_access_code(portal["id"], value)
    if not code:
        print(f"No access code matching '{value}' was found in this portal.\n")
        return

    if not ask_yes_no(f"Are you sure you want to delete access code '{value}'? This cannot be undone."):
        print("Delete cancelled.\n")
        return

    url = f"https://u1.nile-global.cloud/api/v2/portalconfig/{portal['id']}/access-codes"
    response = requests.delete(url, headers=headers, json={"targets": [{"id": code["id"]}]})

    if response.status_code in (200, 204):
        print(f"Access code '{value}' deleted successfully.")
    else:
        print(f"Error deleting access code: {response.status_code} - {response.text}")


def delete_guest_access_code(portal):
    print("\n--- Delete Access Code (Guest Specific) ---")
    email = confirm_guest_email()
    if email is None:
        return

    code = find_access_code_by_guest_email(portal["id"], email)
    if not code:
        print(f"No access code matching guest email '{email}' was found in this portal.\n")
        return

    guest_label = code.get("guestName") or email
    if not ask_yes_no(f"Are you sure you want to delete the access code for {guest_label}? This cannot be undone."):
        print("Delete cancelled.\n")
        return

    url = f"https://u1.nile-global.cloud/api/v2/portalconfig/{portal['id']}/access-codes"
    response = requests.delete(url, headers=headers, json={"targets": [{"guestEmail": email, "guestName": code.get("guestName")}]})

    if response.status_code in (200, 204):
        print(f"Access code for {email} deleted successfully.")
    else:
        print(f"Error deleting access code: {response.status_code} - {response.text}")


def delete_access_code(portal):
    if portal["genericAccessCode"]:
        delete_generic_access_code(portal)
    else:
        delete_guest_access_code(portal)


def portal_menu(portal):
    while True:
        print(f"\n--- {portal['name']} ---")
        print("1: View Access Codes")
        print("2: Create Access Code")
        print("3: Edit Access Code")
        print("4: Delete Access Code")
        print("5: Switch Portal")
        print("6: Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            access_codes = get_access_codes(portal["id"])
            display_access_codes(access_codes)
        elif choice == "2":
            create_access_code(portal)
        elif choice == "3":
            edit_access_code(portal)
        elif choice == "4":
            delete_access_code(portal)
        elif choice == "5":
            return "switch"
        elif choice == "6":
            return "exit"
        else:
            print(f"Invalid selection: {choice}\n")


if __name__ == "__main__":
    portals = get_portals()
    while True:
        selected_portal = choose_portal(portals)
        action = portal_menu(selected_portal)
        if action == "exit":
            break
