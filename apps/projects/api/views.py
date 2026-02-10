from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.api_docs import (
    list_endpoint_schema,
    create_endpoint_schema,
    retrieve_endpoint_schema,
    update_endpoint_schema,
    delete_endpoint_schema,
    action_endpoint_schema,
)

from apps.users import selectors as user_selectors

from .. import selectors, services
from ..models import Project
from .permissions import IsProjectAdminOrOwner, IsProjectMember, IsProjectOwner
from .serializers import (
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectMemberCreateSerializer,
    ProjectMemberSerializer,
    ProjectMemberUpdateSerializer,
    ProjectUpdateSerializer,
)


class ProjectViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления проектами.

    Роли участников:
    - owner: полный доступ
    - admin: управление проектом и участниками (кроме удаления)
    - member: просмотр и создание задач
    - viewer: только просмотр
    """
    queryset = Project.objects.all()
    serializer_class = ProjectDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['partial_update', 'archive']:
            return [IsAuthenticated(), IsProjectAdminOrOwner()]
        if self.action == 'destroy':
            return [IsAuthenticated(), IsProjectOwner()]
        if self.action in ['retrieve', 'members', 'leave']:
            return [IsAuthenticated(), IsProjectMember()]
        if self.action in ['member_detail', 'add_member']:
            return [IsAuthenticated(), IsProjectAdminOrOwner()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        if self.action == 'create':
            return ProjectCreateSerializer
        if self.action == 'partial_update':
            return ProjectUpdateSerializer
        return ProjectDetailSerializer

    def get_queryset(self):
        return selectors.filter_for_user_with_members_count(self.request.user)

    def get_object(self):
        project_id = self.kwargs.get('pk')
        project = selectors.get_by_id(project_id)
        self.check_object_permissions(self.request, project)
        return project

    @list_endpoint_schema(
        summary="Список проектов",
        description="Возвращает список проектов пользователя (где он является участником).",
        tags=['projects'],
    )
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @create_endpoint_schema(
        summary="Создать проект",
        description="Создаёт новый проект. Пользователь автоматически становится владельцем (owner).",
        tags=['projects'],
        request_examples=[
            OpenApiExample(
                name='CreateProjectRequest',
                value={'name': 'Новый проект', 'description': 'Описание проекта'},
                request_only=True,
            ),
        ],
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = services.create_project(
            owner=request.user,
            **serializer.validated_data,
        )
        data = selectors.get_detail(project.id)
        return Response(data, status=status.HTTP_201_CREATED)

    @retrieve_endpoint_schema(
        summary="Детали проекта",
        description="Возвращает подробную информацию о проекте.",
        tags=['projects'],
    )
    def retrieve(self, request, pk=None):
        project = self.get_object()
        data = selectors.get_detail(project.id)
        return Response(data)

    @update_endpoint_schema(
        summary="Обновить проект",
        description="Обновляет информацию о проекте. Доступно admin и owner.",
        tags=['projects'],
        request_examples=[
            OpenApiExample(
                name='UpdateProjectRequest',
                value={'name': 'Обновлённое название'},
                request_only=True,
            ),
        ],
    )
    def partial_update(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_project(project=project, **serializer.validated_data)
        data = selectors.get_detail(project.id)
        return Response(data)

    @delete_endpoint_schema(
        summary="Удалить проект",
        description="Удаляет проект. Доступно только owner.",
        tags=['projects'],
    )
    def destroy(self, request, pk=None):
        project = self.get_object()
        services.delete_project(project=project)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action_endpoint_schema(
        summary="Архивировать проект",
        description="Переводит проект в статус 'archived'. Доступно admin и owner.",
        tags=['projects'],
        method='POST',
    )
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        project = self.get_object()
        services.archive_project(project=project)
        data = selectors.get_detail(project.id)
        return Response(data)

    @action_endpoint_schema(
        summary="Список участников проекта",
        description="Возвращает список всех участников проекта с их ролями.",
        tags=['projects'],
        method='GET',
    )
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        project = self.get_object()
        members = selectors.filter_members(project)

        page = self.paginate_queryset(members)
        if page is not None:
            serializer = ProjectMemberSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Добавить участника",
        description="Добавляет нового участника в проект. Доступно admin и owner.",
        tags=['projects'],
        request=ProjectMemberCreateSerializer,
        responses={
            201: ProjectMemberSerializer,
            404: {'description': 'Пользователь не найден'},
            409: {'description': 'Пользователь уже является участником'},
        },
        examples=[
            OpenApiExample(
                name='AddMemberRequest',
                value={'user_id': 2, 'role': 'member'},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=['post'], url_path='members/add')
    def add_member(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectMemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = user_selectors.get_by_id(serializer.validated_data['user_id'])
        member = services.add_member(
            project=project,
            user=user,
            role=serializer.validated_data['role'],
        )
        return Response(
            ProjectMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Управление участником",
        description="Изменение роли (PATCH) или удаление участника (DELETE). Доступно admin и owner.",
        tags=['projects'],
        request=ProjectMemberUpdateSerializer,
        responses={
            200: ProjectMemberSerializer,
            204: {'description': 'Участник удалён'},
            404: {'description': 'Пользователь не найден'},
        },
        examples=[
            OpenApiExample(
                name='UpdateMemberRoleRequest',
                value={'role': 'admin'},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=['patch', 'delete'], url_path='members/(?P<user_id>[^/.]+)')
    def member_detail(self, request, pk=None, user_id=None):
        project = self.get_object()

        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise ValidationError({'user_id': 'Некорректный идентификатор пользователя'})

        user = user_selectors.get_by_id(user_id_int)
        membership = selectors.get_member(project, user)

        if request.method == 'PATCH':
            serializer = ProjectMemberUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            membership = services.update_member_role(
                membership=membership,
                role=serializer.validated_data['role'],
            )
            return Response(ProjectMemberSerializer(membership).data)

        services.remove_member(membership=membership)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action_endpoint_schema(
        summary="Покинуть проект",
        description="Пользователь покидает проект. Владелец не может покинуть проект.",
        tags=['projects'],
        method='POST',
    )
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        project = self.get_object()
        services.leave_project(project=project, user=request.user)
        return Response({'detail': 'Вы покинули проект'})
