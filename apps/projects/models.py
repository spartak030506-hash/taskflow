from django.conf import settings
from django.db import models

from core.mixins import TimestampMixin


class Project(TimestampMixin, models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активный"
        ARCHIVED = "archived", "Архивирован"
        COMPLETED = "completed", "Завершён"

    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Владелец"
        ADMIN = "admin", "Администратор"
        MEMBER = "member", "Участник"
        VIEWER = "viewer", "Наблюдатель"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="Проект",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        verbose_name="Пользователь",
    )
    role = models.CharField(
        "Роль",
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField("Дата вступления", auto_now_add=True)

    class Meta:
        verbose_name = "Участник проекта"
        verbose_name_plural = "Участники проекта"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_member",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "role"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.project} ({self.get_role_display()})"
