from rest_framework import serializers

from apps.tags.api.serializers import TagMinimalSerializer
from apps.users.api.serializers import UserListSerializer

from ..models import Task


class TaskListSerializer(serializers.ModelSerializer):
    creator = UserListSerializer(read_only=True)
    assignee = UserListSerializer(read_only=True)
    tags = TagMinimalSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "status",
            "priority",
            "deadline",
            "position",
            "creator",
            "assignee",
            "tags",
            "created_at",
        ]
        read_only_fields = fields


class TaskDetailSerializer(serializers.ModelSerializer):
    creator = UserListSerializer(read_only=True)
    assignee = UserListSerializer(read_only=True)
    tags = TagMinimalSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project_id",
            "title",
            "description",
            "status",
            "priority",
            "deadline",
            "position",
            "creator",
            "assignee",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, help_text="Название задачи")
    description = serializers.CharField(
        required=False, allow_blank=True, default="", help_text="Описание задачи"
    )
    priority = serializers.ChoiceField(
        choices=Task.Priority.choices,
        default=Task.Priority.MEDIUM,
        help_text="Приоритет: low, medium, high, urgent",
    )
    deadline = serializers.DateTimeField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Крайний срок выполнения (ISO 8601 формат)",
    )
    assignee_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        help_text="ID пользователя для назначения задачи",
    )


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, help_text="Название задачи")
    description = serializers.CharField(
        required=False, allow_blank=True, help_text="Описание задачи"
    )
    priority = serializers.ChoiceField(
        choices=Task.Priority.choices,
        required=False,
        help_text="Приоритет: low, medium, high, urgent",
    )
    deadline = serializers.DateTimeField(
        required=False, allow_null=True, help_text="Крайний срок выполнения (ISO 8601 формат)"
    )


class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Task.Status.choices, help_text="Статус: pending, in_progress, completed, cancelled"
    )


class TaskAssignSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField(
        allow_null=True, help_text="ID пользователя для назначения (null для снятия назначения)"
    )


class TaskReorderSerializer(serializers.Serializer):
    position = serializers.IntegerField(min_value=0, help_text="Новая позиция задачи (0-based)")


class TaskSetTagsSerializer(serializers.Serializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        max_length=20,
        help_text="Список ID тегов (максимум 20)",
    )
