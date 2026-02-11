import factory
from factory.django import DjangoModelFactory

from apps.projects.models import Project, ProjectMember
from apps.users.tests.factories import UserFactory


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Faker("paragraph")
    status = Project.Status.ACTIVE
    owner = factory.SubFactory(UserFactory, is_verified=True)

    @factory.post_generation
    def create_owner_membership(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is False:
            return
        ProjectMember.objects.get_or_create(
            project=self, user=self.owner, defaults={"role": ProjectMember.Role.OWNER}
        )


class ProjectMemberFactory(DjangoModelFactory):
    class Meta:
        model = ProjectMember

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory, is_verified=True)
    role = ProjectMember.Role.MEMBER
