from rest_framework import serializers

from apps.users.serializers import UserListSerializer

from .models import Project, ProjectMember


class ProjectListSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'status',
            'owner_id',
            'members_count',
            'created_at',
        ]
        read_only_fields = fields


class ProjectDetailSerializer(serializers.ModelSerializer):
    owner = UserListSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'status',
            'owner',
            'members_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_members_count(self, obj) -> int:
        if hasattr(obj, 'members_count'):
            return obj.members_count
        return obj.members.count()


class ProjectCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')


class ProjectUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            'id',
            'user',
            'role',
            'joined_at',
        ]
        read_only_fields = fields


class ProjectMemberCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    role = serializers.ChoiceField(
        choices=[
            (ProjectMember.Role.ADMIN, 'Администратор'),
            (ProjectMember.Role.MEMBER, 'Участник'),
            (ProjectMember.Role.VIEWER, 'Наблюдатель'),
        ],
        default=ProjectMember.Role.MEMBER,
    )


class ProjectMemberUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=[
            (ProjectMember.Role.ADMIN, 'Администратор'),
            (ProjectMember.Role.MEMBER, 'Участник'),
            (ProjectMember.Role.VIEWER, 'Наблюдатель'),
        ],
    )
