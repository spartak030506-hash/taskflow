import pytest
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from apps.users.tests.factories import UserFactory
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.projects.models import ProjectMember
from apps.websocket.routing import websocket_urlpatterns
from core.middleware import JWTAuthMiddleware

test_application = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


@pytest.fixture
async def ws_communicator():
    communicators = []

    async def _create(project_id: int, token: str):
        path = f'/ws/projects/{project_id}/?token={token}'
        communicator = WebsocketCommunicator(
            test_application,
            path
        )
        communicators.append(communicator)
        return communicator

    yield _create

    for communicator in communicators:
        try:
            await communicator.disconnect()
        except Exception:
            pass


@pytest.fixture
def jwt_token(user):
    from rest_framework_simplejwt.tokens import AccessToken
    token = AccessToken.for_user(user)
    return str(token)


@pytest.fixture
def project_with_member():
    project = ProjectFactory()
    member = UserFactory(is_verified=True)
    ProjectMemberFactory(
        project=project,
        user=member,
        role=ProjectMember.Role.MEMBER
    )
    return project, member
