from unittest.mock import patch

import pytest

from apps.comments import services
from apps.comments.models import Comment
from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.tasks.tests.factories import TaskFactory
from apps.users.tests.factories import UserFactory

from .factories import CommentFactory


@pytest.mark.django_db
class TestCreateComment:
    def test_create_comment_success(self):
        project = ProjectFactory()
        task = TaskFactory(project=project)
        author = project.owner

        comment = services.create_comment(
            task=task,
            author=author,
            content="Test comment",
        )

        assert comment.content == "Test comment"
        assert comment.author == author
        assert comment.task == task
        assert comment.is_edited is False

    @pytest.mark.django_db(transaction=True)
    def test_create_comment_notifies_assignee(self):
        project = ProjectFactory()
        assignee = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=assignee, role=ProjectMember.Role.MEMBER)
        task = TaskFactory(project=project, assignee=assignee)
        author = project.owner

        with patch(
            "apps.comments.services.send_comment_notification_to_assignee.delay"
        ) as mock_notify:
            services.create_comment(
                task=task,
                author=author,
                content="Comment",
            )

        mock_notify.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_create_comment_notifies_creator(self):
        project = ProjectFactory()
        task = TaskFactory(project=project)
        commenter = UserFactory(is_verified=True)
        ProjectMemberFactory(project=project, user=commenter, role=ProjectMember.Role.MEMBER)

        with patch(
            "apps.comments.services.send_comment_notification_to_creator.delay"
        ) as mock_notify:
            services.create_comment(
                task=task,
                author=commenter,
                content="Comment",
            )

        mock_notify.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_create_comment_no_duplicate_notifications(self):
        project = ProjectFactory()
        task = TaskFactory(project=project, assignee=project.owner)

        with patch(
            "apps.comments.services.send_comment_notification_to_assignee.delay"
        ) as mock_assignee:
            with patch(
                "apps.comments.services.send_comment_notification_to_creator.delay"
            ) as mock_creator:
                services.create_comment(
                    task=task,
                    author=project.owner,
                    content="Comment",
                )

        mock_assignee.assert_not_called()
        mock_creator.assert_not_called()


@pytest.mark.django_db
class TestUpdateComment:
    def test_update_comment_success(self):
        comment = CommentFactory(content="Old content")

        result = services.update_comment(comment=comment, content="New content")

        assert result.content == "New content"

    def test_update_comment_sets_is_edited(self):
        comment = CommentFactory(is_edited=False)

        result = services.update_comment(comment=comment, content="Updated")

        assert result.is_edited is True


@pytest.mark.django_db
class TestDeleteComment:
    def test_delete_comment_success(self):
        comment = CommentFactory()
        comment_id = comment.id

        services.delete_comment(comment=comment)

        assert not Comment.objects.filter(id=comment_id).exists()
