from django.core.validators import RegexValidator
from django.db import models

from apps.projects.models import Project
from core.mixins import TimestampMixin


class Tag(TimestampMixin, models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tags",
        verbose_name="Проект",
    )
    name = models.CharField("Название", max_length=50)
    color = models.CharField(
        "Цвет",
        max_length=7,
        default="#6B7280",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Цвет должен быть в формате HEX (#RRGGBB)",
            ),
        ],
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_tag_name_per_project",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "name"]),
        ]

    def __str__(self):
        return self.name
