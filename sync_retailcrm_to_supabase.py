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

retailcrm_url = env["RETAILCRM_URL"].rstrip("/") + "/api/v5/orders"
retailcrm_api_key = env["RETAILCRM_API_KEY"]
retailcrm_site = env["RETAILCRM_SITE"]

supabase_url = env["SUPABASE_URL"].rstrip("/") + "/rest/v1/orders?on_conflict=retailcrm_id"
supabase_key = env["SUPABASE_KEY"]

headers_retailcrm = {"X-API-KEY": retailcrm_api_key}
headers_supabase = {
    "apikey": supabase_key,
    "Authorization": f"Bearer {supabase_key}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge duplicates",
}

page = 1
limit = 100
processed_total = 0
uploaded_total = 0
batch_size = 10

while True:
    resp = requests.get(
        retailcrm_url,
        headers=headers_retailcrm,
        params={"site": retailcrm_site, "limit": limit, "page": page},
    )

    if resp.status_code >= 400:
        print("RetailCRM error:", resp.text)
        break

    try:
        payload = resp.json()
    except Exception:
        print("RetailCRM error:", resp.text)
        break

    orders = payload.get("orders") or payload.get("data") or []
    print(page)
    print(len(orders))

    if not orders:
        break

    records = []
    for order in orders:
        items = order.get("items") or []
        items_count = 0
        for item in items:
            qty = item.get("quantity")
            if isinstance(qty, (int, float)):
                items_count += qty

        delivery = order.get("delivery") or {}
        address = delivery.get("address") or {}
        custom_fields = order.get("customFields") or {}
        utm_source = None
        if isinstance(custom_fields, dict):
            utm_source = custom_fields.get("utm_source")

        total_sum = order.get("totalSumm") if "totalSumm" in order else order.get("summ")

        records.append(
            {
                "retailcrm_id": order.get("id"),
                "order_number": order.get("number"),
                "created_at": order.get("createdAt"),
                "status": order.get("status"),
                "first_name": order.get("firstName"),
                "last_name": order.get("lastName"),
                "phone": order.get("phone"),
                "email": order.get("email"),
                "city": address.get("city"),
                "address": address.get("text"),
                "total_sum": total_sum,
                "items_count": items_count,
                "utm_source": utm_source,
                "raw": order,
            }
        )

    for batch_start in range(0, len(records), batch_size):
        batch_records = records[batch_start : batch_start + batch_size]
        try:
            supabase_resp = requests.post(
                supabase_url,
                headers=headers_supabase,
                json=batch_records,
                timeout=60,
            )

            print(page)
            print(len(batch_records))
            print(supabase_resp.status_code)
            print(supabase_resp.text)

            if supabase_resp.status_code < 400:
                processed_total += len(batch_records)
                uploaded_total += len(batch_records)
                time.sleep(1)
        except Exception as e:
            print("SUPABASE BATCH ERROR")
            print(page)
            print(len(batch_records))
            print(str(e))

    page += 1

print(processed_total)
print(uploaded_total)
