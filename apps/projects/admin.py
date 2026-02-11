from django.contrib import admin

from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    raw_id_fields = ["user"]
    readonly_fields = ["joined_at"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "status", "owner", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "owner__email"]
    raw_id_fields = ["owner"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProjectMemberInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "user", "role", "joined_at"]
    list_filter = ["role", "joined_at"]
    search_fields = ["project__name", "user__email"]
    raw_id_fields = ["project", "user"]
    readonly_fields = ["joined_at"]
