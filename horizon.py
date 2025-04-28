import requests
from config import HORIZON_URL

def get_account_info(account_id):
    url = f"{HORIZON_URL}/accounts/{account_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch account info.")
        return None