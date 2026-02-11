from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.tags.tests.factories import TagFactory
from apps.tasks.models import Task
from apps.users.tests.factories import UserFactory

from .factories import TaskFactory


@pytest.mark.django_db
class TestTaskListAPI:
    def test_list_tasks_success(self, api_client, project_for_tasks):
        TaskFactory.create_batch(3, project=project_for_tasks)
        api_client.force_authenticate(user=project_for_tasks.owner)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_tasks_with_filters(self, api_client, project_for_tasks):
        TaskFactory(project=project_for_tasks, status=Task.Status.PENDING)
        TaskFactory(project=project_for_tasks, status=Task.Status.COMPLETED)
        api_client.force_authenticate(user=project_for_tasks.owner)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})

        response = api_client.get(url, {"status": Task.Status.PENDING})

        assert response.status_code == status.HTTP_200_OK
        assert all(t["status"] == Task.Status.PENDING for t in response.data["results"])

    def test_list_tasks_non_member_forbidden(self, api_client, project_for_tasks):
        non_member = UserFactory(is_verified=True)
        api_client.force_authenticate(user=non_member)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskCreateAPI:
    def test_create_task_owner_success(self, api_client, project_for_tasks):
        api_client.force_authenticate(user=project_for_tasks.owner)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})
        data = {"title": "New Task", "priority": Task.Priority.HIGH}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Task"

    def test_create_task_member_success(self, api_client, project_for_tasks, project_member_user):
        api_client.force_authenticate(user=project_member_user)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})
        data = {"title": "Task by Member"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_viewer_forbidden(self, api_client, project_for_tasks, project_viewer_user):
        api_client.force_authenticate(user=project_viewer_user)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})
        data = {"title": "Task"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db(transaction=True)
    def test_create_task_with_assignee(self, api_client, project_for_tasks, project_member_user):
        api_client.force_authenticate(user=project_for_tasks.owner)
        url = reverse("task-list", kwargs={"project_pk": project_for_tasks.pk})
        data = {"title": "Task", "assignee_id": project_member_user.id}

        with patch("apps.tasks.services.send_task_assigned_email.delay"):
            response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["assignee"]["id"] == project_member_user.id


@pytest.mark.django_db
class TestTaskDetailAPI:
    def test_retrieve_task_success(self, api_client, project_for_tasks, task):
        api_client.force_authenticate(user=project_for_tasks.owner)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == task.title

    def test_retrieve_task_wrong_project_not_found(self, api_client):
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        task = TaskFactory(project=project1)
        api_client.force_authenticate(user=project2.owner)
        url = reverse("task-detail", kwargs={"project_pk": project2.pk, "pk": task.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaskUpdateAPI:
    def test_update_task_creator_success(self, api_client, project_for_tasks, task):
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"title": "Updated"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated"

    def test_update_task_assignee_success(self, api_client, project_for_tasks, task_with_assignee):
        task, assignee = task_with_assignee
        api_client.force_authenticate(user=assignee)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"description": "Updated by assignee"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_update_task_admin_success(
        self, api_client, project_for_tasks, task, project_admin_user
    ):
        api_client.force_authenticate(user=project_admin_user)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"title": "Admin update"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_update_task_other_member_forbidden(self, api_client, project_for_tasks, task):
        other_member = UserFactory(is_verified=True)
        ProjectMemberFactory(
            project=project_for_tasks, user=other_member, role=ProjectMember.Role.MEMBER
        )
        api_client.force_authenticate(user=other_member)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"title": "Should fail"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskDeleteAPI:
    def test_delete_task_creator_success(self, api_client, project_for_tasks, task):
        task_id = task.id
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task_id).exists()

    def test_delete_task_admin_success(
        self, api_client, project_for_tasks, task, project_admin_user
    ):
        api_client.force_authenticate(user=project_admin_user)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_task_assignee_forbidden(
        self, api_client, project_for_tasks, task_with_assignee
    ):
        task, assignee = task_with_assignee
        api_client.force_authenticate(user=assignee)
        url = reverse("task-detail", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskStatusAPI:
    def test_change_status_success(self, api_client, project_for_tasks, task):
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-status", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"status": Task.Status.IN_PROGRESS}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == Task.Status.IN_PROGRESS


@pytest.mark.django_db
class TestTaskAssignAPI:
    @pytest.mark.django_db(transaction=True)
    def test_assign_task_success(self, api_client, project_for_tasks, task, project_member_user):
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-assign", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"assignee_id": project_member_user.id}

        with patch("apps.tasks.services.send_task_assigned_email.delay"):
            response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["assignee"]["id"] == project_member_user.id

    def test_assign_task_non_member_fails(self, api_client, project_for_tasks, task):
        non_member = UserFactory(is_verified=True)
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-assign", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"assignee_id": non_member.id}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTaskReorderAPI:
    def test_reorder_task_success(self, api_client, project_for_tasks, task):
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-reorder", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"position": 10}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["position"] == 10


@pytest.mark.django_db
class TestTaskSetTagsAPI:
    def test_set_tags_success(self, api_client, project_for_tasks, task):
        tag1 = TagFactory(project=project_for_tasks)
        tag2 = TagFactory(project=project_for_tasks)
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-set-tags", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"tag_ids": [tag1.id, tag2.id]}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["tags"]) == 2

    def test_set_tags_empty_clears(self, api_client, project_for_tasks, task):
        tag = TagFactory(project=project_for_tasks)
        task.tags.add(tag)
        api_client.force_authenticate(user=task.creator)
        url = reverse("task-set-tags", kwargs={"project_pk": project_for_tasks.pk, "pk": task.pk})
        data = {"tag_ids": []}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["tags"]) == 0
