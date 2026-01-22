# users/api/legacy/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("sync/", views.legacy_sync_users, name="api_legacy_sync_users"),
    path("upsert/", views.legacy_upsert_user, name="api_legacy_upsert_user"),
]
