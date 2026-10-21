from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название жанра")

    def __str__(self):
        return self.name

class FormatInstance(models.Model):
    """Вторая связанная сущность: Формат / Носитель"""
    name = models.CharField(max_length=100, verbose_name="Тип формата (напр. Бумажная, Цифровая)")
    is_available = models.BooleanField(default=True, verbose_name="Доступно на полке")

    def __str__(self):
        status = "Доступно"[cite: 1] if self.is_available else "Используется"
        return f"{self.name} ({status})"

class Title(models.Model):
    KIND_CHOICES = [
        ('movie', 'Фильм'),
        ('series', 'Сериал'),
        ('book', 'Книга'),
        ('game', 'Игра'),
    ]
    title = models.CharField(max_length=200, verbose_name="Название")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='movie', verbose_name="Тип")
    genres = models.ManyToManyField(Genre, blank=True, verbose_name="Жанры")
    poster = models.ImageField(upload_to='posters/', blank=True, null=True, verbose_name="Постер/Обложка")
    # Связь с форматами носителей
    formats = models.ManyToManyField(FormatInstance, blank=True, verbose_name="Доступные форматы")

    def __str__(self):
        return self.title

class WatchEntry(models.Model):
    STATUS_CHOICES = [
        ('planned', 'В планах (Отложено)'),
        ('in_progress', 'Читаю / Смотрю сейчас'),
        ('completed', 'Прочитано / Завершено'),
    ]

    ALLOWED_TRANSITIONS = {
        'planned': ['in_progress'],
        'in_progress': ['completed'],
        'completed': [],
    }

    title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name='entries', verbose_name="Произведение")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_entries', null=True, blank=True, verbose_name="Владелец")
    format_used = models.ForeignKey(FormatInstance, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Используемый формат")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', verbose_name="Статус")
    rating = models.PositiveIntegerField(blank=True, null=True, verbose_name="Оценка (1-10)")
    notes = models.TextField(blank=True, null=True, verbose_name="Личные заметки")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Дата добавления")

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def __str__(self):
        return f"{self.title.title} ({self.get_status_display()})"

class EntryEvent(models.Model):
    """Журнал истории событий личной библиотеки"""
    EVENT_TYPES = [
        ('created', 'Добавлено в библиотеку'),
        ('status_changed', 'Смена статуса (Транзакция)'),
        ('updated', 'Обновление заметок/оценки'),
    ]

    entry = models.ForeignKey(WatchEntry, on_delete=models.CASCADE, related_name='events', verbose_name="Запись")
    initiator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Инициатор")
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, verbose_name="Тип события")
    description = models.CharField(max_length=255, verbose_name="Описание изменения")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Событие библиотеки"
        verbose_name_plural = "История библиотеки"

    def __str__(self):
        return f"[{self.timestamp.strftime('%d.%m.%Y %H:%M')}] {self.entry.title.title}: {self.description}"