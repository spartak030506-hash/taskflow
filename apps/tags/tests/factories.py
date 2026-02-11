import factory
from factory.django import DjangoModelFactory

from apps.projects.tests.factories import ProjectFactory
from apps.tags.models import Tag


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Tag {n}")
    color = "#6B7280"
