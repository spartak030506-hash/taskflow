import pytest
from django.urls import reverse
from rest_framework import status

from apps.comments.models import Comment
from apps.tasks.tests.factories import TaskFactory
from apps.users.tests.factories import UserFactory

from .factories import CommentFactory


@pytest.mark.django_db
class TestCommentListAPI:
    def test_list_comments_success(self, api_client, project_for_comments, task_for_comments):
        CommentFactory.create_batch(3, task=task_for_comments)
        api_client.force_authenticate(user=project_for_comments.owner)
        url = reverse(
            "comment-list",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

    def test_list_comments_non_member_forbidden(
        self, api_client, project_for_comments, task_for_comments
    ):
        non_member = UserFactory(is_verified=True)
        api_client.force_authenticate(user=non_member)
        url = reverse(
            "comment-list",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCommentCreateAPI:
    def test_create_comment_owner_success(
        self, api_client, project_for_comments, task_for_comments
    ):
        api_client.force_authenticate(user=project_for_comments.owner)
        url = reverse(
            "comment-list",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
            },
        )
        data = {"content": "New comment"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "New comment"

    def test_create_comment_member_success(
        self, api_client, project_for_comments, task_for_comments, project_member_for_comments
    ):
        api_client.force_authenticate(user=project_member_for_comments)
        url = reverse(
            "comment-list",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
            },
        )
        data = {"content": "Member comment"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_comment_viewer_forbidden(
        self, api_client, project_for_comments, task_for_comments, project_viewer_for_comments
    ):
        api_client.force_authenticate(user=project_viewer_for_comments)
        url = reverse(
            "comment-list",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
            },
        )
        data = {"content": "Should fail"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_comment_empty_content_fails(
        self, api_client, project_for_comments, task_for_comments
    ):
        api_client.force_authenticate(user=project_for_comments.owner)
        url = reverse(
            "comment-list",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
            },
        )
        data = {"content": ""}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCommentDetailAPI:
    def test_retrieve_comment_success(
        self, api_client, project_for_comments, task_for_comments, comment
    ):
        api_client.force_authenticate(user=project_for_comments.owner)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == comment.content

    def test_retrieve_comment_wrong_task_not_found(self, api_client, project_for_comments):
        task1 = TaskFactory(project=project_for_comments)
        task2 = TaskFactory(project=project_for_comments)
        comment = CommentFactory(task=task1)
        api_client.force_authenticate(user=project_for_comments.owner)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task2.pk,
                "pk": comment.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCommentUpdateAPI:
    def test_update_comment_author_success(
        self, api_client, project_for_comments, task_for_comments, comment_author
    ):
        comment, author = comment_author
        api_client.force_authenticate(user=author)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )
        data = {"content": "Updated"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Updated"
        assert response.data["is_edited"] is True

    def test_update_comment_other_user_forbidden(
        self, api_client, project_for_comments, task_for_comments, comment_author
    ):
        comment, author = comment_author
        other_user = UserFactory(is_verified=True)
        api_client.force_authenticate(user=other_user)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )
        data = {"content": "Should fail"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_comment_admin_forbidden(
        self,
        api_client,
        project_for_comments,
        task_for_comments,
        comment_author,
        project_admin_for_comments,
    ):
        comment, author = comment_author
        api_client.force_authenticate(user=project_admin_for_comments)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )
        data = {"content": "Should fail"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCommentDeleteAPI:
    def test_delete_comment_author_success(
        self, api_client, project_for_comments, task_for_comments, comment_author
    ):
        comment, author = comment_author
        comment_id = comment.id
        api_client.force_authenticate(user=author)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_delete_comment_admin_success(
        self,
        api_client,
        project_for_comments,
        task_for_comments,
        comment_author,
        project_admin_for_comments,
    ):
        comment, author = comment_author
        api_client.force_authenticate(user=project_admin_for_comments)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_comment_other_member_forbidden(
        self,
        api_client,
        project_for_comments,
        task_for_comments,
        comment_author,
        project_member_for_comments,
    ):
        comment, author = comment_author
        api_client.force_authenticate(user=project_member_for_comments)
        url = reverse(
            "comment-detail",
            kwargs={
                "project_pk": project_for_comments.pk,
                "task_pk": task_for_comments.pk,
                "pk": comment.pk,
            },
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
