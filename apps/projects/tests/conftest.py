import pytest

from apps.projects.models import ProjectMember
from apps.users.tests.factories import UserFactory
from .factories import ProjectFactory, ProjectMemberFactory


@pytest.fixture
def project(db):
    return ProjectFactory()


@pytest.fixture
def project_owner(project):
    return project.owner


@pytest.fixture
def project_admin(db, project):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(project=project, user=user, role=ProjectMember.Role.ADMIN)
    return user


@pytest.fixture
def project_member(db, project):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(project=project, user=user, role=ProjectMember.Role.MEMBER)
    return user


@pytest.fixture
def project_viewer(db, project):
    user = UserFactory(is_verified=True)
    ProjectMemberFactory(project=project, user=user, role=ProjectMember.Role.VIEWER)
    return user


@pytest.fixture
def project_with_members(db):
    project = ProjectFactory()
    members = []
    for role in [ProjectMember.Role.ADMIN, ProjectMember.Role.MEMBER, ProjectMember.Role.VIEWER]:
        user = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=user, role=role)
        members.append(user)
    return project, members


@pytest.fixture
def non_member_user(db):
    return UserFactory(is_verified=True)
