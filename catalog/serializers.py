from rest_framework import serializers
from .models import Genre, Title, WatchEntry, EntryEvent, FormatInstance


class EntryEventSerializer(serializers.ModelSerializer):
    initiator_name = serializers.SerializerMethodField()
    timestamp_formatted = serializers.DateTimeField(source='timestamp', format='%d.%m.%Y %H:%M:%S', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = EntryEvent
        fields = ['id', 'event_type', 'event_type_display', 'initiator_name', 'description', 'timestamp_formatted']

    def get_initiator_name(self, obj):
        # Если инициатор не указан, пишем "Система"
        if not obj.initiator:
            return "Система"

        # Меняем технические логины на красивые русские названия
        if obj.initiator.username == 'student_main':
            return "Основной"
        elif obj.initiator.username == 'other_user':
            return "Другой"

        return obj.initiator.username


class WatchEntrySerializer(serializers.ModelSerializer):
    title_name = serializers.CharField(source='title.title', read_only=True)
    kind_display = serializers.CharField(source='title.get_kind_display', read_only=True)
    kind_code = serializers.CharField(source='title.kind', read_only=True)
    status_display = serializers.SerializerMethodField()
    format_name = serializers.CharField(source='format_used.name', read_only=True)
    genres = serializers.SerializerMethodField()
    all_formats = serializers.SerializerMethodField()
    poster = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    created_at_formatted = serializers.DateTimeField(source='created_at', format='%d.%m.%Y %H:%M', read_only=True)

    class Meta:
        model = WatchEntry
        fields = [
            'id', 'title_name', 'kind_code', 'kind_display',
            'status', 'status_display', 'rating', 'notes',
            'format_name', 'genres', 'all_formats', 'poster',
            'owner_name', 'created_at_formatted'
        ]

    def get_status_display(self, obj):
        if obj.status in ['watching', 'in_progress']:
            return 'В процессе'
        return obj.get_status_display()

    def get_genres(self, obj):
        return [g.name for g in obj.title.genres.all()]

    def get_all_formats(self, obj):
        return [{'id': f.id, 'name': f.name, 'available': f.is_available} for f in obj.title.formats.all()]

    def get_poster(self, obj):
        return obj.title.poster.url if obj.title.poster else ''

    def get_owner_name(self, obj):
        return obj.owner.username if obj.owner else 'Личный профиль'
