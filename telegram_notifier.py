import json
import os
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


def load_sent_ids(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return set()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Ошибка чтения sent_order_ids.json:", str(e))
        data = []

    if not isinstance(data, list):
        print("sent_order_ids.json поврежден, будет сброшен")
        data = []

    return {str(value) for value in data}


def save_sent_ids(path, sent_ids):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(sent_ids), f, ensure_ascii=False, indent=2)


def parse_total(order):
    value = order.get("totalSumm")
    if value is None:
        value = order.get("summ")

    try:
        return float(value)
    except Exception:
        return None


def send_telegram_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": text},
            timeout=30,
        )
    except Exception as e:
        print("Ошибка отправки в Telegram:", str(e))
        return False

    if response.status_code >= 400:
        print("Telegram API error:", response.status_code, response.text)
        return False

    return True


def check_orders(env, sent_ids, storage_path):
    retailcrm_url = env["RETAILCRM_URL"].rstrip("/") + "/api/v5/orders"
    retailcrm_api_key = env["RETAILCRM_API_KEY"]
    retailcrm_site = env["RETAILCRM_SITE"]
    telegram_bot_token = env["TELEGRAM_BOT_TOKEN"]
    telegram_chat_id = env["TELEGRAM_CHAT_ID"]

    try:
        response = requests.get(
            retailcrm_url,
            headers={"X-API-KEY": retailcrm_api_key},
            params={"site": retailcrm_site, "limit": 20, "page": 1},
            timeout=30,
        )
    except Exception as e:
        print("Ошибка запроса в RetailCRM:", str(e))
        return

    if response.status_code >= 400:
        print("RetailCRM API error:", response.status_code, response.text)
        return

    try:
        payload = response.json()
    except Exception:
        print("Ошибка парсинга ответа RetailCRM:", response.text)
        return

    orders = payload.get("orders") or payload.get("data") or []

    for order in orders:
        order_id = order.get("id")
        if order_id is None:
            continue

        total = parse_total(order)
        if total is None or total <= 50000:
            continue

        order_id_key = str(order_id)
        if order_id_key in sent_ids:
            continue

        number = order.get("number")
        created_at = order.get("createdAt")
        first_name = order.get("firstName") or ""
        last_name = order.get("lastName") or ""
        phone = order.get("phone")
        client = (first_name + " " + last_name).strip() or "-"

        message = (
            "Новый заказ больше 50000\n"
            f"ID: {order_id}\n"
            f"Номер: {number}\n"
            f"Сумма: {total}\n"
            f"Клиент: {client}\n"
            f"Телефон: {phone}\n"
            f"Создан: {created_at}"
        )

        sent = send_telegram_message(telegram_bot_token, telegram_chat_id, message)
        if sent:
            sent_ids.add(order_id_key)
            try:
                save_sent_ids(storage_path, sent_ids)
                print("Отправлено уведомление по заказу:", order_id)
            except Exception as e:
                print("Ошибка сохранения sent_order_ids.json:", str(e))


def main():
    try:
        env = read_env(".env")
    except Exception as e:
        print("Ошибка чтения .env:", str(e))
        return

    required_keys = [
        "RETAILCRM_URL",
        "RETAILCRM_API_KEY",
        "RETAILCRM_SITE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    missing = [key for key in required_keys if not env.get(key)]
    if missing:
        print("Не хватает переменных в .env:", ", ".join(missing))
        return

    storage_path = "sent_order_ids.json"
    sent_ids = load_sent_ids(storage_path)

    while True:
        try:
            check_orders(env, sent_ids, storage_path)
        except Exception as e:
            print("Неожиданная ошибка:", str(e))
        time.sleep(15)


if __name__ == "__main__":
    main()
