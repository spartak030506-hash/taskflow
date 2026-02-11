from drf_spectacular.utils import OpenApiExample
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects import selectors as project_selectors
from core.api_docs import (
    create_endpoint_schema,
    delete_endpoint_schema,
    list_endpoint_schema,
    retrieve_endpoint_schema,
    update_endpoint_schema,
)
from core.exceptions import NotFoundError

from .. import selectors, services
from ..models import Tag
from .permissions import CanManageTag, CanViewTag
from .serializers import (
    TagCreateSerializer,
    TagDetailSerializer,
    TagListSerializer,
    TagUpdateSerializer,
)


class TagViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления тегами задач.

    Доступ:
    - Просмотр: все участники проекта
    - Создание/редактирование/удаление: admin, owner
    """

    queryset = Tag.objects.all()
    serializer_class = TagDetailSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsAuthenticated(), CanViewTag()]
        if self.action == "retrieve":
            return [IsAuthenticated(), CanViewTag()]
        if self.action == "create":
            return [IsAuthenticated(), CanManageTag()]
        if self.action == "partial_update":
            return [IsAuthenticated(), CanViewTag(), CanManageTag()]
        if self.action == "destroy":
            return [IsAuthenticated(), CanViewTag(), CanManageTag()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return TagListSerializer
        if self.action == "create":
            return TagCreateSerializer
        if self.action == "partial_update":
            return TagUpdateSerializer
        return TagDetailSerializer

    def get_project(self):
        project_id = self.kwargs.get("project_pk")
        return project_selectors.get_by_id(project_id)

    def get_queryset(self):
        project = self.get_project()
        return selectors.filter_by_project(project)

    def get_object(self):
        tag_id = self.kwargs.get("pk")
        tag = selectors.get_by_id(tag_id)

        project_id = self.kwargs.get("project_pk")
        if tag.project_id != int(project_id):
            raise NotFoundError("Тег не найден в этом проекте")

        self.check_object_permissions(self.request, tag)
        return tag

    @list_endpoint_schema(
        summary="Список тегов проекта",
        description="Возвращает список всех тегов проекта.",
        tags=["tags"],
    )
    def list(self, request, project_pk=None):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @create_endpoint_schema(
        summary="Создать тег",
        description="Создаёт новый тег для проекта. Имя должно быть уникальным в рамках проекта. Доступно admin и owner.",
        tags=["tags"],
        request_examples=[
            OpenApiExample(
                name="CreateTagRequest",
                value={"name": "bug", "color": "#FF5733"},
                request_only=True,
            ),
        ],
    )
    def create(self, request, project_pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = self.get_project()
        tag = services.create_tag(
            project=project,
            **serializer.validated_data,
        )
        tag = selectors.get_by_id(tag.id)
        return Response(
            TagDetailSerializer(tag).data,
            status=status.HTTP_201_CREATED,
        )

    @retrieve_endpoint_schema(
        summary="Детали тега",
        description="Возвращает подробную информацию о теге.",
        tags=["tags"],
    )
    def retrieve(self, request, project_pk=None, pk=None):
        tag = self.get_object()
        serializer = TagDetailSerializer(tag)
        return Response(serializer.data)

    @update_endpoint_schema(
        summary="Обновить тег",
        description="Обновляет информацию о теге. Доступно admin и owner.",
        tags=["tags"],
        request_examples=[
            OpenApiExample(
                name="UpdateTagRequest",
                value={"name": "critical-bug", "color": "#DC2626"},
                request_only=True,
            ),
        ],
    )
    def partial_update(self, request, project_pk=None, pk=None):
        tag = self.get_object()
        serializer = TagUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_tag(tag=tag, **serializer.validated_data)
        tag = selectors.get_by_id(tag.id)
        return Response(TagDetailSerializer(tag).data)

    @delete_endpoint_schema(
        summary="Удалить тег",
        description="Удаляет тег. Тег автоматически убирается из всех задач. Доступно admin и owner.",
        tags=["tags"],
    )
    def destroy(self, request, project_pk=None, pk=None):
        tag = self.get_object()
        services.delete_tag(tag=tag)
        return Response(status=status.HTTP_204_NO_CONTENT)
