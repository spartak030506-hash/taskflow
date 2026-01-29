from django.db import transaction

from apps.projects.models import Project
from apps.tasks.models import Task
from core.exceptions import ConflictError, ValidationError

from . import selectors
from .models import Tag


@transaction.atomic
def create_tag(
    *,
    project: Project,
    name: str,
    color: str = '#6B7280',
) -> Tag:
    if selectors.exists_tag_name_in_project(project, name):
        raise ConflictError('Тег с таким именем уже существует в проекте')

    tag = Tag.objects.create(
        project=project,
        name=name,
        color=color,
    )
    return tag


@transaction.atomic
def update_tag(
    *,
    tag: Tag,
    name: str | None = None,
    color: str | None = None,
) -> Tag:
    update_fields = ['updated_at']

    if name is not None:
        if selectors.exists_tag_name_in_project(tag.project, name, exclude_id=tag.id):
            raise ConflictError('Тег с таким именем уже существует в проекте')
        tag.name = name
        update_fields.append('name')

    if color is not None:
        tag.color = color
        update_fields.append('color')

    tag.save(update_fields=update_fields)
    return tag


@transaction.atomic
def delete_tag(*, tag: Tag) -> None:
    tag.delete()


@transaction.atomic
def set_task_tags(*, task: Task, tag_ids: list[int]) -> Task:
    if not tag_ids:
        task.tags.clear()
        return task

    unique_tag_ids = list(set(tag_ids))
    tags = list(selectors.filter_by_ids(unique_tag_ids))

    if len(tags) != len(unique_tag_ids):
        found_ids = {tag.id for tag in tags}
        missing_ids = set(unique_tag_ids) - found_ids
        raise ValidationError(f'Теги не найдены: {missing_ids}')

    for tag in tags:
        if tag.project_id != task.project_id:
            raise ValidationError('Некоторые теги не принадлежат проекту задачи')

    task.tags.set(tags)
    return task
