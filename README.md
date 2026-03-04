# MyShop (Django)

Интернет‑магазин на **Django 6** с **PostgreSQL**, **Redis**, **Celery**, **Gunicorn** и **Nginx**.

## Структура проекта
- `shop/` — настройки Django, urls, wsgi
- `catalog/` — каталог товаров, категории, варианты, скидки, форма контактов
- `cart/` — корзина (сессии)
- `orders/` — оформление заказов (3 шага), история заказов
- `users/` — аутентификация, регистрация, профиль, сброс пароля
- `templates/` — HTML-шаблоны

## Что внутри
- **Каталог**: категории, товары, варианты товара, изображения (оптимизация при сохранении).
- **Корзина**: сессии + UI.
- **Заказы**: оформление (3 шага) + история заказов + детальная страница заказа.
- **Админка**: заказы и позиции заказа с inline‑позициями.
- **Статика**:
  - Bootstrap хранится **локально** в `static/vendor/bootstrap/`
  - WhiteNoise включён, чтобы `/static/` работал даже если заходить на `:8000` напрямую

## Требования
- **Python 3.12+**
- **Poetry**
- **Docker + Docker Compose** (рекомендуемый способ запуска)

## Быстрый старт (Docker — рекомендовано)
1) Создайте `.env` из примера:

```bash
# Linux/macOS
cp env.example .env
```

```powershell
# Windows PowerShell
copy env.example .env
```

2) Отредактируйте `.env` и **обязательно** задайте:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS` (например `127.0.0.1,localhost`)

3) Поднимите проект:

```bash
docker compose up -d --build
```

4) Откройте:
- **Сайт (через Nginx)**: `http://localhost/`
- **Админка**: `http://localhost/admin/`

> Можно открыть и `http://localhost:8000/` (напрямую Gunicorn) — статика тоже будет работать благодаря WhiteNoise, но в проде обычно ходят через Nginx.

## Локальный запуск (Poetry + Docker для инфраструктуры)
Подходит, если хочешь дебажить `runserver`, но БД/Redis держать в Docker.

1) Установить зависимости:

```bash
poetry install
```

2) Поднять Postgres+Redis:

```bash
docker compose up -d postgres redis
```

3) Прогнать миграции и статику:

```bash
poetry run python manage.py migrate
poetry run python manage.py collectstatic --noinput
```

4) Запустить Django:

```bash
poetry run python manage.py runserver
```

## Переменные окружения (`.env`)
Минимально для запуска:
- `DJANGO_SECRET_KEY` — секретный ключ (обязательно)
- `DJANGO_ALLOWED_HOSTS` — хосты через запятую (например `127.0.0.1,localhost`)
- `DJANGO_DEBUG` — `True` или `False`

Полный список — смотри `env.example`. Основные:
- **Django**
  - `DJANGO_SECRET_KEY`
  - `DJANGO_DEBUG` (`True`/`False`)
  - `DJANGO_ALLOWED_HOSTS` (через запятую)
  - `DJANGO_CSRF_TRUSTED_ORIGINS` (для https/домена в проде)
- **PostgreSQL**
  - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- **Redis / Celery**
  - `REDIS_URL`
  - `DJANGO_USE_REDIS_CACHE` — `False` для fallback на LocMemCache (если Redis недоступен)
  - `CELERY_BROKER_URL`
  - `CELERY_RESULT_BACKEND`
  - `CELERY_TASK_DEFAULT_QUEUE`
- **Email**
  - `EMAIL_BACKEND`
  - `DEFAULT_FROM_EMAIL`

## Создать суперпользователя

```bash
docker compose exec web python manage.py createsuperuser
```

или локально:

```bash
poetry run python manage.py createsuperuser
```

## Заказы в админке
В админке доступны:
- **Orders → Orders** (заказы)
- **Orders → Order items** (позиции заказа)

В карточке заказа позиции отображаются inline.

## Тестовые данные (сидинг каталога)
Есть management command для наполнения каталога:

```bash
docker compose exec web python manage.py seed_products
```

## Проверка Celery

```bash
docker compose exec web python manage.py shell
```

```python
from catalog.tasks import ping
ping.delay().get(timeout=10)
```

Ожидаемый результат: `pong`.

## Статика и Nginx
- `STATIC_ROOT = staticfiles/` (результат `collectstatic`)
- Nginx раздаёт:
  - `/static/` из `./staticfiles`
  - `/media/` из `./media`

Конфиг: `nginx/conf.d/default.conf`

## Troubleshooting
### В админке/на сайте нет стилей
- Открывай сайт через `http://localhost/` (Nginx).
- Если заходишь на `http://localhost:8000/`, статика отдаётся WhiteNoise (встроено), но **после изменений** нужно пересобрать контейнер:

```bash
docker compose up -d --build
```

### `/static/admin/...` отдаёт 404
Проверь:
- `docker compose logs --tail 200 nginx`
- что `collectstatic` отработал (в логах `web` будет `post-processed`)
