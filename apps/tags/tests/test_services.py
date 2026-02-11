import pytest

from apps.projects.tests.factories import ProjectFactory
from apps.tags import services
from apps.tags.models import Tag
from apps.tasks.tests.factories import TaskFactory
from core.exceptions import ConflictError, ValidationError

from .factories import TagFactory


@pytest.mark.django_db
class TestCreateTag:
    def test_create_tag_success(self):
        project = ProjectFactory()

        tag = services.create_tag(
            project=project,
            name="Bug",
            color="#FF0000",
        )

        assert tag.name == "Bug"
        assert tag.color == "#FF0000"
        assert tag.project == project

    def test_create_tag_default_color(self):
        project = ProjectFactory()

        tag = services.create_tag(
            project=project,
            name="Feature",
        )

        assert tag.color == "#6B7280"

    def test_create_tag_duplicate_name_raises(self):
        project = ProjectFactory()
        TagFactory(project=project, name="Bug")

        with pytest.raises(ConflictError) as exc_info:
            services.create_tag(
                project=project,
                name="Bug",
            )

        assert "уже существует" in str(exc_info.value)

    def test_create_tag_duplicate_name_case_insensitive(self):
        project = ProjectFactory()
        TagFactory(project=project, name="Bug")

        with pytest.raises(ConflictError):
            services.create_tag(
                project=project,
                name="BUG",
            )

    def test_create_tag_same_name_different_projects_ok(self):
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        TagFactory(project=project1, name="Bug")

        tag = services.create_tag(
            project=project2,
            name="Bug",
        )

        assert tag.name == "Bug"


@pytest.mark.django_db
class TestUpdateTag:
    def test_update_tag_name(self):
        tag = TagFactory(name="Old Name")

        result = services.update_tag(tag=tag, name="New Name")

        assert result.name == "New Name"

    def test_update_tag_color(self):
        tag = TagFactory(color="#000000")

        result = services.update_tag(tag=tag, color="#FF0000")

        assert result.color == "#FF0000"

    def test_update_tag_duplicate_name_raises(self):
        project = ProjectFactory()
        TagFactory(project=project, name="Existing")
        tag = TagFactory(project=project, name="Other")

        with pytest.raises(ConflictError) as exc_info:
            services.update_tag(tag=tag, name="Existing")

        assert "уже существует" in str(exc_info.value)

    def test_update_tag_same_name_ok(self):
        tag = TagFactory(name="Same")

        result = services.update_tag(tag=tag, name="Same")

        assert result.name == "Same"


@pytest.mark.django_db
class TestDeleteTag:
    def test_delete_tag_success(self):
        tag = TagFactory()
        tag_id = tag.id

        services.delete_tag(tag=tag)

        assert not Tag.objects.filter(id=tag_id).exists()

    def test_delete_tag_clears_m2m(self):
        project = ProjectFactory()
        tag = TagFactory(project=project)
        task = TaskFactory(project=project)
        task.tags.add(tag)

        services.delete_tag(tag=tag)

        assert not task.tags.exists()


@pytest.mark.django_db
class TestSetTaskTags:
    def test_set_task_tags_success(self):
        project = ProjectFactory()
        task = TaskFactory(project=project)
        tags = TagFactory.create_batch(2, project=project)
        tag_ids = [t.id for t in tags]

        result = services.set_task_tags(task=task, tag_ids=tag_ids)

        assert result.tags.count() == 2

    def test_set_task_tags_empty_list_clears(self):
        project = ProjectFactory()
        task = TaskFactory(project=project)
        tag = TagFactory(project=project)
        task.tags.add(tag)

        result = services.set_task_tags(task=task, tag_ids=[])

        assert result.tags.count() == 0

    def test_set_task_tags_not_found_raises(self):
        project = ProjectFactory()
        task = TaskFactory(project=project)

        with pytest.raises(ValidationError) as exc_info:
            services.set_task_tags(task=task, tag_ids=[99999])

        assert "не найдены" in str(exc_info.value)

    def test_set_task_tags_wrong_project_raises(self):
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        task = TaskFactory(project=project1)
        tag = TagFactory(project=project2)

        with pytest.raises(ValidationError) as exc_info:
            services.set_task_tags(task=task, tag_ids=[tag.id])

        assert "не принадлежат" in str(exc_info.value)

    def test_set_task_tags_replaces_existing(self):
        project = ProjectFactory()
        task = TaskFactory(project=project)
        old_tag = TagFactory(project=project)
        new_tag = TagFactory(project=project)
        task.tags.add(old_tag)

        result = services.set_task_tags(task=task, tag_ids=[new_tag.id])

        assert list(result.tags.all()) == [new_tag]
