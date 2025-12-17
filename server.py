from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="License Server", version="0.1.0")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "config"
CLIENTS_FILE = DATA_DIR / "clients.json"
MAINTENANCE_FILE = DATA_DIR / "maintenance_state.json"

DATA_DIR.mkdir(exist_ok=True)

def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _now_ts() -> int:
    return int(time.time())

class CheckRequest(BaseModel):
    api_key: str

class CheckResponse(BaseModel):
    status: str  # ok | invalid_key | blocked | disabled | expired | limit_exceeded | maintenance
    message: Optional[str] = None
    client_name: Optional[str] = None
    remaining_requests: Optional[int] = None
    days_left: Optional[int] = None
    active: Optional[bool] = None

def _is_maintenance() -> bool:
    env_flag = os.getenv("MAINTENANCE", "false").strip().lower() in {"1","true","yes","on"}
    file_state = _read_json(MAINTENANCE_FILE) or {}
    file_flag = bool(file_state.get("active", False))
    return env_flag or file_flag

def _find_client(clients: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
    for c in clients.get("clients", []):
        if c.get("api_key") == api_key:
            return c
    return None

def _days_left(expires_at: Optional[int]) -> Optional[int]:
    if not expires_at:
        return None
    now = _now_ts()
    diff = expires_at - now
    if diff < 0:
        return 0
    return int(diff // 86400)

@app.post("/api/check-key", response_model=CheckResponse)
def check_key(payload: CheckRequest):
    if _is_maintenance():
        return CheckResponse(status="maintenance", message="Сервис временно недоступен (режим обслуживания)", active=False)

    clients = _read_json(CLIENTS_FILE) or {"clients": []}
    client = _find_client(clients, payload.api_key)
    if not client:
        return CheckResponse(status="invalid_key", message="Ключ не найден", active=False)

    if client.get("blocked"):
        return CheckResponse(status="blocked", message="Ключ заблокирован", active=False)
    if not client.get("active", True):
        return CheckResponse(status="disabled", message="Ключ отключён", active=False)

    expires_at = client.get("expires_at")
    days = _days_left(expires_at)
    if expires_at and _now_ts() > expires_at:
        return CheckResponse(status="expired", message="Срок действия подписки закончился", active=False)

    monthly_limit = int(client.get("monthly_limit", 0))
    used = int(client.get("used", 0))
    if monthly_limit and used >= monthly_limit:
        return CheckResponse(status="limit_exceeded", message="Лимит запросов за месяц исчерпан", active=False, remaining_requests=0, days_left=days, client_name=client.get("name"))

    client["used"] = used + 1
    _write_json(CLIENTS_FILE, clients)

    remaining = monthly_limit - client["used"] if monthly_limit else None
    msg = None
    reminders = []
    if days is not None:
        if days <= 3:
            reminders.append(f"Ваш ключ истекает через {days} дн.")
        elif days == 0:
            reminders.append("Срок действия подписки истекает сегодня")
    if remaining is not None:
        if remaining <= 100:
            reminders.append(f"У вас осталось {remaining} запросов")
        elif remaining <= 0:
            reminders.append("Лимит запросов исчерпан")
    if reminders:
        msg = " | ".join(reminders)

    return CheckResponse(
        status="ok",
        message=msg,
        client_name=client.get("name"),
        remaining_requests=remaining,
        days_left=days,
        active=True,
    )

@app.post("/api/maintenance/enable")
def enable_maintenance():
    _write_json(MAINTENANCE_FILE, {"active": True})
    return {"status": "ok", "maintenance": True}

@app.post("/api/maintenance/disable")
def disable_maintenance():
    _write_json(MAINTENANCE_FILE, {"active": False})
    return {"status": "ok", "maintenance": False}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("API_PORT", "9000")))
    uvicorn.run(app, host="0.0.0.0", port=port)
