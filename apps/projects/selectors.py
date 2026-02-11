import logging

from django.db.models import Count, Q, QuerySet

from apps.users.models import User
from core.cache import (
    CACHE_FALSE_SENTINEL,
    CACHE_NONE_SENTINEL,
    CacheKeys,
    CacheTTL,
    cache_with_lock,
    safe_cache_get,
    safe_cache_set,
)
from core.exceptions import NotFoundError

from .models import Project, ProjectMember

logger = logging.getLogger(__name__)


def get_by_id(project_id: int) -> Project:
    try:
        return Project.objects.select_related("owner").get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError("Проект не найден")


def get_detail(project_id: int) -> dict:
    cache_key = CacheKeys.PROJECT_DETAIL.format(project_id=project_id)

    def fetch_project():
        try:
            project = (
                Project.objects.select_related("owner")
                .annotate(members_count=Count("members"))
                .get(id=project_id)
            )
        except Project.DoesNotExist:
            safe_cache_set(cache_key, CACHE_NONE_SENTINEL, CacheTTL.NOT_FOUND)
            raise NotFoundError("Проект не найден")

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "owner": {
                "id": project.owner.id,
                "email": project.owner.email,
                "first_name": project.owner.first_name,
                "last_name": project.owner.last_name,
                "avatar": project.owner.avatar.url if project.owner.avatar else None,
            },
            "members_count": project.members_count,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }

    result = cache_with_lock(cache_key, CacheTTL.PROJECT, fetch_project)

    if result == CACHE_NONE_SENTINEL:
        raise NotFoundError("Проект не найден")

    return result


def get_by_id_with_members(project_id: int) -> Project:
    try:
        return (
            Project.objects.select_related("owner")
            .prefetch_related("members__user")
            .get(id=project_id)
        )
    except Project.DoesNotExist:
        raise NotFoundError("Проект не найден")


def get_by_id_for_update(project_id: int) -> Project:
    try:
        return Project.objects.select_for_update().get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError("Проект не найден")


def get_by_id_with_members_count(project_id: int) -> Project:
    try:
        return (
            Project.objects.select_related("owner")
            .annotate(members_count=Count("members"))
            .get(id=project_id)
        )
    except Project.DoesNotExist:
        raise NotFoundError("Проект не найден")


def filter_for_user(user: User) -> QuerySet[Project]:
    return (
        Project.objects.filter(members__user=user)
        .select_related("owner")
        .distinct()
        .order_by("-created_at")
    )


def filter_for_user_with_members_count(user: User) -> QuerySet[Project]:
    return (
        Project.objects.filter(members__user=user)
        .select_related("owner")
        .annotate(members_count=Count("members"))
        .distinct()
        .order_by("-created_at")
    )


def get_member(project: Project, user: User) -> ProjectMember:
    try:
        return ProjectMember.objects.select_related("user", "project").get(
            project=project,
            user=user,
        )
    except ProjectMember.DoesNotExist:
        raise NotFoundError("Участник не найден")


def get_member_role(project: Project, user: User) -> str | None:
    cache_key = CacheKeys.MEMBER_ROLE.format(project_id=project.id, user_id=user.id)

    cached = safe_cache_get(cache_key)

    if cached == CACHE_NONE_SENTINEL:
        return None

    if cached is not None:
        return cached

    role = (
        ProjectMember.objects.filter(
            project=project,
            user=user,
        )
        .values_list("role", flat=True)
        .first()
    )

    ttl = CacheTTL.MEMBERSHIP if role is not None else CacheTTL.NOT_FOUND
    cache_value = role if role is not None else CACHE_NONE_SENTINEL

    safe_cache_set(cache_key, cache_value, ttl)
    return role


def filter_members(project: Project) -> QuerySet[ProjectMember]:
    return (
        ProjectMember.objects.filter(project=project).select_related("user").order_by("joined_at")
    )


def exists_member(project: Project, user: User) -> bool:
    cache_key = CacheKeys.EXISTS_MEMBER.format(project_id=project.id, user_id=user.id)

    cached = safe_cache_get(cache_key)

    if cached == CACHE_FALSE_SENTINEL:
        return False

    if cached is not None:
        return cached

    exists = ProjectMember.objects.filter(
        project=project,
        user=user,
    ).exists()

    ttl = CacheTTL.MEMBERSHIP if exists else CacheTTL.NOT_FOUND
    cache_value = exists if exists else CACHE_FALSE_SENTINEL

    safe_cache_set(cache_key, cache_value, ttl)
    return exists


def is_admin_or_owner(project: Project, user: User) -> bool:
    cache_key = CacheKeys.IS_ADMIN_OR_OWNER.format(project_id=project.id, user_id=user.id)

    cached = safe_cache_get(cache_key)

    if cached == CACHE_FALSE_SENTINEL:
        return False

    if cached is not None:
        return cached

    is_admin = ProjectMember.objects.filter(
        project=project,
        user=user,
        role__in=[ProjectMember.Role.OWNER, ProjectMember.Role.ADMIN],
    ).exists()

    ttl = CacheTTL.MEMBERSHIP if is_admin else CacheTTL.NOT_FOUND
    cache_value = is_admin if is_admin else CACHE_FALSE_SENTINEL

    safe_cache_set(cache_key, cache_value, ttl)
    return is_admin


def get_project_with_task_stats(project_id: int) -> Project:
    from apps.tasks.models import Task

    try:
        return (
            Project.objects.select_related("owner")
            .annotate(
                total_tasks=Count("tasks"),
                completed_tasks=Count("tasks", filter=Q(tasks__status=Task.Status.COMPLETED)),
                pending_tasks=Count("tasks", filter=Q(tasks__status=Task.Status.PENDING)),
                in_progress_tasks=Count("tasks", filter=Q(tasks__status=Task.Status.IN_PROGRESS)),
                members_count=Count("members", distinct=True),
            )
            .get(id=project_id)
        )
    except Project.DoesNotExist:
        raise NotFoundError("Проект не найден")
