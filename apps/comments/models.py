from django.conf import settings
from django.db import models

from apps.tasks.models import Task
from core.mixins import TimestampMixin


class Comment(TimestampMixin, models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    content = models.TextField('Содержимое')
    is_edited = models.BooleanField('Редактировалось', default=False)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f'Comment {self.id} by {self.author_id} on task {self.task_id}'
