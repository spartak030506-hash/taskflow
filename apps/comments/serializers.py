from rest_framework import serializers

from apps.users.serializers import UserListSerializer

from .models import Comment


class CommentListSerializer(serializers.ModelSerializer):
    author = UserListSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'author',
            'content',
            'is_edited',
            'created_at',
        ]
        read_only_fields = fields


class CommentDetailSerializer(serializers.ModelSerializer):
    author = UserListSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'task_id',
            'author',
            'content',
            'is_edited',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=10000)


class CommentUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=10000)
