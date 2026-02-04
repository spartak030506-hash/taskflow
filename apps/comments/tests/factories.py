import factory
from factory.django import DjangoModelFactory

from apps.comments.models import Comment
from apps.tasks.tests.factories import TaskFactory
from apps.users.tests.factories import UserFactory


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.LazyAttribute(lambda obj: obj.task.creator)
    content = factory.Faker('paragraph')
    is_edited = False
