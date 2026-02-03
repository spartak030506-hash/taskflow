from rest_framework import permissions

from .. import selectors
from ..models import ProjectMember


class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return selectors.exists_member(obj, request.user)


class IsProjectAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return selectors.is_admin_or_owner(obj, request.user)


class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = selectors.get_member_role(obj, request.user)
        return role == ProjectMember.Role.OWNER
