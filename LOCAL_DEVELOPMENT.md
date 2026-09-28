# Локальный запуск без Telegram

Dev-вход автоматически авторизует браузер под пользователем из локальной БД.
Telegram-бот и `initData` для этого режима не нужны.

## 1. Backend

Используйте Python-окружение с зависимостями из `backend/requirements.txt`:

```bash
python -m pip install -r backend/requirements.txt
```

В корневом `.env` должны быть настройки локальной PostgreSQL и остальные
параметры из `env_template`. Добавьте или измените:

```dotenv
APP_ENV=development
DEV_AUTH_ENABLED=true
```

Если база новая, сначала примените миграции из каталога `backend/`:

```bash
alembic upgrade head
```

Из корня проекта создайте dev-пользователя:

```bash
PYTHONPATH=.. python -m lit_club_app.backend.dev_user
```

Команда создаёт активного администратора `dev_admin` без привязки к Telegram
и печатает `DEV_AUTH_USER_ID=...`. Добавьте эту строку в корневой `.env`.
Повторный запуск возвращает тот же аккаунт; конфликтующий аккаунт не изменяется.
ID зависит от базы: используйте значение, напечатанное командой.

Запустите API из корня проекта:

```bash
PYTHONPATH=.. uvicorn lit_club_app.backend.main:app --reload --host 127.0.0.1 --port 8001
```

## 2. Frontend

В `frontend/.env.local`:

```dotenv
VITE_API_URL=/api
VITE_DEV_AUTH=true
```

Из каталога `frontend/`:

```bash
npm ci
npm run dev
```

Откройте http://localhost:5173 в обычном браузере. Вход под `dev_admin`
произойдёт автоматически. Существующий Vite-прокси направляет `/api` на
`http://127.0.0.1:8001`.

После изменения env-файлов перезапустите соответствующие процессы.

## Проверка других ролей и отключение режима

Чтобы войти под другим локальным аккаунтом, измените `DEV_AUTH_USER_ID` на его ID
и перезапустите backend. Права берутся из БД; dev-вход не повышает роль аккаунта.
Неактивные пользователи не допускаются, удаление/деактивация аккаунта прекращает
доступ и по уже выданному токену.

Чтобы вернуться к Telegram-входу, установите `DEV_AUTH_ENABLED=false` на backend
и `VITE_DEV_AUTH=false` на frontend, затем перезапустите оба процесса.

В production используйте `APP_ENV=production` и `DEV_AUTH_ENABLED=false`.
Backend отказывается запускаться с включённым dev-входом вне development.
Dev-endpoint возвращает 404 при выключенном режиме, dev-токены также отвергаются.
Во frontend dev-вход работает только на dev-сервере Vite, не в production-сборке.

## Проверки

Из корня проекта:

```bash
PYTHONPATH=.. python -m pytest backend/tests/test_dev_auth.py backend/tests/test_telegram_auth.py
```

Из `frontend/`:

```bash
node --test auth.test.mjs
npm run build
npm run lint
```
