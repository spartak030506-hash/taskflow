import pytest
from unittest.mock import patch
from apps.tasks.tests.factories import TaskFactory
from apps.websocket.tasks import broadcast_task_created


@pytest.mark.django_db
class TestBroadcastTasks:
    def test_broadcast_task_created(self):
        task = TaskFactory()

        with patch('apps.websocket.tasks.send_to_project_group') as mock_send:
            broadcast_task_created(task.id, task.creator.id)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        assert call_args[0][0] == task.project_id
        assert call_args[0][1] == 'task.created'

    def test_broadcast_task_created_missing_task(self):
        with patch('apps.websocket.tasks.send_to_project_group') as mock_send:
            broadcast_task_created(99999, 1)

        mock_send.assert_not_called()
