import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.projects import selectors as project_selectors

logger = logging.getLogger(__name__)


class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            logger.warning('WebSocket: anonymous user tried to connect')
            await self.close(code=4001)
            return

        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.group_name = f'project_{self.project_id}'

        is_member = await self._check_project_membership(self.project_id, user.id)
        if not is_member:
            logger.warning(
                f'WebSocket: user {user.id} not member of project {self.project_id}'
            )
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(f'WebSocket connected: user={user.id}, project={self.project_id}')

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        logger.info(f'WebSocket disconnected: code={close_code}')

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception as e:
            logger.warning(f'WebSocket receive error: {e}')

    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'data': event['data'],
        }))

    @database_sync_to_async
    def _check_project_membership(self, project_id: int, user_id: int) -> bool:
        try:
            project = project_selectors.get_by_id(project_id)
            from apps.users.models import User
            user = User.objects.get(id=user_id)
            return project_selectors.exists_member(project, user)
        except Exception:
            return False
