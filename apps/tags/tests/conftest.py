import pytest

from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.users.tests.factories import UserFactory
from .factories import TagFactory


@pytest.fixture
def project_with_owner(db):
    project = ProjectFactory()
    return project, project.owner


@pytest.fixture
def tag(db, project_with_owner):
    project, owner = project_with_owner
    return TagFactory(project=project)


@pytest.fixture
def tags_in_project(db, project_with_owner):
    project, owner = project_with_owner
    tags = TagFactory.create_batch(3, project=project)
    return project, tags


@pytest.fixture
def project_admin_for_tags(db, project_with_owner):
    project, owner = project_with_owner
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(project=project, user=user, role=ProjectMember.Role.ADMIN)
    return user


@pytest.fixture
def project_member_for_tags(db, project_with_owner):
    project, owner = project_with_owner
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(project=project, user=user, role=ProjectMember.Role.MEMBER)
    return user
