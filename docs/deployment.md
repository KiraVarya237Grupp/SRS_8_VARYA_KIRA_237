# Инструкция по облачному развёртыванию (Платформа Render)

Развёртывание выполняется на бесплатном тарифе (Free Tier) облачной платформы **Render** в связке `Web Service` + управляемая СУБД `Render PostgreSQL`.

## 1. Создание базы данных PostgreSQL

1. В панели управления Render нажмите **New + -> PostgreSQL**.
2. Укажите имя базы (например, `mediatracker-db`), регион и выберите бесплатный тарифный план **Free**.
3. После создания перейдите на страницу настроек БД и скопируйте значение **Internal Database URL** (формат `postgresql://user:pass@host:5432/dbname`).

> **Важно про Internal Database URL:**
> * **Когда используется:** применяется для подключения `Web Service` к базе данных `PostgreSQL`, когда оба сервиса размещены внутри одной внутренней сети Render.
> * **Безопасность:** в публичных инструкциях и репозитории запрещено публиковать фактическое значение `Internal Database URL`, так как оно содержит учётные данные доступа к БД.

> **Различие локальной и облачной БД:**
> Локальная база `SQLite` (`db.sqlite3`) и облачная `PostgreSQL` на Render не являются одной базой данных — локальные записи не переносятся в облако автоматически. В облачной СУБД таблицы создаются с нуля при выполнении миграций.

## 2. Настройка переменных окружения (Environment Variables)

При создании **Web Service** подключите GitHub-репозиторий проекта и в разделе **Environment** добавьте следующие переменные:

| Имя переменной | Назначение | Безопасный пример значения |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | Криптографическая подпись сессий и токенов Django | `django-insecure-prod-example-key-98765` |
| `DJANGO_DEBUG` | Управление режимом отладки (в продакшене строго выключен) | `False` |
| `DJANGO_ALLOWED_HOSTS` | Разрешённые доменные имена для заголовка `Host` | `mediatracker-app.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Доверенные домены с `https://` для прохождения CSRF-проверки в изменяющих запросах | `https://mediatracker-app.onrender.com` |
| `DATABASE_URL` | Строка подключения к облачной СУБД PostgreSQL | `postgresql://user:pass@dpg-xxxx:5432/dbname` *(Internal Database URL)* |

## 3. Разделение процессов: Сборка, Миграции, Запуск и Проверка

1. **Сборка и статика (Build Command):** установка зависимостей из `requirements.txt` и сборка статических файлов в каталог `STATIC_ROOT` (`staticfiles/`).
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput
   ```
2. **Миграции БД (Pre-Deploy / Build):** создание таблиц в PostgreSQL перед запуском приложения.
   ```bash
   python manage.py migrate --noinput
   ```
3. **Запуск сервера приложений (Start Command):** старт WSGI-сервера `Gunicorn`.
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```
4. **Проверка работоспособности:**
   * Дождаться статуса `Live` в панели Render.
   * Открыть страницу `/catalog/`, проверить загрузку стилей CSS.
   * Открыть вкладку `Network` (F12) и выполнить смену статуса карточки или тест кнопки «Сбой», убедившись в корректном ответе API и сохранении данных в PostgreSQL.