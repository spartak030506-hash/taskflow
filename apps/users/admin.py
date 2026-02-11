from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EmailVerificationToken, PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "is_verified", "is_active", "date_joined"]
    list_filter = ["is_verified", "is_active", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {"fields": ("first_name", "last_name", "avatar", "phone", "bio")},
        ),
        ("Статус", {"fields": ("is_verified", "is_active", "is_staff", "is_superuser")}),
        ("Права", {"fields": ("groups", "user_permissions")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "is_used", "created_at", "expires_at"]
    list_filter = ["is_used", "created_at"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]
