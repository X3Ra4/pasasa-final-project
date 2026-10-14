from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import SubscriptionStatus, User


@admin.register(SubscriptionStatus)
class SubscriptionStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("status", "avatar_preview", "bio_short")
    list_filter = UserAdmin.list_filter + ("status",)
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("avatar", "avatar_preview", "status", "bio")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("avatar", "status", "bio")}),
    )
    readonly_fields = ("avatar_preview",)

    @admin.display(description="avatar")
    def avatar_preview(self, obj):
        if not obj.avatar:
            return "-"
        return format_html(
            '<img src="{}" style="max-width: 48px; max-height: 48px; border-radius: 50%;" />',
            obj.avatar.url,
        )

    @admin.display(description="bio")
    def bio_short(self, obj):
        if not obj.bio:
            return "-"
        return obj.bio[:50] + ("..." if len(obj.bio) > 50 else "")
