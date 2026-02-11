from rest_framework import permissions

from apps.projects import selectors as project_selectors


class CanViewTag(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_pk")
        if not project_id:
            return False
        project = project_selectors.get_by_id(project_id)
        return project_selectors.exists_member(project, request.user)


class CanManageTag(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_pk")
        if not project_id:
            return False
        project = project_selectors.get_by_id(project_id)
        return project_selectors.is_admin_or_owner(project, request.user)

    def has_object_permission(self, request, view, obj):
        return project_selectors.is_admin_or_owner(obj.project, request.user)
