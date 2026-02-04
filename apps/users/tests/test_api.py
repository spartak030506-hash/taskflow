import pytest
from unittest.mock import patch
from rest_framework import status
from django.urls import reverse

from apps.users.models import User
from .factories import UserFactory


@pytest.mark.django_db
class TestRegisterAPI:
    def test_register_success(self, api_client):
        url = reverse('auth-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }

        with patch('apps.users.services.send_verification_email.delay'):
            response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newuser@example.com'
        assert User.objects.filter(email='newuser@example.com').exists()

    def test_register_duplicate_email(self, api_client):
        UserFactory(email='existing@example.com')
        url = reverse('auth-register')
        data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_register_invalid_data(self, api_client):
        url = reverse('auth-register')
        data = {
            'email': 'invalid-email',
            'password': '123',
            'first_name': '',
            'last_name': '',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestVerifyEmailAPI:
    def test_verify_email_success(self, api_client, user_with_verification_token):
        user, token = user_with_verification_token
        url = reverse('auth-verify-email')
        data = {'token': token.token}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_verified is True

    def test_verify_email_invalid_token(self, api_client):
        url = reverse('auth-verify-email')
        data = {'token': 'invalid-token'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_verify_email_expired_token(self, api_client, user_with_expired_verification_token):
        user, token = user_with_expired_verification_token
        url = reverse('auth-verify-email')
        data = {'token': token.token}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestResendVerificationAPI:
    def test_resend_verification_success(self, api_client, unverified_user):
        api_client.force_authenticate(user=unverified_user)
        url = reverse('auth-resend-verification')

        with patch('apps.users.services.send_verification_email.delay'):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

    def test_resend_verification_unauthenticated(self, api_client):
        url = reverse('auth-resend-verification')

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_resend_verification_already_verified(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('auth-resend-verification')

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordResetAPI:
    def test_password_reset_request_success(self, api_client, verified_user):
        url = reverse('auth-password-reset')
        data = {'email': verified_user.email}

        with patch('apps.users.services.send_password_reset_email.delay'):
            response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_nonexistent_email(self, api_client):
        url = reverse('auth-password-reset')
        data = {'email': 'nonexistent@example.com'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_success(self, api_client, user_with_password_reset_token):
        user, token = user_with_password_reset_token
        url = reverse('auth-password-reset-confirm')
        data = {
            'token': token.token,
            'new_password': 'NewSecurePass456!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('NewSecurePass456!')

    def test_password_reset_confirm_invalid_token(self, api_client):
        url = reverse('auth-password-reset-confirm')
        data = {
            'token': 'invalid-token',
            'new_password': 'NewSecurePass456!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserListAPI:
    def test_list_users_admin_success(self, api_client, admin_user):
        UserFactory.create_batch(3)
        api_client.force_authenticate(user=admin_user)
        url = reverse('users-list')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_users_non_admin_forbidden(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-list')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserDetailAPI:
    def test_retrieve_own_user_success(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-detail', kwargs={'pk': verified_user.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == verified_user.email

    def test_retrieve_other_user_forbidden(self, api_client, verified_user):
        other_user = UserFactory()
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-detail', kwargs={'pk': other_user.pk})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserUpdateAPI:
    def test_update_own_user_success(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-detail', kwargs={'pk': verified_user.pk})
        data = {'first_name': 'UpdatedName'}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'UpdatedName'

    def test_update_other_user_forbidden(self, api_client, verified_user):
        other_user = UserFactory()
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-detail', kwargs={'pk': other_user.pk})
        data = {'first_name': 'UpdatedName'}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserMeAPI:
    def test_me_success(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-me')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == verified_user.email

    def test_me_unauthenticated(self, api_client):
        url = reverse('users-me')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChangePasswordAPI:
    def test_change_password_success(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-change-password')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewSecurePass456!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        verified_user.refresh_from_db()
        assert verified_user.check_password('NewSecurePass456!')

    def test_change_password_wrong_old_password(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)
        url = reverse('users-change-password')
        data = {
            'old_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass456!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
