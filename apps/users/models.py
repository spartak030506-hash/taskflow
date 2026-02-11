import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField("Email", unique=True, db_index=True)
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    bio = models.TextField("О себе", max_length=500, blank=True)
    is_verified = models.BooleanField("Email подтверждён", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
        verbose_name="Пользователь",
    )
    token = models.CharField("Токен", max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает")

    class Meta:
        verbose_name = "Токен верификации email"
        verbose_name_plural = "Токены верификации email"

    def __str__(self):
        return f"Verification token for {self.user.email}"

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user).delete()
        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=24)
        return cls.objects.create(user=user, token=token, expires_at=expires_at)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
        verbose_name="Пользователь",
    )
    token = models.CharField("Токен", max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает")
    is_used = models.BooleanField("Использован", default=False)

    class Meta:
        verbose_name = "Токен сброса пароля"
        verbose_name_plural = "Токены сброса пароля"

    def __str__(self):
        return f"Password reset token for {self.user.email}"

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=1)
        return cls.objects.create(user=user, token=token, expires_at=expires_at)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
