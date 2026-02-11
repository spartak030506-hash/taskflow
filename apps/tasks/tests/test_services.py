from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.tasks import services
from apps.tasks.models import Task
from apps.users.tests.factories import UserFactory

from .factories import TaskFactory


@pytest.mark.django_db
class TestCreateTask:
    def test_create_task_success(self):
        project = ProjectFactory()
        creator = project.owner

        task = services.create_task(
            project=project,
            creator=creator,
            title="Test Task",
            description="Description",
        )

        assert task.title == "Test Task"
        assert task.description == "Description"
        assert task.creator == creator
        assert task.project == project
        assert task.status == Task.Status.PENDING

    def test_create_task_auto_position(self):
        project = ProjectFactory()
        TaskFactory(project=project, position=5)

        task = services.create_task(
            project=project,
            creator=project.owner,
            title="New Task",
        )

        assert task.position == 6

    @pytest.mark.django_db(transaction=True)
    def test_create_task_with_assignee_sends_email(self):
        project = ProjectFactory()
        assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=assignee, role=ProjectMember.Role.MEMBER)

        with patch("apps.tasks.services.send_task_assigned_email.delay") as mock_email:
            task = services.create_task(
                project=project,
                creator=project.owner,
                title="Task",
                assignee=assignee,
            )

        assert task.assignee == assignee
        mock_email.assert_called_once()


@pytest.mark.django_db
class TestUpdateTask:
    def test_update_task_title(self):
        task = TaskFactory(title="Old")

        result = services.update_task(task=task, title="New")

        assert result.title == "New"

    def test_update_task_description(self):
        task = TaskFactory(description="Old")

        result = services.update_task(task=task, description="New")

        assert result.description == "New"

    def test_update_task_priority(self):
        task = TaskFactory(priority=Task.Priority.LOW)

        result = services.update_task(task=task, priority=Task.Priority.HIGH)

        assert result.priority == Task.Priority.HIGH

    def test_update_task_deadline(self):
        task = TaskFactory()
        deadline = timezone.now() + timedelta(days=7)

        result = services.update_task(task=task, deadline=deadline)

        assert result.deadline == deadline

    def test_update_task_deadline_to_none(self):
        task = TaskFactory(deadline=timezone.now())

        result = services.update_task(task=task, deadline=None)

        assert result.deadline is None


@pytest.mark.django_db
class TestDeleteTask:
    def test_delete_task_success(self):
        task = TaskFactory()
        task_id = task.id

        services.delete_task(task=task)

        assert not Task.objects.filter(id=task_id).exists()


@pytest.mark.django_db
class TestChangeStatus:
    def test_change_status_success(self):
        task = TaskFactory(status=Task.Status.PENDING)

        result = services.change_status(task=task, new_status=Task.Status.IN_PROGRESS)

        assert result.status == Task.Status.IN_PROGRESS

    def test_change_status_same_returns_unchanged(self):
        task = TaskFactory(status=Task.Status.PENDING)

        result = services.change_status(task=task, new_status=Task.Status.PENDING)

        assert result.status == Task.Status.PENDING

    @pytest.mark.django_db(transaction=True)
    def test_change_status_sends_email_to_assignee(self):
        project = ProjectFactory()
        assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=assignee, role=ProjectMember.Role.MEMBER)
        task = TaskFactory(project=project, assignee=assignee, status=Task.Status.PENDING)

        with patch("apps.tasks.services.send_task_status_changed_email.delay") as mock_email:
            services.change_status(task=task, new_status=Task.Status.IN_PROGRESS)

        mock_email.assert_called_once()


@pytest.mark.django_db
class TestAssignTask:
    @pytest.mark.django_db(transaction=True)
    def test_assign_task_success(self):
        project = ProjectFactory()
        assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=assignee, role=ProjectMember.Role.MEMBER)
        task = TaskFactory(project=project, assignee=None)

        with patch("apps.tasks.services.send_task_assigned_email.delay") as mock_email:
            result = services.assign_task(
                task=task,
                assignee=assignee,
                project_name=project.name,
            )

        assert result.assignee == assignee
        mock_email.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_unassign_task_success(self):
        project = ProjectFactory()
        assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=assignee, role=ProjectMember.Role.MEMBER)
        task = TaskFactory(project=project, assignee=assignee)

        with patch("apps.tasks.services.send_task_unassigned_email.delay") as mock_email:
            result = services.assign_task(
                task=task,
                assignee=None,
                project_name=project.name,
            )

        assert result.assignee is None
        mock_email.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_reassign_task_sends_both_emails(self):
        project = ProjectFactory()
        old_assignee = UserFactory(is_verified=True)
        new_assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=old_assignee, role=ProjectMember.Role.MEMBER)
        ProjectMemberFactory(project=project, user=new_assignee, role=ProjectMember.Role.MEMBER)
        task = TaskFactory(project=project, assignee=old_assignee)

        with patch("apps.tasks.services.send_task_unassigned_email.delay") as mock_unassign:
            with patch("apps.tasks.services.send_task_assigned_email.delay") as mock_assign:
                services.assign_task(
                    task=task,
                    assignee=new_assignee,
                    project_name=project.name,
                )

        mock_unassign.assert_called_once()
        mock_assign.assert_called_once()

    def test_assign_same_user_no_change(self):
        project = ProjectFactory()
        assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=assignee, role=ProjectMember.Role.MEMBER)
        task = TaskFactory(project=project, assignee=assignee)

        result = services.assign_task(
            task=task,
            assignee=assignee,
            project_name=project.name,
        )

        assert result.assignee == assignee


@pytest.mark.django_db
class TestReorderTask:
    def test_reorder_task_move_up(self):
        project = ProjectFactory()
        task1 = TaskFactory(project=project, position=1)
        task2 = TaskFactory(project=project, position=2)
        task3 = TaskFactory(project=project, position=3)

        services.reorder_task(task=task3, new_position=1)

        task1.refresh_from_db()
        task2.refresh_from_db()
        task3.refresh_from_db()
        assert task3.position == 1
        assert task1.position == 2
        assert task2.position == 3

    def test_reorder_task_move_down(self):
        project = ProjectFactory()
        task1 = TaskFactory(project=project, position=1)
        task2 = TaskFactory(project=project, position=2)
        task3 = TaskFactory(project=project, position=3)

        services.reorder_task(task=task1, new_position=3)

        task1.refresh_from_db()
        task2.refresh_from_db()
        task3.refresh_from_db()
        assert task1.position == 3
        assert task2.position == 1
        assert task3.position == 2

    def test_reorder_task_same_position_no_change(self):
        task = TaskFactory(position=2)

        result = services.reorder_task(task=task, new_position=2)

        assert result.position == 2
