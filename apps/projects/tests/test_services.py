import pytest
from unittest.mock import patch

from apps.projects import services
from apps.projects.models import Project, ProjectMember
from apps.users.tests.factories import UserFactory
from core.exceptions import ValidationError, ConflictError
from .factories import ProjectFactory


@pytest.mark.django_db
class TestCreateProject:
    def test_create_project_success(self):
        owner = UserFactory(is_verified=True)

        project = services.create_project(
            owner=owner,
            name='Test Project',
            description='Test Description',
        )

        assert project.name == 'Test Project'
        assert project.description == 'Test Description'
        assert project.owner == owner
        assert project.status == Project.Status.ACTIVE

    def test_create_project_owner_auto_member(self):
        owner = UserFactory(is_verified=True)

        project = services.create_project(
            owner=owner,
            name='Test Project',
        )

        membership = ProjectMember.objects.get(project=project, user=owner)
        assert membership.role == ProjectMember.Role.OWNER

    def test_create_project_without_description(self):
        owner = UserFactory(is_verified=True)

        project = services.create_project(
            owner=owner,
            name='Test Project',
        )

        assert project.description == ''


@pytest.mark.django_db
class TestUpdateProject:
    @pytest.mark.django_db(transaction=True)
    def test_update_project_name(self, project):
        with patch('apps.projects.services.invalidate_project_cache') as mock_cache:
            result = services.update_project(project=project, name='New Name')

        assert result.name == 'New Name'
        mock_cache.assert_called_once_with(project.id)

    def test_update_project_description(self, project):
        with patch('apps.projects.services.invalidate_project_cache'):
            result = services.update_project(
                project=project,
                description='New Description'
            )

        assert result.description == 'New Description'

    def test_update_project_multiple_fields(self, project):
        with patch('apps.projects.services.invalidate_project_cache'):
            result = services.update_project(
                project=project,
                name='New Name',
                description='New Description',
            )

        assert result.name == 'New Name'
        assert result.description == 'New Description'


@pytest.mark.django_db
class TestDeleteProject:
    @pytest.mark.django_db(transaction=True)
    def test_delete_project_success(self, project):
        project_id = project.id

        with patch('apps.projects.services.invalidate_project_cache') as mock_cache:
            with patch('apps.projects.services.invalidate_membership_cache'):
                services.delete_project(project=project)

        assert not Project.objects.filter(id=project_id).exists()
        mock_cache.assert_called_once_with(project_id)


@pytest.mark.django_db
class TestArchiveProject:
    @pytest.mark.django_db(transaction=True)
    def test_archive_project_success(self, project):
        with patch('apps.projects.services.invalidate_project_cache') as mock_cache:
            result = services.archive_project(project=project)

        assert result.status == Project.Status.ARCHIVED
        mock_cache.assert_called_once_with(project.id)


@pytest.mark.django_db
class TestAddMember:
    @pytest.mark.django_db(transaction=True)
    def test_add_member_success(self, project):
        new_user = UserFactory(is_verified=True)

        with patch('apps.projects.services.invalidate_membership_cache'):
            with patch('apps.projects.services.send_project_invitation_email.delay') as mock_email:
                member = services.add_member(
                    project=project,
                    user=new_user,
                    role=ProjectMember.Role.MEMBER,
                )

        assert member.user == new_user
        assert member.project == project
        assert member.role == ProjectMember.Role.MEMBER
        mock_email.assert_called_once()

    def test_add_member_as_admin(self, project):
        new_user = UserFactory(is_verified=True)

        with patch('apps.projects.services.invalidate_membership_cache'):
            with patch('apps.projects.services.send_project_invitation_email.delay'):
                member = services.add_member(
                    project=project,
                    user=new_user,
                    role=ProjectMember.Role.ADMIN,
                )

        assert member.role == ProjectMember.Role.ADMIN

    def test_add_member_duplicate_raises(self, project, project_member):
        with pytest.raises(ConflictError) as exc_info:
            services.add_member(
                project=project,
                user=project_member,
                role=ProjectMember.Role.MEMBER,
            )

        assert 'уже является' in str(exc_info.value)

    def test_add_member_as_owner_raises(self, project):
        new_user = UserFactory(is_verified=True)

        with pytest.raises(ValidationError) as exc_info:
            services.add_member(
                project=project,
                user=new_user,
                role=ProjectMember.Role.OWNER,
            )

        assert 'владельца' in str(exc_info.value)

    @pytest.mark.django_db(transaction=True)
    def test_add_member_invalidates_cache(self, project):
        new_user = UserFactory(is_verified=True)

        with patch('apps.projects.services.invalidate_membership_cache') as mock_cache:
            with patch('apps.projects.services.send_project_invitation_email.delay'):
                services.add_member(
                    project=project,
                    user=new_user,
                )

        mock_cache.assert_called_once_with(project.id, new_user.id)


@pytest.mark.django_db
class TestUpdateMemberRole:
    @pytest.mark.django_db(transaction=True)
    def test_update_member_role_success(self, project, project_member):
        membership = ProjectMember.objects.get(project=project, user=project_member)

        with patch('apps.projects.services.invalidate_membership_cache'):
            with patch('apps.projects.services.send_role_changed_email.delay') as mock_email:
                result = services.update_member_role(
                    membership=membership,
                    role=ProjectMember.Role.ADMIN,
                )

        assert result.role == ProjectMember.Role.ADMIN
        mock_email.assert_called_once()

    def test_update_owner_role_raises(self, project, project_owner):
        membership = ProjectMember.objects.get(project=project, user=project_owner)

        with pytest.raises(ValidationError) as exc_info:
            services.update_member_role(
                membership=membership,
                role=ProjectMember.Role.ADMIN,
            )

        assert 'владельца' in str(exc_info.value)

    def test_update_to_owner_role_raises(self, project, project_member):
        membership = ProjectMember.objects.get(project=project, user=project_member)

        with pytest.raises(ValidationError) as exc_info:
            services.update_member_role(
                membership=membership,
                role=ProjectMember.Role.OWNER,
            )

        assert 'владельца' in str(exc_info.value)


@pytest.mark.django_db
class TestRemoveMember:
    @pytest.mark.django_db(transaction=True)
    def test_remove_member_success(self, project, project_member):
        membership = ProjectMember.objects.get(project=project, user=project_member)

        with patch('apps.projects.services.invalidate_membership_cache'):
            with patch('apps.projects.services.send_removed_from_project_email.delay') as mock_email:
                services.remove_member(membership=membership)

        assert not ProjectMember.objects.filter(
            project=project, user=project_member
        ).exists()
        mock_email.assert_called_once()

    def test_remove_owner_raises(self, project, project_owner):
        membership = ProjectMember.objects.get(project=project, user=project_owner)

        with pytest.raises(ValidationError) as exc_info:
            services.remove_member(membership=membership)

        assert 'владельца' in str(exc_info.value)


@pytest.mark.django_db
class TestLeaveProject:
    def test_leave_project_success(self, project, project_member):
        with patch('apps.projects.services.invalidate_membership_cache'):
            services.leave_project(project=project, user=project_member)

        assert not ProjectMember.objects.filter(
            project=project, user=project_member
        ).exists()

    def test_leave_project_owner_raises(self, project, project_owner):
        with pytest.raises(ValidationError) as exc_info:
            services.leave_project(project=project, user=project_owner)

        assert 'Владелец' in str(exc_info.value)
