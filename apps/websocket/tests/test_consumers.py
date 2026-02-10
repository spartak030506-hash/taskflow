import pytest
from channels.testing import WebsocketCommunicator
from apps.users.tests.factories import UserFactory
from rest_framework_simplejwt.tokens import AccessToken


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestProjectConsumer:
    async def test_connect_success(self, ws_communicator, project_with_member):
        project, member = project_with_member
        token = str(AccessToken.for_user(member))

        communicator = await ws_communicator(project.id, token)
        connected, _ = await communicator.connect()

        assert connected is True

        await communicator.disconnect()

    async def test_connect_anonymous_rejected(self, ws_communicator, project_with_member):
        project, _ = project_with_member

        communicator = await ws_communicator(project.id, 'invalid_token')
        connected, code = await communicator.connect()

        assert connected is False
        assert code == 4001

    async def test_ping_pong(self, ws_communicator, project_with_member):
        project, member = project_with_member
        token = str(AccessToken.for_user(member))

        communicator = await ws_communicator(project.id, token)
        await communicator.connect()

        await communicator.send_json_to({'type': 'ping'})
        response = await communicator.receive_json_from()
        assert response['type'] == 'pong'

        await communicator.disconnect()
