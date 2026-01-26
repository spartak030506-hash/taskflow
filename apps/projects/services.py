from django.db import transaction

from apps.users.models import User
from core.exceptions import ConflictError, ValidationError

from . import selectors
from .models import Project, ProjectMember
from .tasks import (
    send_project_invitation_email,
    send_removed_from_project_email,
    send_role_changed_email,
)


@transaction.atomic
def create_project(*, owner: User, name: str, description: str = '') -> Project:
    project = Project.objects.create(
        owner=owner,
        name=name,
        description=description,
    )

    ProjectMember.objects.create(
        project=project,
        user=owner,
        role=ProjectMember.Role.OWNER,
    )

    project.refresh_from_db()
    project.owner = owner
    return project


@transaction.atomic
def update_project(
    *,
    project: Project,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    update_fields = ['updated_at']

    if name is not None:
        project.name = name
        update_fields.append('name')

    if description is not None:
        project.description = description
        update_fields.append('description')

    project.save(update_fields=update_fields)
    return project


@transaction.atomic
def delete_project(*, project: Project) -> None:
    project.delete()


@transaction.atomic
def archive_project(*, project: Project) -> Project:
    project.status = Project.Status.ARCHIVED
    project.save(update_fields=['status', 'updated_at'])
    return project


@transaction.atomic
def add_member(
    *,
    project: Project,
    user: User,
    role: str = ProjectMember.Role.MEMBER,
) -> ProjectMember:
    if selectors.exists_member(project, user):
        raise ConflictError('Пользователь уже является участником проекта')

    if role == ProjectMember.Role.OWNER:
        raise ValidationError('Нельзя добавить участника с ролью владельца')

    member = ProjectMember.objects.create(
        project=project,
        user=user,
        role=role,
    )

    _user_id = user.id
    _project_id = project.id
    _role = role
    transaction.on_commit(
        lambda: send_project_invitation_email.delay(_user_id, _project_id, _role)
    )

    return member


@transaction.atomic
def update_member_role(*, membership: ProjectMember, role: str) -> ProjectMember:
    if membership.role == ProjectMember.Role.OWNER:
        raise ValidationError('Нельзя изменить роль владельца проекта')

    if role == ProjectMember.Role.OWNER:
        raise ValidationError('Нельзя назначить роль владельца')

    old_role = membership.role
    membership.role = role
    membership.save(update_fields=['role'])

    if old_role != role:
        _user_id = membership.user_id
        _project_id = membership.project_id
        _role = role
        transaction.on_commit(
            lambda: send_role_changed_email.delay(_user_id, _project_id, _role)
        )

    return membership


@transaction.atomic
def remove_member(*, membership: ProjectMember) -> None:
    if membership.role == ProjectMember.Role.OWNER:
        raise ValidationError('Нельзя удалить владельца из проекта')

    _user_id = membership.user_id
    _project_name = membership.project.name

    membership.delete()

    transaction.on_commit(
        lambda: send_removed_from_project_email.delay(_user_id, _project_name)
    )


@transaction.atomic
def leave_project(*, project: Project, user: User) -> None:
    membership = selectors.get_member(project, user)

    if membership.role == ProjectMember.Role.OWNER:
        raise ValidationError('Владелец не может покинуть проект')

    membership.delete()
