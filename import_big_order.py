import json

import requests


def read_env(path):
    env = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


env = read_env(".env")
url = env["RETAILCRM_URL"].rstrip("/") + "/api/v5/orders/create"
api_key = env["RETAILCRM_API_KEY"]
site = env["RETAILCRM_SITE"]

order = {
    "site": site,
    "firstName": "Big",
    "lastName": "Order",
    "phone": "+77009990000",
    "email": "big.order@example.com",
    "orderType": "eshop-individual",
    "orderMethod": "shopping-cart",
    "status": "new",
    "items": [
        {
            "productName": "Premium Test Product",
            "quantity": 1,
            "initialPrice": 70000,
        }
    ],
    "delivery": {
        "address": {
            "city": "Almaty",
            "text": "Test street 1, apt 1",
        }
    },
}

order.pop("orderType", None)
order.pop("orderMethod", None)
order.pop("status", None)

response = requests.post(
    url,
    headers={"X-API-KEY": api_key},
    data={
        "site": site,
        "order": json.dumps(order, ensure_ascii=False),
    },
)

print(url)
print(response.status_code)
print(response.text)

try:
    result = response.json()
except Exception:
    result = {}

if result.get("success") is True:
    print("created")
else:
    print("error")
