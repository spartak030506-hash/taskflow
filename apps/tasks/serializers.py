from rest_framework import serializers

from apps.users.serializers import UserListSerializer

from .models import Task


class TaskListSerializer(serializers.ModelSerializer):
    creator = UserListSerializer(read_only=True)
    assignee = UserListSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'status',
            'priority',
            'deadline',
            'position',
            'creator',
            'assignee',
            'created_at',
        ]
        read_only_fields = fields


class TaskDetailSerializer(serializers.ModelSerializer):
    creator = UserListSerializer(read_only=True)
    assignee = UserListSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'project_id',
            'title',
            'description',
            'status',
            'priority',
            'deadline',
            'position',
            'creator',
            'assignee',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class TaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    priority = serializers.ChoiceField(
        choices=Task.Priority.choices,
        default=Task.Priority.MEDIUM,
    )
    deadline = serializers.DateTimeField(required=False, allow_null=True, default=None)
    assignee_id = serializers.IntegerField(required=False, allow_null=True, default=None)


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(choices=Task.Priority.choices, required=False)
    deadline = serializers.DateTimeField(required=False, allow_null=True)


class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.Status.choices)


class TaskAssignSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField(allow_null=True)


class TaskReorderSerializer(serializers.Serializer):
    position = serializers.IntegerField(min_value=0)
