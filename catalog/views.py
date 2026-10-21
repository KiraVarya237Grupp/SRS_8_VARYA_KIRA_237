from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.contrib.auth import login
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status

from .models import WatchEntry, Title, Genre, EntryEvent, FormatInstance
from .serializers import WatchEntrySerializer, EntryEventSerializer


def get_current_user(request):
    if request.user.is_authenticated:
        return request.user
    user, _ = User.objects.get_or_create(username='student_main')
    return user


def check_entry_permission(request, entry):
    current_user = get_current_user(request)
    if entry.owner and entry.owner != current_user and not current_user.is_superuser:
        return False
    return True


def serialize_entry_dict(entry):
    format_val = "Не выбран"
    try:
        if hasattr(entry, 'format_used') and entry.format_used:
            format_val = entry.format_used.name
    except Exception:
        pass

    rating_val = entry.rating if entry.rating else '—'
    rating_raw_val = entry.rating or ''
    notes_val = entry.notes or ''
    poster_val = entry.title.poster.url if entry.title.poster else ''
    owner_val = entry.owner.username if entry.owner else 'Личный профиль'
    created_val = entry.created_at.strftime('%d.%m.%Y %H:%M') if entry.created_at else ''

    genres_list = [g.name for g in entry.title.genres.all()]
    all_formats_list = [{'id': f.id, 'name': f.name, 'available': f.is_available} for f in entry.title.formats.all()]

    return {
        'id': entry.id,
        'title': entry.title.title,
        'kind_code': entry.title.kind,
        'kind': entry.title.get_kind_display(),
        'status_code': entry.status,
        'status': 'В процессе' if entry.status in ['watching', 'in_progress'] else entry.get_status_display(),
        'rating': rating_val,
        'rating_raw': rating_raw_val,
        'notes': notes_val,
        'format_name': format_val,
        'genres': genres_list,
        'all_formats': all_formats_list,
        'poster': poster_val,
        'owner': owner_val,
        'created_at': created_val,
        'detail_url': f"/entry/{entry.id}/"
    }


# HTML ПРЕДСТАВЛЕНИЯ

def index_view(request):
    user = get_current_user(request)
    entries = WatchEntry.objects.filter(owner=user)

    total_titles = entries.count()
    completed_count = entries.filter(status='completed').count()
    recent_entries = entries.select_related('title').order_by('-id')[:5]

    context = {
        'total_titles': total_titles,
        'completed_count': completed_count,
        'recent_entries': recent_entries,
    }
    return render(request, 'index.html', context)


def catalog_view(request):
    user = get_current_user(request)
    User.objects.get_or_create(username='other_user')
    genres = Genre.objects.all()

    context = {
        'genres': genres,
        'current_username': user.username,
    }
    return render(request, 'catalog.html', context)


def stats_view(request):
    user = get_current_user(request)
    entries = WatchEntry.objects.filter(owner=user)
    total_titles = Title.objects.count()
    total_entries = entries.count()

    completed_count = entries.filter(status='completed').count()
    in_progress_count = entries.filter(status='in_progress').count()
    planned_count = entries.filter(status='planned').count()

    context = {
        'total_titles': total_titles,
        'total_entries': total_entries,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'planned_count': planned_count,
    }
    return render(request, 'stats.html', context)


def entry_detail_view(request, pk):
    entry = get_object_or_404(WatchEntry, pk=pk)
    return render(request, 'partials/entry_detail.html', {'entry': entry})


def update_status_view(request, pk):
    pass


@api_view(['POST'])
def api_switch_user(request):
    username = request.data.get('username', 'student_main')
    user, _ = User.objects.get_or_create(username=username)
    login(request, user)

    if username == 'student_main':
        WatchEntry.objects.filter(owner__isnull=True).update(owner=user)

    user_nice_name = "Основной" if username == 'student_main' else "Другой"

    return Response({
        'success': True,
        'username': user.username,
        'message': f"Выполнен вход под пользователем: {user_nice_name}"
    })


# REST API

@api_view(['GET'])
def api_catalog_list(request):
    current_user = get_current_user(request)
    if current_user.username == 'student_main':
        WatchEntry.objects.filter(owner__isnull=True).update(owner=current_user)

    search_query = request.GET.get('search', '').strip()
    genre_query = request.GET.get('genre', 'all').strip()
    status_query = request.GET.get('status', 'all').strip()

    entries = WatchEntry.objects.select_related('title', 'owner', 'format_used').prefetch_related('title__genres',
                                                                                                  'title__formats').filter(
        owner=current_user)

    if search_query:
        entries = entries.filter(title__title__icontains=search_query)

    if genre_query and genre_query != 'all':
        entries = entries.filter(title__genres__name=genre_query)

    if status_query and status_query != 'all':
        if status_query == 'planned':
            entries = entries.filter(status='planned')
        elif status_query in ['in_progress', 'watching']:
            entries = entries.filter(status__in=['in_progress', 'watching'])
        elif status_query == 'completed':
            entries = entries.filter(status='completed')
        else:
            entries = entries.filter(status=status_query)

    entries = entries.distinct().order_by('-id')
    data = [serialize_entry_dict(entry) for entry in entries]

    return Response({'results': data, 'current_user': current_user.username})


@api_view(['POST'])
def api_create_entry(request):
    current_user = get_current_user(request)
    data = request.data

    title_text = str(data.get('title', '')).strip()
    kind = data.get('kind', 'movie')
    genre_names = data.get('genres', [])
    format_name = data.get('format_name', 'Цифровой')
    rating = data.get('rating')

    if not title_text:
        return Response({'error': 'Название произведения обязательно.'}, status=drf_status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            title, created = Title.objects.get_or_create(
                title=title_text,
                defaults={'kind': kind}
            )
            if not created:
                title.kind = kind
                title.save()

            if genre_names:
                genre_objs = [Genre.objects.get_or_create(name=g)[0] for g in genre_names]
                title.genres.set(genre_objs)

            fmt_obj, _ = FormatInstance.objects.get_or_create(name=format_name, defaults={'is_available': True})
            title.formats.add(fmt_obj)

            entry = WatchEntry.objects.create(
                title=title,
                owner=current_user,
                format_used=fmt_obj,
                status='planned',
                rating=int(rating) if rating else None
            )

            EntryEvent.objects.create(
                entry=entry,
                initiator=current_user,
                event_type='created',
                description=f"Произведение добавлено в библиотеку (статус: «В планах», формат: {fmt_obj.name})"
            )

        return Response({'success': True, 'entry': serialize_entry_dict(entry)}, status=drf_status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'PATCH'])
def api_transition_status(request, entry_id):
    """
    Транзакционная бизнес-операция в личной библиотеке
    """
    entry = get_object_or_404(WatchEntry, pk=entry_id)

    if not check_entry_permission(request, entry):
        return Response({'error': 'Доступ запрещён (403): чужая запись.'}, status=drf_status.HTTP_403_FORBIDDEN)

    new_status = request.data.get('status')
    simulate_error = request.data.get('simulate_error', False)

    if not new_status:
        return Response({'error': 'Не указан новый статус.'}, status=drf_status.HTTP_400_BAD_REQUEST)

    # Проверяем допустимость переходов
    is_express_complete = (entry.status == 'planned' and new_status == 'completed')
    is_roll_back = (entry.status in ['in_progress', 'watching'] and new_status == 'planned')

    if not entry.can_transition_to(new_status):
        if not (is_express_complete or is_roll_back):
            return Response({
                'error': f"Недопустимый переход: из статуса «{entry.get_status_display()}» нельзя перейти в выбранный статус."
            }, status=drf_status.HTTP_400_BAD_REQUEST)

    current_user = get_current_user(request)

    try:
        with transaction.atomic():
            old_status_display = entry.get_status_display()

            # 1. Переход planned -> in_progress с проверкой лимита одновременных просмотров
            if entry.status == 'planned' and new_status == 'in_progress':
                # Проверяем, сколько у пользователя уже запущено произведений (в статусе in_progress или watching)
                active_count = WatchEntry.objects.filter(owner=current_user,
                                                         status__in=['in_progress', 'watching']).count()
                MAX_ACTIVE_LIMIT = 3  # Лимит одновременно просматриваемых объектов

                if active_count >= MAX_ACTIVE_LIMIT:
                    return Response({
                        'error': f"Превышен лимит! У вас уже запущено {active_count} произведений (максимум: {MAX_ACTIVE_LIMIT}). Завершите что-то из текущего, чтобы начать новое."
                    }, status=drf_status.HTTP_400_BAD_REQUEST)

                action_desc = f"Начало прочтения/просмотра: «{old_status_display}» → «Читаю / Смотрю сейчас»."

            # 2. Переход in_progress -> completed
            elif entry.status in ['in_progress', 'watching'] and new_status == 'completed':
                if entry.format_used:
                    entry.format_used.is_available = True
                    entry.format_used.save()
                action_desc = f"Произведение завершено: «{old_status_display}» → «Прочитано / Завершено»."

            # 3. Возврат назад из процесса в планы
            elif entry.status in ['in_progress', 'watching'] and new_status == 'planned':
                if entry.format_used:
                    entry.format_used.is_available = True
                    entry.format_used.save()
                action_desc = f"Возврат в планы: «{old_status_display}» → «В планах (Отложено)»."

            # 4. Экспресс-завершение из «В планах» сразу в «Завершено»
            elif entry.status == 'planned' and new_status == 'completed':
                action_desc = f"Экспресс-завершение: «{old_status_display}» → «Прочитано / Завершено»."

            else:
                action_desc = f"Статус изменён на {new_status}"

            entry.status = new_status
            entry.save()

            EntryEvent.objects.create(
                entry=entry,
                initiator=current_user,
                event_type='status_changed',
                description=action_desc
            )

            if simulate_error:
                raise RuntimeError("Искусственный сбой транзакции для проверки отката!")

        entry.refresh_from_db()
        return Response({'success': True, 'message': action_desc, 'entry': serialize_entry_dict(entry)})

    except RuntimeError as e:
        return Response({'error': f"Сбой транзакции (откат выполнен): {str(e)}"},
                        status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'PUT'])
def api_update_note(request, entry_id):
    entry = get_object_or_404(WatchEntry, pk=entry_id)
    if not check_entry_permission(request, entry):
        return Response({'error': 'Доступ запрещён (403).'}, status=drf_status.HTTP_403_FORBIDDEN)

    data = request.data
    current_user = get_current_user(request)
    changes = []

    with transaction.atomic():
        if 'notes' in data:
            entry.notes = str(data['notes']).strip()
            changes.append("обновлена заметка")

        if 'rating' in data:
            val = data['rating']
            if val in ('', None):
                entry.rating = None
                changes.append("сброшена оценка")
            else:
                r_int = int(val)
                if not (1 <= r_int <= 10):
                    return Response({'error': 'Оценка от 1 до 10.'}, status=drf_status.HTTP_400_BAD_REQUEST)
                entry.rating = r_int
                changes.append(f"поставлена оценка {r_int}")

        if not changes:
            return Response({'error': 'Нет данных.'}, status=drf_status.HTTP_400_BAD_REQUEST)

        entry.save()
        EntryEvent.objects.create(
            entry=entry,
            initiator=current_user,
            event_type='updated',
            description=f"Редактирование: {', '.join(changes)}."
        )

    return Response({'status': 'success', 'entry': serialize_entry_dict(entry)})


@api_view(['DELETE', 'POST'])
def api_delete_entry(request, entry_id):
    entry = get_object_or_404(WatchEntry, pk=entry_id)
    if not check_entry_permission(request, entry):
        return Response({'error': 'Доступ запрещён (403).'}, status=drf_status.HTTP_403_FORBIDDEN)

    with transaction.atomic():
        if entry.format_used and entry.status in ['in_progress', 'watching']:
            entry.format_used.is_available = True
            entry.format_used.save()
        entry.delete()

    return Response({'success': True})


@api_view(['GET'])
def api_entry_history(request, entry_id):
    current_user = get_current_user(request)
    if entry_id == 0:
        events = EntryEvent.objects.filter(entry__owner=current_user).select_related('entry__title', 'initiator')[:30]
    else:
        entry = get_object_or_404(WatchEntry, pk=entry_id)
        if not check_entry_permission(request, entry):
            return Response({'error': 'Доступ запрещён (403).'}, status=drf_status.HTTP_403_FORBIDDEN)
        events = entry.events.select_related('initiator').all()

    serializer = EntryEventSerializer(events, many=True)
    return Response({'events': serializer.data})