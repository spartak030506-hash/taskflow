import pytest
from channels.testing import WebsocketCommunicator
from apps.users.tests.factories import UserFactory
from rest_framework_simplejwt.tokens import AccessToken


@pytest.mark.django_db(transaction=True)
class TestProjectConsumer:
    async def test_connect_success(self, ws_communicator, project_with_member):
        project, member = project_with_member
        token = str(AccessToken.for_user(member))

        communicator = await ws_communicator(project.id, token)
        connected, subprotocol = await communicator.connect()

        assert connected is True, (
            f"Expected successful connection but got: "
            f"connected={connected}, subprotocol={subprotocol}"
        )

        await communicator.disconnect()

    async def test_connect_anonymous_rejected(self, ws_communicator, project_with_member):
        project, _ = project_with_member

        communicator = await ws_communicator(project.id, 'invalid_token')
        connected, _ = await communicator.connect()

        assert connected is True, (
            f"Expected connection to be accepted first"
        )

        message = await communicator.receive_output(timeout=5)

        assert message['type'] == 'websocket.close', (
            f"Expected websocket.close but got {message['type']}"
        )
        assert message['code'] == 4001, (
            f"Expected code 4001 (unauthorized) but got {message.get('code')}"
        )

    async def test_connect_non_member_rejected(self, ws_communicator, project_with_member):
        from channels.db import database_sync_to_async

        project, _ = project_with_member

        @database_sync_to_async
        def create_non_member():
            return UserFactory(is_verified=True)

        non_member = await create_non_member()
        token = str(AccessToken.for_user(non_member))

        communicator = await ws_communicator(project.id, token)
        connected, _ = await communicator.connect()

        assert connected is True, (
            f"Expected connection to be accepted first"
        )

        message = await communicator.receive_output(timeout=5)

        assert message['type'] == 'websocket.close', (
            f"Expected websocket.close but got {message['type']}"
        )
        assert message['code'] == 4003, (
            f"Expected code 4003 (forbidden) but got {message.get('code')}"
        )

    async def test_ping_pong(self, ws_communicator, project_with_member):
        project, member = project_with_member
        token = str(AccessToken.for_user(member))

        communicator = await ws_communicator(project.id, token)
        connected, _ = await communicator.connect()

        assert connected is True, "Failed to connect before ping-pong test"

        await communicator.send_json_to({'type': 'ping'})
        response = await communicator.receive_json_from(timeout=5)

        assert response['type'] == 'pong', (
            f"Expected pong response but got: {response}"
        )

        await communicator.disconnect()
