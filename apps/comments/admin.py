from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "task",
        "author",
        "is_edited",
        "created_at",
    ]
    list_filter = ["is_edited", "created_at"]
    search_fields = ["content", "task__title", "author__email"]
    raw_id_fields = ["task", "author"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
