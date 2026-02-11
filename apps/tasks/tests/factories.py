import factory
from factory.django import DjangoModelFactory

from apps.projects.tests.factories import ProjectFactory
from apps.tasks.models import Task


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    project = factory.SubFactory(ProjectFactory)
    creator = factory.LazyAttribute(lambda obj: obj.project.owner)
    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker("paragraph")
    status = Task.Status.PENDING
    priority = Task.Priority.MEDIUM
    position = factory.Sequence(lambda n: n)
