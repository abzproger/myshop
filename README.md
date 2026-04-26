# SofaArt

Интернет-магазин на **Django 6** с каталогом, корзиной на сессиях, многошаговым оформлением заказа, личным кабинетом и базовой фоновой инфраструктурой на **Celery**. Проект готовится к развертыванию на **VPS** через **Docker Compose**, **Gunicorn** и **Nginx**.

## Что есть в проекте

- `catalog` — каталог, карточки товаров, варианты, изображения, скидки, API
- `cart` — корзина на сессиях
- `orders` — оформление заказа и история заказов
- `users` — регистрация, вход, профиль, восстановление пароля
- `shop` — настройки Django, SEO-инфраструктура, корневые URL, WSGI/Celery
- `nginx/` — конфигурация reverse proxy

## SEO и индексация

Проект подготовлен под основной домен `https://sofaart.ru` и географию России.

Что реализовано:

- глобальные `meta description`, `robots`, `canonical`, Open Graph и Twitter Card
- schema.org JSON-LD: `Organization`, `WebSite`, `Product`, `Offer`, `BreadcrumbList`, `FurnitureStore`, `FAQPage`
- `GET /robots.txt` с правилами индексации и ссылкой на sitemap
- `GET /sitemap.xml` для главной, каталога, категорий, товаров и статичных страниц
- `noindex, nofollow` для корзины, заказов, профиля, входа и страниц восстановления пароля
- `noindex, follow` для поисковых/сортировочных URL каталога, чтобы не плодить дубли
- canonical для товаров без query-параметра `?variant=`
- единый бренд `SofaArt` в шаблонах, письмах, админке и настройках

После деплоя проверьте:

- `https://sofaart.ru/robots.txt`
- `https://sofaart.ru/sitemap.xml`
- canonical и JSON-LD на страницах товара

## Технологии

- Python 3.12
- Django 6
- PostgreSQL
- Redis
- Celery
- Gunicorn
- Nginx
- Jazzmin
- Docker / Docker Compose
- Poetry

## Архитектура деплоя

На VPS стек запускается так:

1. `postgres` хранит данные проекта.
2. `redis` используется для кеша и Celery.
3. `web` запускает Django через Gunicorn.
4. `nginx` принимает HTTP-запросы, отдает статику/медиа и проксирует приложение.
5. `celery-worker` выполняет фоновые задачи.
6. `celery-beat` запускает периодические задачи.

Важно:

- основной внешний вход в приложение — через `nginx` на порту `80`
- Gunicorn на `8000`, PostgreSQL на `5432` и Redis на `6379` проброшены только на `127.0.0.1`, то есть доступны только с самого сервера
- `web` контейнер использует `shop.settings.prod`, чтобы `migrate`, `collectstatic` и сам Gunicorn работали в одной конфигурации

## Быстрый старт через Docker

### 1. Подготовьте `.env`

Скопируйте шаблон:

```bash
cp env.example .env
```

Для PowerShell:

```powershell
copy env.example .env
```

Минимально обязательно проверьте:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_URL`
- `POSTGRES_PASSWORD`
- `EMAIL_*`, если используете SMTP

### 2. Запустите стек

```bash
docker compose up -d --build
```

После первого запуска будут автоматически выполнены:

- `python manage.py migrate`
- `python manage.py collectstatic --noinput`
- запуск Gunicorn

### 3. Откройте сайт

- сайт: [http://localhost/](http://localhost/)
- админка: [http://localhost/admin/](http://localhost/admin/)
- healthcheck: [http://localhost/healthz/](http://localhost/healthz/)

## Локальная разработка

Если вы хотите запускать Django локально через `runserver`, а PostgreSQL и Redis оставить в Docker:

```bash
poetry install
cp env.example .env
docker compose up -d postgres redis
poetry run python manage.py migrate
poetry run python manage.py runserver
```

По умолчанию `manage.py` использует `shop.settings`, а это алиас на `shop.settings.local`.

Это нормально для локальной разработки. В Docker-контейнерах для деплоя используется `shop.settings.prod`.

## Переменные окружения

Основные настройки собраны в `env.example`.

### Django

- `DJANGO_SECRET_KEY` — секретный ключ Django
- `DJANGO_DEBUG` — режим отладки
- `DJANGO_ALLOWED_HOSTS` — список доменов / IP через запятую
- `DJANGO_CSRF_TRUSTED_ORIGINS` — trusted origins для форм и админки
- `SITE_NAME` — публичное название сайта, по умолчанию `SofaArt`
- `SITE_URL` — основной production URL для canonical, sitemap и schema.org, по умолчанию `https://sofaart.ru`
- `SITE_DESCRIPTION` — описание сайта для базового meta description
- `SITE_DEFAULT_IMAGE` — изображение по умолчанию для Open Graph / Twitter Card

### Безопасность и HTTPS

Эти флаги особенно важны на VPS:

- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`

По умолчанию в шаблоне они выключены, чтобы сайт не ломался на HTTP-only сервере.

Когда на VPS будет настроен HTTPS, рекомендуется:

```env
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=False
```

### База данных и Redis

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `REDIS_URL`
- `DJANGO_USE_REDIS_CACHE`

### Celery

- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CELERY_TASK_DEFAULT_QUEUE`

### Gunicorn и запуск контейнера

- `PORT`
- `GUNICORN_WORKERS`
- `GUNICORN_TIMEOUT`
- `DJANGO_RUN_MIGRATIONS`
- `DJANGO_COLLECTSTATIC`

По умолчанию web-контейнер запускается через `entrypoint.sh`, который:

1. применяет миграции
2. собирает статику
3. запускает Gunicorn

Если позже вы захотите масштабировать несколько `web` контейнеров, лучше вынести миграции в отдельный ручной шаг, а `DJANGO_RUN_MIGRATIONS` отключить.

## Развертывание на VPS

Ниже безопасный базовый сценарий для одного сервера.

### 1. Подготовка сервера

Установите:

- Docker Engine
- Docker Compose plugin
- Git

Проверьте, что открыты нужные порты:

- `80` — HTTP
- `443` — если будете подключать HTTPS

### 2. Клонируйте проект

```bash
git clone <your-repo-url> myshop
cd myshop
```

### 3. Создайте production `.env`

Пример минимального набора:

```env
DJANGO_SECRET_KEY=replace-with-a-real-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=sofaart.ru,www.sofaart.ru,server-ip
DJANGO_CSRF_TRUSTED_ORIGINS=https://sofaart.ru,https://www.sofaart.ru
SITE_NAME=SofaArt
SITE_URL=https://sofaart.ru
SITE_DESCRIPTION=SofaArt — интернет-магазин качественной мебели для дома и офиса с доставкой по России.

POSTGRES_DB=myshop
POSTGRES_USER=myshop
POSTGRES_PASSWORD=very-strong-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/1
DJANGO_USE_REDIS_CACHE=True

CELERY_BROKER_URL=redis://redis:6379/2
CELERY_RESULT_BACKEND=redis://redis:6379/3
CELERY_TASK_DEFAULT_QUEUE=default

PORT=8000
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=60
DJANGO_RUN_MIGRATIONS=1
DJANGO_COLLECTSTATIC=1
```

Если домен и HTTPS еще не настроены, временно оставьте:

```env
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_SSL_REDIRECT=False
```

После настройки HTTPS включите их обратно в `True`.

### 4. Поднимите контейнеры

```bash
docker compose up -d --build
```

### 5. Проверьте состояние

```bash
docker compose ps
docker compose logs --tail 200 web
docker compose logs --tail 200 nginx
docker compose logs --tail 200 celery-worker
```

Проверьте:

- главную страницу
- `/admin/`
- `/healthz/`
- `/robots.txt`
- `/sitemap.xml`
- загрузку статики
- загрузку карточек товаров

### 6. Создайте суперпользователя

```bash
docker compose exec web python manage.py createsuperuser
```

## Nginx

Конфиг находится в `nginx/conf.d/default.conf`.

Что он делает:

- принимает трафик на `80`
- проксирует запросы в `web:8000`
- отдает `/static/` из `./staticfiles`
- отдает `/media/` из `./media`

Сейчас конфигурация рассчитана на базовый reverse proxy без TLS.

Если вы будете ставить HTTPS через Certbot, внешний TLS можно завершать:

- либо на самом Nginx в этом проекте
- либо на внешнем reverse proxy перед контейнерами

После включения HTTPS не забудьте обновить `.env`:

- `DJANGO_CSRF_TRUSTED_ORIGINS=https://...`
- `DJANGO_SESSION_COOKIE_SECURE=True`
- `DJANGO_CSRF_COOKIE_SECURE=True`
- `DJANGO_SECURE_SSL_REDIRECT=True`

## Статика и медиа

- `static/` — исходные статические файлы проекта
- `staticfiles/` — результат `collectstatic`
- `media/` — пользовательские загрузки

`staticfiles/` и `media/` не должны коммититься в репозиторий.

Nginx читает их напрямую с хоста:

- `./staticfiles -> /static`
- `./media -> /media`

## Администрирование и полезные команды

Админка оформлена через `Jazzmin` и дополнительно подправлена минималистичными локальными стилями из `static/css/admin-custom.css`.

### Перезапуск стека

```bash
docker compose up -d
```

### Полная пересборка

```bash
docker compose up -d --build
```

### Остановка

```bash
docker compose down
```

### Остановка с удалением томов БД/Redis

Осторожно: команда удалит данные PostgreSQL и Redis.

```bash
docker compose down -v
```

### Применить миграции вручную

```bash
docker compose exec web python manage.py migrate
```

### Собрать статику вручную

```bash
docker compose exec web python manage.py collectstatic --noinput
```

### Наполнить каталог тестовыми данными

```bash
docker compose exec web python manage.py seed_products
```

### Проверка Celery

```bash
docker compose exec web python manage.py shell
```

```python
from catalog.tasks import ping
ping.delay().get(timeout=10)
```

Ожидаемый ответ: `"pong"`.

## Healthcheck

Добавлен endpoint `GET /healthz/`.

Он используется:

- для проверки доступности Django
- для healthcheck контейнера `web`

Если база недоступна, endpoint вернет `503`.

## SEO-проверки

После изменения шаблонов, URL или настроек домена полезно проверить:

```bash
poetry run python manage.py check
poetry run python manage.py test shop
```

Локально можно быстро убедиться, что SEO endpoints подключены:

```bash
poetry run python manage.py shell -c "from django.test import Client; c=Client(HTTP_HOST='localhost'); print(c.get('/robots.txt').status_code); print(c.get('/sitemap.xml').status_code)"
```

В production дополнительно проверьте:

- `robots.txt` содержит `Sitemap: https://sofaart.ru/sitemap.xml`
- страницы корзины, заказов и профиля отдают `noindex, nofollow`
- страницы каталога с `?search=`, `?sort=` и `?variant=` не становятся отдельными canonical URL
- карточка товара содержит `Product` / `Offer` JSON-LD с актуальной ценой и наличием

## Отладка проблем

### Сайт не открывается

Проверьте:

```bash
docker compose ps
docker compose logs --tail 200 nginx
docker compose logs --tail 200 web
```

### Нет стилей или 404 на `/static/...`

Проверьте:

```bash
docker compose exec web python manage.py collectstatic --noinput
docker compose logs --tail 200 nginx
```

### Не работает логин / формы на VPS

Чаще всего причина в одном из пунктов:

- неверный `DJANGO_ALLOWED_HOSTS`
- не настроен `DJANGO_CSRF_TRUSTED_ORIGINS`
- включены secure-cookie / SSL redirect флаги, но HTTPS еще не поднят

### Не запускается `web`

Проверьте:

- корректность `.env`
- доступность `postgres`
- доступность `redis`
- логи:

```bash
docker compose logs --tail 200 web
```

## Тесты

```bash
poetry run python manage.py test
```

или в контейнере:

```bash
docker compose exec web python manage.py test
```

## Что еще можно улучшить

Проект уже пригоден для базового VPS-деплоя, но дальше я бы рекомендовал:

- добавить HTTPS-конфиг для Nginx и сценарий с Certbot
- добавить сайт в Яндекс Вебмастер и Google Search Console после деплоя
- отправить `https://sofaart.ru/sitemap.xml` в панели вебмастеров
- вынести секреты из `.env` в менеджер секретов или хотя бы в защищенное хранилище VPS
- добавить отдельный backup-процесс для PostgreSQL
- разделить dev/prod compose-конфигурации, если проект будет активно развиваться
- добавить мониторинг и алерты по ошибкам
- при масштабировании вынести миграции из startup-скрипта в отдельный deploy step
