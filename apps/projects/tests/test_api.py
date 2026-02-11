from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project, ProjectMember
from apps.users.tests.factories import UserFactory

from .factories import ProjectFactory, ProjectMemberFactory


@pytest.mark.django_db
class TestProjectListAPI:
    def test_list_projects_success(self, api_client, project, project_owner):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-list")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_projects_only_member_projects(self, api_client):
        user = UserFactory(is_verified=True)
        own_project = ProjectFactory(owner=user)
        other_project = ProjectFactory()
        api_client.force_authenticate(user=user)
        url = reverse("project-list")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        project_ids = [p["id"] for p in response.data["results"]]
        assert own_project.id in project_ids
        assert other_project.id not in project_ids

    def test_list_projects_unauthenticated(self, api_client):
        url = reverse("project-list")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProjectCreateAPI:
    def test_create_project_success(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse("project-list")
        data = {"name": "New Project", "description": "Test description"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Project"
        assert Project.objects.filter(name="New Project").exists()

    def test_create_project_owner_becomes_member(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse("project-list")
        data = {"name": "New Project"}

        response = api_client.post(url, data)

        project = Project.objects.get(id=response.data["id"])
        assert ProjectMember.objects.filter(
            project=project, user=verified_user, role=ProjectMember.Role.OWNER
        ).exists()


@pytest.mark.django_db
class TestProjectDetailAPI:
    def test_retrieve_project_success(self, api_client, project, project_owner):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-detail", kwargs={"pk": project.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == project.name

    def test_retrieve_project_non_member_forbidden(self, api_client, project, non_member_user):
        api_client.force_authenticate(user=non_member_user)
        url = reverse("project-detail", kwargs={"pk": project.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProjectUpdateAPI:
    def test_update_project_owner_success(self, api_client, project, project_owner):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-detail", kwargs={"pk": project.pk})
        data = {"name": "Updated Name"}

        with patch("apps.projects.services.invalidate_project_cache"):
            response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_update_project_admin_success(self, api_client, project, project_admin):
        api_client.force_authenticate(user=project_admin)
        url = reverse("project-detail", kwargs={"pk": project.pk})
        data = {"name": "Updated by Admin"}

        with patch("apps.projects.services.invalidate_project_cache"):
            response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_update_project_member_forbidden(self, api_client, project, project_member):
        api_client.force_authenticate(user=project_member)
        url = reverse("project-detail", kwargs={"pk": project.pk})
        data = {"name": "Updated Name"}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProjectDeleteAPI:
    def test_delete_project_owner_success(self, api_client, project, project_owner):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-detail", kwargs={"pk": project.pk})
        project_id = project.id

        with patch("apps.projects.services.invalidate_project_cache"):
            with patch("apps.projects.services.invalidate_membership_cache"):
                response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(id=project_id).exists()

    def test_delete_project_admin_forbidden(self, api_client, project, project_admin):
        api_client.force_authenticate(user=project_admin)
        url = reverse("project-detail", kwargs={"pk": project.pk})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProjectArchiveAPI:
    def test_archive_project_owner_success(self, api_client, project, project_owner):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-archive", kwargs={"pk": project.pk})

        with patch("apps.projects.services.invalidate_project_cache"):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == Project.Status.ARCHIVED

    def test_archive_project_admin_success(self, api_client, project, project_admin):
        api_client.force_authenticate(user=project_admin)
        url = reverse("project-archive", kwargs={"pk": project.pk})

        with patch("apps.projects.services.invalidate_project_cache"):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProjectMembersAPI:
    def test_list_members_success(self, api_client, project_with_members):
        project, members = project_with_members
        api_client.force_authenticate(user=project.owner)
        url = reverse("project-members", kwargs={"pk": project.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_add_member_success(self, api_client, project, project_owner):
        new_user = UserFactory(is_verified=True)
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-add-member", kwargs={"pk": project.pk})
        data = {"user_id": new_user.id, "role": ProjectMember.Role.MEMBER}

        with patch("apps.projects.services.invalidate_membership_cache"):
            with patch("apps.projects.services.send_project_invitation_email.delay"):
                response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert ProjectMember.objects.filter(project=project, user=new_user).exists()

    def test_add_member_duplicate_conflict(
        self, api_client, project, project_owner, project_member
    ):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-add-member", kwargs={"pk": project.pk})
        data = {"user_id": project_member.id, "role": ProjectMember.Role.MEMBER}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
class TestProjectMemberDetailAPI:
    def test_update_member_role_success(self, api_client, project, project_owner, project_member):
        api_client.force_authenticate(user=project_owner)
        url = reverse(
            "project-member-detail", kwargs={"pk": project.pk, "user_id": project_member.id}
        )
        data = {"role": ProjectMember.Role.ADMIN}

        with patch("apps.projects.services.invalidate_membership_cache"):
            with patch("apps.projects.services.send_role_changed_email.delay"):
                response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        membership = ProjectMember.objects.get(project=project, user=project_member)
        assert membership.role == ProjectMember.Role.ADMIN

    def test_remove_member_success(self, api_client, project, project_owner, project_member):
        api_client.force_authenticate(user=project_owner)
        url = reverse(
            "project-member-detail", kwargs={"pk": project.pk, "user_id": project_member.id}
        )

        with patch("apps.projects.services.invalidate_membership_cache"):
            with patch("apps.projects.services.send_removed_from_project_email.delay"):
                response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectMember.objects.filter(project=project, user=project_member).exists()


@pytest.mark.django_db
class TestProjectLeaveAPI:
    def test_leave_project_member_success(self, api_client, project, project_member):
        api_client.force_authenticate(user=project_member)
        url = reverse("project-leave", kwargs={"pk": project.pk})

        with patch("apps.projects.services.invalidate_membership_cache"):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not ProjectMember.objects.filter(project=project, user=project_member).exists()

    def test_leave_project_owner_forbidden(self, api_client, project, project_owner):
        api_client.force_authenticate(user=project_owner)
        url = reverse("project-leave", kwargs={"pk": project.pk})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProjectPermissions:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (ProjectMember.Role.OWNER, status.HTTP_200_OK),
            (ProjectMember.Role.ADMIN, status.HTTP_200_OK),
            (ProjectMember.Role.MEMBER, status.HTTP_403_FORBIDDEN),
            (ProjectMember.Role.VIEWER, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_update_project_permissions(self, api_client, role, expected_status):
        project = ProjectFactory()
        user = UserFactory(is_verified=True)
        if role != ProjectMember.Role.OWNER:
            ProjectMemberFactory(project=project, user=user, role=role)
        else:
            user = project.owner
        api_client.force_authenticate(user=user)
        url = reverse("project-detail", kwargs={"pk": project.pk})
        data = {"name": "Updated"}

        with patch("apps.projects.services.invalidate_project_cache"):
            response = api_client.patch(url, data)

        assert response.status_code == expected_status
