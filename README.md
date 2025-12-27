# myshop

Интернет-магазин на Django с PostgreSQL, Redis, Celery и Nginx.

## Требования
- Python 3.12
- Poetry
- Docker/Docker Compose (для Postgres/Redis/Nginx)

## Быстрый старт (локально)
1) Установите зависимости (пакетный режим Poetry отключён):
```bash
poetry install
```
2) Создайте файл `.env` на основе примера:
```bash
# Linux/macOS: cp env.example .env
# Windows PowerShell: copy env.example .env
# Не забудьте подставить DJANGO_SECRET_KEY
```
3) Поднимите инфраструктуру (БД, Redis):
```bash
docker-compose up -d postgres redis
```
4) Запустите Django + Celery + Nginx через Docker (зависимости ставятся на этапе build):
```bash
docker-compose up --build -d web celery-worker celery-beat nginx
```
Сайт будет доступен на `http://localhost/` (через Nginx). Для отладки напрямую Django также остаётся `http://localhost:8000/`.

## Переменные окружения (env.example)
- `DJANGO_SECRET_KEY` — секретный ключ Django (обязательно поменять)
- `DJANGO_DEBUG` — режим отладки (`True`/`False`)
- `DJANGO_ALLOWED_HOSTS` — через запятую, например `127.0.0.1,localhost`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` — параметры БД
- `REDIS_URL` — URL Redis (используется кэш)
- `CELERY_BROKER_URL` — брокер Celery (по умолчанию Redis, см. `env.example`)
- `CELERY_RESULT_BACKEND` — backend для результатов (по умолчанию Redis, см. `env.example`)
- `CELERY_TASK_DEFAULT_QUEUE` — дефолтная очередь задач
- `EMAIL_BACKEND` — backend отправки писем (по умолчанию консоль)
- `DEFAULT_FROM_EMAIL` — адрес отправителя по умолчанию

## SMTP через Gmail
Google больше не поддерживает “less secure apps”, поэтому самый простой вариант — **App Password**:
- Включите 2FA в аккаунте Google
- Создайте “App password” для почты
- Пропишите в `.env`:
  - `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
  - `EMAIL_HOST=smtp.gmail.com`
  - `EMAIL_PORT=587`
  - `EMAIL_USE_TLS=True`
  - `EMAIL_HOST_USER=ваш@gmail.com`
  - `EMAIL_HOST_PASSWORD=app_password`

## Проверка Celery
В Django shell (внутри контейнера `web`) выполните:
```bash
docker-compose exec web python manage.py shell
>>> from catalog.tasks import ping
>>> ping.delay().get(timeout=10)
```
Ожидаемый результат: `pong`.

## Полезные команды
- Создание суперпользователя: `poetry run python manage.py createsuperuser`
- Сбор статики (прод): `poetry run python manage.py collectstatic`

## Примечания
- Poetry настроен с `package-mode = false`, поэтому проект не устанавливается как пакет; используется для управления зависимостями.
- БД по умолчанию — PostgreSQL (см. переменные окружения в `env.example`).

## Nginx
Конфиг Nginx лежит в `nginx/conf.d/default.conf` и в docker-compose монтируется в контейнер `nginx`.
Он раздаёт:
- `/static/` из `./staticfiles` (результат `collectstatic`)
- `/media/` из `./media`
