from django.contrib import admin

from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'color', 'project', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['name', 'project__name']
    raw_id_fields = ['project']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['project', 'name']
