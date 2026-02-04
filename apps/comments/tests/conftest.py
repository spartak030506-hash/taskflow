import pytest

from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.tasks.tests.factories import TaskFactory
from apps.users.tests.factories import UserFactory
from .factories import CommentFactory


@pytest.fixture
def project_for_comments(db):
    return ProjectFactory()


@pytest.fixture
def task_for_comments(db, project_for_comments):
    return TaskFactory(project=project_for_comments)


@pytest.fixture
def comment(db, task_for_comments):
    return CommentFactory(task=task_for_comments)


@pytest.fixture
def task_with_comments(db, project_for_comments):
    task = TaskFactory(project=project_for_comments)
    comments = CommentFactory.create_batch(3, task=task)
    return task, comments


@pytest.fixture
def comment_author(db, project_for_comments, task_for_comments):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_comments,
        user=user,
        role=ProjectMember.Role.MEMBER,
    )
    comment = CommentFactory(task=task_for_comments, author=user)
    return comment, user


@pytest.fixture
def project_member_for_comments(db, project_for_comments):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_comments,
        user=user,
        role=ProjectMember.Role.MEMBER,
    )
    return user


@pytest.fixture
def project_viewer_for_comments(db, project_for_comments):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_comments,
        user=user,
        role=ProjectMember.Role.VIEWER,
    )
    return user


@pytest.fixture
def project_admin_for_comments(db, project_for_comments):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project_for_comments,
        user=user,
        role=ProjectMember.Role.ADMIN,
    )
    return user
