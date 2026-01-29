from django.db.models import QuerySet

from apps.projects.models import Project
from core.exceptions import NotFoundError

from .models import Tag


def get_by_id(tag_id: int) -> Tag:
    try:
        return Tag.objects.select_related('project').get(id=tag_id)
    except Tag.DoesNotExist:
        raise NotFoundError('Тег не найден')


def get_by_id_for_update(tag_id: int) -> Tag:
    try:
        return Tag.objects.select_for_update().select_related('project').get(id=tag_id)
    except Tag.DoesNotExist:
        raise NotFoundError('Тег не найден')


def filter_by_project(project: Project) -> QuerySet[Tag]:
    return Tag.objects.filter(project=project)


def filter_by_ids(tag_ids: list[int]) -> QuerySet[Tag]:
    return Tag.objects.filter(id__in=tag_ids).select_related('project')


def exists_tag_name_in_project(project: Project, name: str, exclude_id: int | None = None) -> bool:
    queryset = Tag.objects.filter(project=project, name__iexact=name)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    return queryset.exists()
