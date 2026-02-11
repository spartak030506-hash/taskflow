import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)


class WebSocketError(Exception):
    pass


def get_project_group_name(project_id: int) -> str:
    return f"project_{project_id}"


def send_to_project_group(project_id: int, event_type: str, event_data: dict) -> bool:
    channel_layer = get_channel_layer()
    group_name = get_project_group_name(project_id)

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "broadcast_event",
                "event_type": event_type,
                "data": event_data,
            },
        )
        return True
    except ConnectionError:
        logger.warning(
            "Redis unavailable, skipping WebSocket broadcast",
            extra={"project_id": project_id, "event_type": event_type},
        )
        return False
    except Exception as e:
        logger.error(
            f"Failed to send WebSocket event: {e}",
            extra={"project_id": project_id, "event_type": event_type},
        )
        return False
