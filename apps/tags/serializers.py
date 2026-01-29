from rest_framework import serializers

from .models import Tag


class TagMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']
        read_only_fields = fields


class TagListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at']
        read_only_fields = fields


class TagDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'id',
            'project_id',
            'name',
            'color',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class TagCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, min_length=1)
    color = serializers.RegexField(
        regex=r'^#[0-9A-Fa-f]{6}$',
        default='#6B7280',
        help_text='HEX цвет в формате #RRGGBB',
    )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Название тега не может быть пустым')
        return value


class TagUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, min_length=1, required=False)
    color = serializers.RegexField(
        regex=r'^#[0-9A-Fa-f]{6}$',
        required=False,
        help_text='HEX цвет в формате #RRGGBB',
    )

    def validate_name(self, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError('Название тега не может быть пустым')
        return value


class SetTaskTagsSerializer(serializers.Serializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        max_length=20,
    )
