import pytest

from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.users.tests.factories import UserFactory
from .factories import TaskFactory


@pytest.fixture
def project_for_tasks(db):
    return ProjectFactory()


@pytest.fixture
def task(db, project_for_tasks):
    return TaskFactory(project=project_for_tasks)


@pytest.fixture
def task_with_assignee(db, project_for_tasks):
    assignee = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_tasks,
        user=assignee,
        role=ProjectMember.Role.MEMBER,
    )
    task = TaskFactory(project=project_for_tasks, assignee=assignee)
    return task, assignee


@pytest.fixture
def project_member_user(db, project_for_tasks):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_tasks,
        user=user,
        role=ProjectMember.Role.MEMBER,
    )
    return user


@pytest.fixture
def project_viewer_user(db, project_for_tasks):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_tasks,
        user=user,
        role=ProjectMember.Role.VIEWER,
    )
    return user


@pytest.fixture
def project_admin_user(db, project_for_tasks):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_tasks,
        user=user,
        role=ProjectMember.Role.ADMIN,
    )
    return user
