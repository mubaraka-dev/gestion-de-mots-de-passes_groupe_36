from django.contrib import admin

from .models import PasswordEntry


@admin.register(PasswordEntry)
class PasswordEntryAdmin(admin.ModelAdmin):
    list_display = ("service_name", "username", "user","created_at", "updated_at")
    search_fields = ("service_name", "username", "user__username")
    list_filter = ("created_at", "updated_at")
