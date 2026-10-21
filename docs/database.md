# Схема базы данных и описание моделей

## 1. ER-диаграмма сущностей проекта

```mermaid
erDiagram
    User ||--o{ WatchEntry : "owner"
    User ||--o{ EntryEvent : "initiator"
    Genre }o--o{ Title : "M2M"
    FormatInstance }o--o{ Title : "M2M"
    FormatInstance ||--o{ WatchEntry : "format_used"
    Title ||--o{ WatchEntry : "entries"
    WatchEntry ||--o{ EntryEvent : "events"

    Genre {
        int id PK
        string name "Название жанра"
    }

    FormatInstance {
        int id PK
        string name "Тип носителя"
        boolean is_available "Доступно на полке"
    }

    Title {
        int id PK
        string title "Название произведения"
        string kind "movie | series | book | game"
        image poster "Обложка/Постер"
    }

    WatchEntry {
        int id PK
        int title_id FK "Произведение"
        int owner_id FK "Владелец записи"
        int format_used_id FK "Используемый носитель"
        string status "planned | in_progress | completed"
        int rating "Оценка (1-10)"
        text notes "Личные заметки"
        datetime created_at "Дата добавления"
    }

    EntryEvent {
        int id PK
        int entry_id FK "Связанная запись"
        int initiator_id FK "Инициатор"
        string event_type "created | status_changed | updated"
        string description "Описание изменения"
        datetime timestamp "Дата и время"
    }
```

## 2. Описание моделей и правил целостности

| Модель | Назначение | Ключевые поля и связи | Бизнес-правила |
| :--- | :--- | :--- | :--- |
| **`Genre`** | Справочник жанров | `name` (CharField, 100) | Связь `ManyToMany` с моделью `Title` для классификации произведений. |
| **`FormatInstance`** | Формат / носитель в личной коллекции | `name` (Бумажная, Цифровая и т.д.), `is_available` (Boolean) | Отражает наличие и статус формата на полке (`Доступно` / `Используется`). |
| **`Title`** | Карточка произведения | `title`, `kind` (фильм/сериал/книга/игра), `genres` (M2M), `formats` (M2M), `poster` | Базовая сущность каталога медиаконтента. |
| **`WatchEntry`** | Запись в личной библиотеке | `title` (FK), `owner` (FK), `format_used` (FK), `status`, `rating` (1-10), `notes`, `created_at` | Контролирует допустимые переходы статуса через словарь `ALLOWED_TRANSITIONS` (`planned` -> `in_progress` -> `completed`). |
| **`EntryEvent`** | Журнал истории личной библиотеки | `entry` (FK), `initiator` (FK), `event_type`, `description`, `timestamp` | Создаётся автоматически в рамках единой транзакции при добавлении записи, смене статуса или обновлении оценки/заметок. |