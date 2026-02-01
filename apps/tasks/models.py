from django.conf import settings
from django.db import models

from apps.projects.models import Project
from core.mixins import TimestampMixin


class Task(TimestampMixin, models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Завершена'
        CANCELLED = 'cancelled', 'Отменена'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
        URGENT = 'urgent', 'Срочный'

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Проект',
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name='Создатель',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Исполнитель',
    )
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        'Приоритет',
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    deadline = models.DateTimeField('Дедлайн', null=True, blank=True)
    position = models.PositiveIntegerField('Позиция', default=0)
    tags = models.ManyToManyField(
        'tags.Tag',
        blank=True,
        related_name='tasks',
        verbose_name='Теги',
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['position', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['project', 'assignee']),
            models.Index(fields=['project', 'position']),
            models.Index(fields=['deadline']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title
