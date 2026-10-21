from django.contrib import admin
from .models import Title, Genre, WatchEntry, EntryEvent
from django.utils.html import format_html
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'poster_thumbnail')
    list_filter = ('kind',)
    search_fields = ('title',)

    def poster_thumbnail(self, obj):
        if obj.poster:
            return f'<img src="{obj.poster.url}" style="max-height:50px; border-radius:4px;">'
        return '—'

    poster_thumbnail.short_description = 'Постер'
    poster_thumbnail.allow_tags = True


@admin.register(WatchEntry)
class WatchEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind_display', 'status', 'rating', 'has_notes', 'owner', 'created_at')
    list_filter = ('status', 'title__kind')
    search_fields = ('title__title',)

    def kind_display(self, obj):
        return obj.title.get_kind_display()

    kind_display.short_description = 'Тип'

    def has_notes(self, obj):
        if obj.notes:
            return format_html('<span style="color: green; font-weight: bold;">Да</span>')
        return format_html('<span style="color: gray;">Нет</span>')

    has_notes.short_description = 'Заметки'

@admin.register(EntryEvent)
class EntryEventAdmin(admin.ModelAdmin):
    list_display = ('entry', 'initiator', 'event_type', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('description', 'entry__title__title')