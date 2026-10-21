from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('stats/', views.stats_view, name='stats'),
    path('entry/<int:pk>/', views.entry_detail_view, name='entry_detail'),
    path('update-status/<int:pk>/', views.update_status_view, name='update_status'),

    # Маршруты REST API
    path('api/catalog/', views.api_catalog_list, name='api_catalog_list'),
    path('api/entry/create/', views.api_create_entry, name='api_create_entry'),
    path('api/entry/<int:entry_id>/update/', views.api_transition_status, name='api_update_status'),
    path('api/entry/<int:entry_id>/note/', views.api_update_note, name='api_update_note'),
    path('api/entry/<int:entry_id>/delete/', views.api_delete_entry, name='api_delete_entry'),
    path('api/entry/<int:entry_id>/history/', views.api_entry_history, name='api_entry_history'),
    path('api/switch-user/', views.api_switch_user, name='api_switch_user'),
]
