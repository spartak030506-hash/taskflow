from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'project',
        'status',
        'priority',
        'assignee',
        'deadline',
        'created_at',
    ]
    list_filter = ['status', 'priority', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'project__name', 'assignee__email']
    raw_id_fields = ['project', 'creator', 'assignee']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['project', 'position', '-created_at']
