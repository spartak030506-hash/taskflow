import pytest
from rest_framework import status
from django.urls import reverse

from apps.tags.models import Tag
from apps.projects.models import ProjectMember
from apps.projects.tests.factories import ProjectFactory, ProjectMemberFactory
from apps.users.tests.factories import UserFactory
from .factories import TagFactory


@pytest.mark.django_db
class TestTagListAPI:
    def test_list_tags_success(self, api_client, project_with_owner):
        project, owner = project_with_owner
        TagFactory.create_batch(3, project=project)
        api_client.force_authenticate(user=owner)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3

    def test_list_tags_member_success(self, api_client, project_with_owner, project_member_for_tags):
        project, owner = project_with_owner
        TagFactory.create_batch(2, project=project)
        api_client.force_authenticate(user=project_member_for_tags)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_tags_non_member_forbidden(self, api_client, project_with_owner):
        project, owner = project_with_owner
        non_member = UserFactory(is_verified=True)
        api_client.force_authenticate(user=non_member)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTagCreateAPI:
    def test_create_tag_owner_success(self, api_client, project_with_owner):
        project, owner = project_with_owner
        api_client.force_authenticate(user=owner)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})
        data = {'name': 'Bug', 'color': '#FF0000'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Bug'
        assert Tag.objects.filter(project=project, name='Bug').exists()

    def test_create_tag_admin_success(self, api_client, project_with_owner, project_admin_for_tags):
        project, owner = project_with_owner
        api_client.force_authenticate(user=project_admin_for_tags)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})
        data = {'name': 'Feature'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_tag_member_forbidden(self, api_client, project_with_owner, project_member_for_tags):
        project, owner = project_with_owner
        api_client.force_authenticate(user=project_member_for_tags)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})
        data = {'name': 'Bug'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tag_duplicate_conflict(self, api_client, project_with_owner):
        project, owner = project_with_owner
        TagFactory(project=project, name='Bug')
        api_client.force_authenticate(user=owner)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})
        data = {'name': 'Bug'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_tag_invalid_color(self, api_client, project_with_owner):
        project, owner = project_with_owner
        api_client.force_authenticate(user=owner)
        url = reverse('tag-list', kwargs={'project_pk': project.pk})
        data = {'name': 'Bug', 'color': 'invalid'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTagDetailAPI:
    def test_retrieve_tag_success(self, api_client, project_with_owner):
        project, owner = project_with_owner
        tag = TagFactory(project=project)
        api_client.force_authenticate(user=owner)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == tag.name

    def test_retrieve_tag_wrong_project_not_found(self, api_client):
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        tag = TagFactory(project=project1)
        api_client.force_authenticate(user=project2.owner)
        url = reverse('tag-detail', kwargs={'project_pk': project2.pk, 'pk': tag.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTagUpdateAPI:
    def test_update_tag_owner_success(self, api_client, project_with_owner):
        project, owner = project_with_owner
        tag = TagFactory(project=project, name='Old')
        api_client.force_authenticate(user=owner)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})
        data = {'name': 'New'}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'New'

    def test_update_tag_admin_success(self, api_client, project_with_owner, project_admin_for_tags):
        project, owner = project_with_owner
        tag = TagFactory(project=project)
        api_client.force_authenticate(user=project_admin_for_tags)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})
        data = {'color': '#00FF00'}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_update_tag_member_forbidden(self, api_client, project_with_owner, project_member_for_tags):
        project, owner = project_with_owner
        tag = TagFactory(project=project)
        api_client.force_authenticate(user=project_member_for_tags)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})
        data = {'name': 'New'}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTagDeleteAPI:
    def test_delete_tag_owner_success(self, api_client, project_with_owner):
        project, owner = project_with_owner
        tag = TagFactory(project=project)
        tag_id = tag.id
        api_client.force_authenticate(user=owner)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(id=tag_id).exists()

    def test_delete_tag_admin_success(self, api_client, project_with_owner, project_admin_for_tags):
        project, owner = project_with_owner
        tag = TagFactory(project=project)
        api_client.force_authenticate(user=project_admin_for_tags)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_tag_member_forbidden(self, api_client, project_with_owner, project_member_for_tags):
        project, owner = project_with_owner
        tag = TagFactory(project=project)
        api_client.force_authenticate(user=project_member_for_tags)
        url = reverse('tag-detail', kwargs={'project_pk': project.pk, 'pk': tag.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
