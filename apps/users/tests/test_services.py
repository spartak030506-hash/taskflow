import pytest
from unittest.mock import patch

from apps.users import services
from apps.users.models import EmailVerificationToken, PasswordResetToken
from core.exceptions import ValidationError, ConflictError, NotFoundError
from .factories import UserFactory, EmailVerificationTokenFactory, PasswordResetTokenFactory


@pytest.mark.django_db
class TestRegisterUser:
    @pytest.mark.django_db(transaction=True)
    def test_register_user_success(self):
        with patch('apps.users.services.send_verification_email.delay') as mock_task:
            user = services.register_user(
                email='test@example.com',
                password='SecurePass123!',
                first_name='John',
                last_name='Doe',
            )

        assert user.email == 'test@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.is_verified is False
        assert user.check_password('SecurePass123!')
        mock_task.assert_called_once_with(user.id)

    def test_register_user_lowercase_email(self):
        with patch('apps.users.services.send_verification_email.delay'):
            user = services.register_user(
                email='TEST@EXAMPLE.COM',
                password='SecurePass123!',
                first_name='John',
                last_name='Doe',
            )

        assert user.email == 'test@example.com'

    def test_register_user_creates_verification_token(self):
        with patch('apps.users.services.send_verification_email.delay'):
            user = services.register_user(
                email='test@example.com',
                password='SecurePass123!',
                first_name='John',
                last_name='Doe',
            )

        assert EmailVerificationToken.objects.filter(user=user).exists()

    def test_register_user_duplicate_email_raises(self):
        UserFactory(email='existing@example.com')

        with pytest.raises(ConflictError) as exc_info:
            services.register_user(
                email='existing@example.com',
                password='SecurePass123!',
                first_name='John',
                last_name='Doe',
            )

        assert 'уже существует' in str(exc_info.value)

    def test_register_user_weak_password_raises(self):
        with pytest.raises(ValidationError):
            services.register_user(
                email='test@example.com',
                password='123',
                first_name='John',
                last_name='Doe',
            )


@pytest.mark.django_db
class TestVerifyEmail:
    def test_verify_email_success(self, user_with_verification_token):
        user, token = user_with_verification_token
        assert user.is_verified is False

        result = services.verify_email(token=token.token)

        assert result.is_verified is True
        assert not EmailVerificationToken.objects.filter(token=token.token).exists()

    def test_verify_email_expired_token_raises(self, user_with_expired_verification_token):
        user, token = user_with_expired_verification_token

        with pytest.raises(ValidationError) as exc_info:
            services.verify_email(token=token.token)

        assert 'истёк' in str(exc_info.value)

    def test_verify_email_already_verified_raises(self, user_with_verification_token):
        user, token = user_with_verification_token
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        with pytest.raises(ValidationError) as exc_info:
            services.verify_email(token=token.token)

        assert 'уже подтверждён' in str(exc_info.value)

    def test_verify_email_invalid_token_raises(self):
        with pytest.raises(NotFoundError):
            services.verify_email(token='invalid-token')


@pytest.mark.django_db
class TestResendVerificationEmail:
    @pytest.mark.django_db(transaction=True)
    def test_resend_verification_email_success(self, unverified_user):
        with patch('apps.users.services.send_verification_email.delay') as mock_task:
            services.resend_verification_email(user=unverified_user)

        mock_task.assert_called_once_with(unverified_user.id)
        assert EmailVerificationToken.objects.filter(user=unverified_user).exists()

    def test_resend_verification_email_already_verified_raises(self, verified_user):
        with pytest.raises(ValidationError) as exc_info:
            services.resend_verification_email(user=verified_user)

        assert 'уже подтверждён' in str(exc_info.value)


@pytest.mark.django_db
class TestUpdateProfile:
    def test_update_profile_single_field(self, verified_user):
        result = services.update_profile(user=verified_user, first_name='NewName')

        assert result.first_name == 'NewName'

    def test_update_profile_multiple_fields(self, verified_user):
        result = services.update_profile(
            user=verified_user,
            first_name='NewFirst',
            last_name='NewLast',
            phone='+1234567890',
            bio='My bio',
        )

        assert result.first_name == 'NewFirst'
        assert result.last_name == 'NewLast'
        assert result.phone == '+1234567890'
        assert result.bio == 'My bio'

    def test_update_profile_partial_update(self, verified_user):
        old_last_name = verified_user.last_name
        result = services.update_profile(user=verified_user, first_name='OnlyFirst')

        assert result.first_name == 'OnlyFirst'
        assert result.last_name == old_last_name


@pytest.mark.django_db
class TestChangePassword:
    def test_change_password_success(self, verified_user):
        old_password = 'TestPass123!'
        new_password = 'NewSecurePass456!'

        result = services.change_password(
            user=verified_user,
            old_password=old_password,
            new_password=new_password,
        )

        assert result.check_password(new_password)
        assert not result.check_password(old_password)

    def test_change_password_wrong_old_password_raises(self, verified_user):
        with pytest.raises(ValidationError) as exc_info:
            services.change_password(
                user=verified_user,
                old_password='WrongPassword123!',
                new_password='NewSecurePass456!',
            )

        assert 'Неверный' in str(exc_info.value)

    def test_change_password_weak_new_password_raises(self, verified_user):
        with pytest.raises(ValidationError):
            services.change_password(
                user=verified_user,
                old_password='TestPass123!',
                new_password='123',
            )


@pytest.mark.django_db
class TestRequestPasswordReset:
    @pytest.mark.django_db(transaction=True)
    def test_request_password_reset_success(self, verified_user):
        with patch('apps.users.services.send_password_reset_email.delay') as mock_task:
            services.request_password_reset(email=verified_user.email)

        mock_task.assert_called_once_with(verified_user.id)
        assert PasswordResetToken.objects.filter(user=verified_user).exists()

    def test_request_password_reset_nonexistent_email_silent(self):
        with patch('apps.users.services.send_password_reset_email.delay') as mock_task:
            services.request_password_reset(email='nonexistent@example.com')

        mock_task.assert_not_called()

    def test_request_password_reset_inactive_user_silent(self):
        user = UserFactory(is_active=False)

        with patch('apps.users.services.send_password_reset_email.delay') as mock_task:
            services.request_password_reset(email=user.email)

        mock_task.assert_not_called()


@pytest.mark.django_db
class TestResetPassword:
    def test_reset_password_success(self, user_with_password_reset_token):
        user, token = user_with_password_reset_token
        new_password = 'NewSecurePass456!'

        result = services.reset_password(
            token=token.token,
            new_password=new_password,
        )

        assert result.check_password(new_password)
        token.refresh_from_db()
        assert token.is_used is True

    def test_reset_password_used_token_raises(self, user_with_used_password_reset_token):
        user, token = user_with_used_password_reset_token

        with pytest.raises(ValidationError) as exc_info:
            services.reset_password(
                token=token.token,
                new_password='NewSecurePass456!',
            )

        assert 'недействителен' in str(exc_info.value)

    def test_reset_password_expired_token_raises(self, user_with_expired_password_reset_token):
        user, token = user_with_expired_password_reset_token

        with pytest.raises(ValidationError) as exc_info:
            services.reset_password(
                token=token.token,
                new_password='NewSecurePass456!',
            )

        assert 'недействителен' in str(exc_info.value)

    def test_reset_password_weak_password_raises(self, user_with_password_reset_token):
        user, token = user_with_password_reset_token

        with pytest.raises(ValidationError):
            services.reset_password(
                token=token.token,
                new_password='123',
            )

    def test_reset_password_invalid_token_raises(self):
        with pytest.raises(NotFoundError):
            services.reset_password(
                token='invalid-token',
                new_password='NewSecurePass456!',
            )
