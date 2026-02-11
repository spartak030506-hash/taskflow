from rest_framework import permissions

from apps.projects import selectors as project_selectors
from apps.projects.models import ProjectMember


class CanViewComment(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_pk")
        if not project_id:
            return False
        project = project_selectors.get_by_id(project_id)
        return project_selectors.exists_member(project, request.user)


class CanCreateComment(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_pk")
        if not project_id:
            return False
        project = project_selectors.get_by_id(project_id)
        role = project_selectors.get_member_role(project, request.user)
        if not role:
            return False
        return role in [
            ProjectMember.Role.OWNER,
            ProjectMember.Role.ADMIN,
            ProjectMember.Role.MEMBER,
        ]


class CanEditComment(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class CanDeleteComment(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if obj.author_id == user.id:
            return True

        project = obj.task.project
        return project_selectors.is_admin_or_owner(project, user)
