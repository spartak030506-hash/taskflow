from rest_framework import permissions

from apps.projects import selectors as project_selectors
from apps.projects.models import ProjectMember


class CanViewTask(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_pk')
        if not project_id:
            return False
        project = project_selectors.get_by_id(project_id)
        return project_selectors.exists_member(project, request.user)


class CanCreateTask(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_pk')
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


class CanEditTask(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        project = obj.project

        if obj.creator_id == user.id:
            return True

        if obj.assignee_id == user.id:
            return True

        return project_selectors.is_admin_or_owner(project, user)


class CanDeleteTask(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        project = obj.project

        if obj.creator_id == user.id:
            return True

        return project_selectors.is_admin_or_owner(project, user)
