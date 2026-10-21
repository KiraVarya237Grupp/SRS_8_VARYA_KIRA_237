# Архитектура системы и структура проекта

## 1. Структура каталогов и файлов проекта

```text
project_root/
├── manage.py               # Точка входа CLI для управления Django-проектом
├── requirements.txt        # Список зафиксированных зависимостей Python
├── .env.example            # Шаблон переменных окружения без секретных данных
├── README.md               # Основное руководство и быстрый старт
├── docs/                   # Комплект технической документации (СРС №8)
│   ├── architecture.md     # Описание архитектуры и структуры
│   ├── database.md         # Схема моделей БД и бизнес-правил
│   ├── api.md              # Документация маршрутов REST API
│   ├── deployment.md       # Руководство по развёртыванию в облаке Render
│   └── troubleshooting.md  # Диагностика и решение типовых проблем
└── catalog/                # Основное приложение «МедиаТрекер»
    ├── models.py           # Модели БД: Genre, FormatInstance, Title, WatchEntry, EntryEvent
    ├── admin.py            # Настройка таблиц, фильтров и колонок в Django Admin
    ├── views.py            # Контроллеры UI, REST API эндпоинты и транзакционная логика
    ├── serializers.py      # Сериализаторы данных для REST API
    ├── urls.py             # Маршруты каталога и API-операций
    ├── templates/          # HTML-шаблоны пользовательского интерфейса (catalog.html)
    └── migrations/         # Файлы миграций схемы базы данных
```

## 2. Архитектурная схема и границы взаимодействия

```mermaid
graph LR
    subgraph Клиентский контур
        Browser[Браузер пользователя<br/>HTML / CSS / JS Fetch]
    end

    subgraph Серверный контур
        WSGI[WSGI-сервер Gunicorn /<br/>Django Dev Server]
        Static[WhiteNoise<br/>Статические файлы CSS/JS]
        
        subgraph Приложение Django catalog
            UI[Django Views & Templates<br/>Рендеринг интерфейса]
            API[REST API Контроллеры<br/>Контроль прав, WIP, Транзакции]
            ORM[Django ORM<br/>Модели и Валидация]
        end
    end

    subgraph Хранение данных
        DB[(СУБД SQLite3 /<br/>PostgreSQL)]
    end

    Browser -- "1. GET /catalog/ (Загрузка UI)" --> WSGI
    WSGI -- "2. Отдача CSS/JS/Постеров" --> Static
    WSGI -- "3. Запрос страницы" --> UI
    Browser -- "4. Fetch/XHR (GET, POST, PATCH)<br/>+ CSRF Token & Session Cookie" --> API
    UI --> ORM
    API -- "atomic() транзакции" --> ORM
    ORM -- "SQL-запросы" --> DB
```