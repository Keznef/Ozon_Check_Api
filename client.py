import os
import sys
import json
import requests

def _load_config() -> dict:
    base_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    cfg_path = os.path.join(base_dir, "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_CFG = _load_config()
SERVER_URL = _CFG.get("SERVER_URL") or os.getenv("SERVER_URL", "http://127.0.0.1:8040")
API_KEY = _CFG.get("API_KEY") or os.getenv("API_KEY", "demo_key_123")
TIMEOUT = float(_CFG.get("TIMEOUT") or os.getenv("TIMEOUT", "8.0"))

STATUS_FATAL = {"invalid_key", "blocked", "disabled", "expired", "limit_exceeded"}

def main() -> int:
    url = f"{SERVER_URL.rstrip('/')}/api/check-key"
    try:
        r = requests.post(url, json={"api_key": API_KEY}, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        print("Сервер не отвечает")
        return 1

    if r.status_code != 200:
        print("Сервер не отвечает")
        return 1

    data = r.json()
    status = data.get("status")
    msg = data.get("message")

    if status == "ok":
        if msg:
            print(msg)
        print("Доступ разрешён")
        return 0

    if status in STATUS_FATAL:
        if status == "expired":
            print("Срок действия закончился")
        elif status == "invalid_key":
            print("Неверный ключ")
        elif status == "limit_exceeded":
            print("Лимит запросов исчерпан")
        elif status == "blocked":
            print("Ключ заблокирован")
        elif status == "disabled":
            print("Ключ отключён")
        else:
            print("Доступ запрещён")
        return 1

    if status == "maintenance":
        print("Сервис недоступен: обслуживание")
        return 1

    print("Неизвестный ответ сервера")
    return 1

if __name__ == "__main__":
    sys.exit(main())
