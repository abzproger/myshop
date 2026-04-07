# MyShop

Интернет-магазин на **Django 6** с каталогом, корзиной на сессиях, многошаговым оформлением заказа и личным кабинетом. В инфраструктуре: **PostgreSQL**, **Redis**, **Celery**, **Gunicorn**, **Nginx**; статика отдаётся через **WhiteNoise** и Nginx.

## Возможности

| Область | Описание |
|--------|----------|
| Каталог | Категории (в т.ч. вложенные), товары, варианты, изображения, скидки, REST API |
| Корзина | Сессии, ограничение количества, AJAX-обновления |
| Заказы | Три шага оформления, история для авторизованных, гостевой просмотр по токену |
| Пользователи | Регистрация, вход, профиль, сброс пароля |
| Фоновые задачи | Celery (пример — задачи в `catalog/tasks.py`) |

## Структура репозитория

- `shop/` — настройки, корневой `urls.py`, WSGI/ASGI, Celery
- `catalog/` — витрина, форма контактов, API, management-команды
- `cart/` — логика корзины и представления
- `orders/` — заказы и чекаут
- `users/` — учётные записи
- `templates/`, `static/` — шаблоны и фронт (Bootstrap лежит в `static/vendor/bootstrap/`)

## Требования

- Python **3.12+**
- **Poetry** (зависимости в `pyproject.toml`)
- **Docker** и **Docker Compose** — рекомендуемый способ запуска всего стека

## Запуск в Docker

1. Скопируйте переменные окружения из примера:

   ```bash
   cp env.example .env
   ```

   В PowerShell:

   ```powershell
   copy env.example .env
   ```

2. В `.env` обязательно задайте как минимум:

   - `DJANGO_SECRET_KEY`
   - `DJANGO_ALLOWED_HOSTS` (например `127.0.0.1,localhost`)

3. Поднимите сервисы:

   ```bash
   docker compose up -d --build
   ```

4. Сайт через reverse proxy: **http://localhost/**  
   Админка: **http://localhost/admin/**  

   Прямой доступ к приложению на порту **8000** тоже возможен; статика подхватывается WhiteNoise. В продакшене обычно используют только Nginx.

## Локальная разработка (Poetry + БД/Redis в Docker)

Удобно для отладки с `runserver`, когда PostgreSQL и Redis крутятся в контейнерах.

```bash
poetry install
docker compose up -d postgres redis
poetry run python manage.py migrate
poetry run python manage.py collectstatic --noinput
poetry run python manage.py runserver
```

## Переменные окружения

Минимум для старта: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, при необходимости `DJANGO_DEBUG`.

Полный перечень с пояснениями — в **`env.example`**: база, Redis, кэш (`DJANGO_USE_REDIS_CACHE`), Celery, почта, CSRF и HTTPS для продакшена.

## Администрирование

Создать суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```

или локально:

```bash
poetry run python manage.py createsuperuser
```

В админке: заказы и позиции заказа (inline у заказа).

## Тестовые данные

Наполнение каталога:

```bash
docker compose exec web python manage.py seed_products
```

## Проверка Celery

```bash
docker compose exec web python manage.py shell
```

```python
from catalog.tasks import ping
ping.delay().get(timeout=10)  # ожидается "pong"
```

## Статика и медиа

- `STATIC_ROOT` → `staticfiles/` (после `collectstatic`)
- Nginx раздаёт `/static/` из `./staticfiles` и `/media/` из `./media`
- Конфигурация Nginx: `nginx/conf.d/default.conf`

## Если что-то не так

**Нет стилей в админке или на сайте**

- Зайдите через **http://localhost/** (Nginx).
- После изменений образа/статики может понадобиться пересборка: `docker compose up -d --build`.

**404 на `/static/admin/...`**

- Проверьте логи: `docker compose logs --tail 200 nginx` и логи сервиса `web`.
- Убедитесь, что `collectstatic` выполнялся успешно.

## Тесты

```bash
poetry run python manage.py test
```
