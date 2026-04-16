import json
import time

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

with open("mock_orders.json", "r", encoding="utf-8") as f:
    orders = json.load(f)

created_count = 0
error_count = 0
total = len(orders)

start_index = 23

for i, order in enumerate(orders[start_index:], start=start_index):
    order.pop("orderType", None)
    order.pop("orderMethod", None)
    order.pop("status", None)

    order_number = i + 1

    try:
        response = requests.post(
            url,
            headers={"X-API-KEY": api_key},
            data={
                "site": site,
                "order": json.dumps(order, ensure_ascii=False),
            },
            timeout=30,
        )

        print(order_number)
        print(response.status_code)
        print(response.text)

        try:
            result = response.json()
        except Exception:
            result = {}

        if result.get("success") is True:
            created_count += 1
        else:
            error_count += 1
    except Exception as e:
        print(order_number)
        print("ERROR")
        print(str(e))
        error_count += 1

    time.sleep(1)

print(total)
print(created_count)
print(error_count)
