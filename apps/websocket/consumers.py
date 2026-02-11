import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.projects import selectors as project_selectors

logger = logging.getLogger(__name__)


class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            logger.warning("WebSocket: anonymous user tried to connect")
            await self.accept()
            await self.close(code=4001)
            return

        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group_name = f"project_{self.project_id}"

        check_membership = database_sync_to_async(
            self._check_project_membership, thread_sensitive=True
        )
        is_member = await check_membership(self.project_id, user.id)
        if not is_member:
            logger.warning(f"WebSocket: user {user.id} not member of project {self.project_id}")
            await self.accept()
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(f"WebSocket connected: user={user.id}, project={self.project_id}")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        logger.info(f"WebSocket disconnected: code={close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except Exception as e:
            logger.warning(f"WebSocket receive error: {e}")

    async def broadcast_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": event["event_type"],
                    "data": event["data"],
                }
            )
        )

    def _check_project_membership(self, project_id: int, user_id: int) -> bool:
        from apps.projects.models import Project
        from apps.users.models import User

        try:
            project = project_selectors.get_by_id(project_id)
            user = User.objects.get(id=user_id)
            return project_selectors.exists_member(project, user)

        except (Project.DoesNotExist, User.DoesNotExist) as e:
            logger.warning(
                f"WebSocket membership check failed: {type(e).__name__}",
                extra={"project_id": project_id, "user_id": user_id, "error": str(e)},
            )
            return False

        except Exception as e:
            logger.error(
                f"WebSocket membership check unexpected error: {type(e).__name__}",
                extra={"project_id": project_id, "user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            return False
