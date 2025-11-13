import json
import os
import time
from uuid import uuid4

import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(".env")

BASE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
INBOUND_ID = os.getenv("INBOUND_ID")
DAYS_VALID = 90


def auth():
    """Auth in x-ui api."""
    session = requests.Session()
    login_data = {"username": USERNAME, "password": PASSWORD}
    resp = session.post(f"{BASE_URL}/login", data=login_data, verify=False)

    if resp.status_code != 200:
        print(resp)
        raise ValueError("Auth failed.")

    print("✅ Authorized...")
    return session


def add_xui_client(user_id: int, nickname: str, obfuscated_user: str):
    """Adding new x-ui client via api on https."""
    session = auth()
    expiry_timestamp = int((time.time() + DAYS_VALID * 86400) * 1000)

    clients_json = {
        "clients": [
            {
                "id": obfuscated_user,
                "tgId": str(user_id),
                "email": f"{obfuscated_user}@vray",
                "enable": True,
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": expiry_timestamp,
            }
        ]
    }

    payload = {"id": int(INBOUND_ID), "settings": json.dumps(clients_json)}
    response = session.post(
        f"{BASE_URL}/panel/api/inbounds/addClient", json=payload, verify=False
    )

    print(f"Server response:\n{response.text}")

    if response.ok and response.json().get("success"):
        print("✅ Client successfully added!")
    else:
        print("❌ Client was not added.")


def get_client_info(email: str):
    """Get client info."""
    session = auth()
    response = session.get(
        f"{BASE_URL}/panel/api/inbounds/getClientTraffics/{email}", verify=False
    )
    print(response)
    if response.status_code == 200:
        print(response.text)
        data = response.json()
        sub_id = data.get("obj", {}).get("subId", [])
        print(sub_id)
        return sub_id
    return []


if __name__ == "__main__":
    # add_xui_client(os.getenv("ADMIN"), "test_nick2", "test")
    get_clients("test@vray")
