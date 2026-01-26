from django.db.models import Count, QuerySet

from apps.users.models import User
from core.exceptions import NotFoundError

from .models import Project, ProjectMember


def get_by_id(project_id: int) -> Project:
    try:
        return Project.objects.select_related('owner').get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def get_by_id_with_members(project_id: int) -> Project:
    try:
        return Project.objects.select_related('owner').prefetch_related(
            'members__user'
        ).get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def get_by_id_for_update(project_id: int) -> Project:
    try:
        return Project.objects.select_for_update().get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def get_by_id_with_members_count(project_id: int) -> Project:
    try:
        return Project.objects.select_related('owner').annotate(
            members_count=Count('members')
        ).get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def filter_for_user(user: User) -> QuerySet[Project]:
    return Project.objects.filter(
        members__user=user
    ).select_related('owner').distinct()


def filter_for_user_with_members_count(user: User) -> QuerySet[Project]:
    return Project.objects.filter(
        members__user=user
    ).select_related('owner').annotate(
        members_count=Count('members')
    ).distinct()


def get_member(project: Project, user: User) -> ProjectMember:
    try:
        return ProjectMember.objects.select_related('user', 'project').get(
            project=project,
            user=user,
        )
    except ProjectMember.DoesNotExist:
        raise NotFoundError('Участник не найден')


def get_member_role(project: Project, user: User) -> str | None:
    membership = ProjectMember.objects.filter(
        project=project,
        user=user,
    ).values_list('role', flat=True).first()
    return membership


def filter_members(project: Project) -> QuerySet[ProjectMember]:
    return ProjectMember.objects.filter(
        project=project
    ).select_related('user').order_by('joined_at')


def exists_member(project: Project, user: User) -> bool:
    return ProjectMember.objects.filter(
        project=project,
        user=user,
    ).exists()


def is_admin_or_owner(project: Project, user: User) -> bool:
    return ProjectMember.objects.filter(
        project=project,
        user=user,
        role__in=[ProjectMember.Role.OWNER, ProjectMember.Role.ADMIN],
    ).exists()
