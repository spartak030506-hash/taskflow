import pytest
from channels.testing import WebsocketCommunicator
from config.asgi import application
from apps.users.tests.factories import UserFactory
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.projects.models import ProjectMember


@pytest.fixture
def ws_communicator(db):
    async def _create(project_id: int, token: str):
        communicator = WebsocketCommunicator(
            application,
            f'/ws/projects/{project_id}/?token={token}'
        )
        return communicator
    return _create


@pytest.fixture
def jwt_token(user):
    from rest_framework_simplejwt.tokens import AccessToken
    token = AccessToken.for_user(user)
    return str(token)


@pytest.fixture
def project_with_member(db):
    project = ProjectFactory()
    member = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project,
        user=member,
        role=ProjectMember.Role.MEMBER
    )
    return project, member
