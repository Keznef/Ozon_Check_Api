# License Server (FastAPI)

Минимальный сервис на FastAPI для проверки API-ключей EXE клиента: проверяет месячные лимиты, срок действия, ручную блокировку и режим обслуживания.

## Эндпоинты
- `POST /api/check-key`: валидирует ключ, увеличивает счётчик, возвращает статус и уведомления.
- `POST /api/maintenance/enable` / `POST /api/maintenance/disable`: включает/выключает режим обслуживания.
- `GET /health`: проверка работоспособности.

## Конфиг
- `config/clients.json`: список клиентов.
- `config/maintenance_state.json`: `{ "active": true|false }`.

### Схема `clients.json`
```json
{
  "clients": [
    {
      "api_key": "string",
      "name": "string",
      "monthly_limit": 1000,
      "used": 0,
      "expires_at": 1735689600,
      "active": true,
      "blocked": false
    }
  ]
}
```
- `expires_at` — Unix timestamp (секунды).

## Локальный запуск
```powershell
$env:PORT="8040"; python SERVER.PY
```
Проверка:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8040/api/check-key" -Method Post -ContentType "application/json" -Body (@{ api_key = "demo_key_123" } | ConvertTo-Json)
```

## Деплой на Render
- Создайте Web Service из репозитория GitHub.
- Runtime: Python 3.x
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn SERVER:app --host 0.0.0.0 --port $PORT`
- Env var: опционально `MAINTENANCE=1` для включения обслуживания.

## Замечания
- Сервер пишет использование обратно в `config/clients.json`. Для конкуретных записей (прод) лучше использовать БД (например, PostgreSQL).
