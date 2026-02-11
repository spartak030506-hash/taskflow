from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects import selectors as project_selectors
from apps.tags import services as tag_services
from apps.users import selectors as user_selectors
from core.api_docs import (
    action_endpoint_schema,
    create_endpoint_schema,
    delete_endpoint_schema,
    list_endpoint_schema,
    retrieve_endpoint_schema,
    update_endpoint_schema,
)
from core.exceptions import NotFoundError

from .. import selectors, services
from ..models import Task
from .permissions import CanCreateTask, CanDeleteTask, CanEditTask, CanViewTask
from .serializers import (
    TaskAssignSerializer,
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskReorderSerializer,
    TaskSetTagsSerializer,
    TaskStatusSerializer,
    TaskUpdateSerializer,
)


class TaskViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления задачами внутри проектов.

    Доступ:
    - Просмотр: все участники проекта
    - Создание: member, admin, owner (не viewer)
    - Редактирование: creator, assignee, admin, owner
    - Удаление: creator, admin, owner
    """

    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsAuthenticated(), CanViewTask()]
        if self.action == "create":
            return [IsAuthenticated(), CanCreateTask()]
        if self.action == "retrieve":
            return [IsAuthenticated(), CanViewTask()]
        if self.action == "partial_update":
            return [IsAuthenticated(), CanViewTask(), CanEditTask()]
        if self.action == "destroy":
            return [IsAuthenticated(), CanViewTask(), CanDeleteTask()]
        if self.action in ["change_status", "assign", "reorder", "set_tags"]:
            return [IsAuthenticated(), CanViewTask(), CanEditTask()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        if self.action == "create":
            return TaskCreateSerializer
        if self.action == "partial_update":
            return TaskUpdateSerializer
        if self.action == "change_status":
            return TaskStatusSerializer
        if self.action == "assign":
            return TaskAssignSerializer
        if self.action == "reorder":
            return TaskReorderSerializer
        if self.action == "set_tags":
            return TaskSetTagsSerializer
        return TaskDetailSerializer

    def get_project(self):
        project_id = self.kwargs.get("project_pk")
        return project_selectors.get_by_id(project_id)

    def get_queryset(self):
        project = self.get_project()
        task_status = self.request.query_params.get("status")
        task_priority = self.request.query_params.get("priority")
        assignee_id = self.request.query_params.get("assignee_id")

        if assignee_id:
            try:
                assignee_id = int(assignee_id)
            except ValueError:
                assignee_id = None

        return selectors.filter_by_project_with_filters(
            project=project,
            status=task_status,
            priority=task_priority,
            assignee_id=assignee_id,
        )

    def get_object(self):
        task_id = self.kwargs.get("pk")
        task = selectors.get_by_id(task_id)

        project_id = self.kwargs.get("project_pk")
        if task.project_id != int(project_id):
            raise NotFoundError("Задача не найдена в этом проекте")

        self.check_object_permissions(self.request, task)
        return task

    def _validate_assignee(self, assignee_id, project):
        assignee = user_selectors.get_by_id(assignee_id)
        if not project_selectors.exists_member(project, assignee):
            raise ValidationError({"assignee_id": "Пользователь не является участником проекта"})
        return assignee

    @list_endpoint_schema(
        summary="Список задач проекта",
        description="Возвращает список задач проекта с фильтрацией по статусу, приоритету и исполнителю.",
        tags=["tasks"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Фильтр по статусу (pending, in_progress, completed, cancelled)",
                required=False,
            ),
            OpenApiParameter(
                name="priority",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Фильтр по приоритету (low, medium, high, urgent)",
                required=False,
            ),
            OpenApiParameter(
                name="assignee_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Фильтр по ID исполнителя",
                required=False,
            ),
        ],
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
        summary="Создать задачу",
        description="Создаёт новую задачу в проекте. Доступно member, admin, owner (не viewer).",
        tags=["tasks"],
        request_examples=[
            OpenApiExample(
                name="CreateTaskRequest",
                value={
                    "title": "Новая задача",
                    "description": "Описание задачи",
                    "priority": "high",
                    "deadline": "2024-12-31T23:59:59Z",
                    "assignee_id": 2,
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, project_pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = self.get_project()
        data = serializer.validated_data.copy()

        assignee = None
        assignee_id = data.pop("assignee_id", None)
        if assignee_id:
            assignee = self._validate_assignee(assignee_id, project)

        task = services.create_task(
            project=project,
            creator=request.user,
            assignee=assignee,
            **data,
        )
        task = selectors.get_by_id(task.id)
        return Response(
            TaskDetailSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )

    @retrieve_endpoint_schema(
        summary="Детали задачи",
        description="Возвращает подробную информацию о задаче.",
        tags=["tasks"],
    )
    def retrieve(self, request, project_pk=None, pk=None):
        task = self.get_object()
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)

    @update_endpoint_schema(
        summary="Обновить задачу",
        description="Обновляет информацию о задаче. Доступно creator, assignee, admin, owner.",
        tags=["tasks"],
        request_examples=[
            OpenApiExample(
                name="UpdateTaskRequest",
                value={"title": "Обновлённое название", "priority": "urgent"},
                request_only=True,
            ),
        ],
    )
    def partial_update(self, request, project_pk=None, pk=None):
        task = self.get_object()
        serializer = TaskUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_task(task=task, updated_by=request.user, **serializer.validated_data)
        task = selectors.get_by_id(task.id)
        return Response(TaskDetailSerializer(task).data)

    @delete_endpoint_schema(
        summary="Удалить задачу",
        description="Удаляет задачу. Доступно creator, admin, owner.",
        tags=["tasks"],
    )
    def destroy(self, request, project_pk=None, pk=None):
        task = self.get_object()
        services.delete_task(task=task, deleted_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action_endpoint_schema(
        summary="Изменить статус задачи",
        description="Изменяет статус задачи. Доступно creator, assignee, admin, owner.",
        tags=["tasks"],
        method="POST",
        request_examples=[
            OpenApiExample(
                name="ChangeStatusRequest",
                value={"status": "in_progress"},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, project_pk=None, pk=None):
        task = self.get_object()
        serializer = TaskStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.change_status(
            task=task,
            new_status=serializer.validated_data["status"],
            updated_by=request.user,
        )
        task = selectors.get_by_id(task.id)
        return Response(TaskDetailSerializer(task).data)

    @action_endpoint_schema(
        summary="Назначить исполнителя",
        description="Назначает или снимает исполнителя задачи. Доступно creator, assignee, admin, owner.",
        tags=["tasks"],
        method="POST",
        request_examples=[
            OpenApiExample(
                name="AssignTaskRequest",
                value={"assignee_id": 2},
                request_only=True,
            ),
            OpenApiExample(
                name="UnassignTaskRequest",
                value={"assignee_id": None},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    def assign(self, request, project_pk=None, pk=None):
        task = self.get_object()
        serializer = TaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = self.get_project()
        assignee = None
        assignee_id = serializer.validated_data["assignee_id"]
        if assignee_id:
            assignee = self._validate_assignee(assignee_id, project)

        services.assign_task(
            task=task,
            assignee=assignee,
            project_name=project.name,
            updated_by=request.user,
        )
        task = selectors.get_by_id(task.id)
        return Response(TaskDetailSerializer(task).data)

    @action_endpoint_schema(
        summary="Изменить позицию задачи",
        description="Изменяет позицию задачи в списке. Доступно creator, assignee, admin, owner.",
        tags=["tasks"],
        method="POST",
        request_examples=[
            OpenApiExample(
                name="ReorderTaskRequest",
                value={"position": 0},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    def reorder(self, request, project_pk=None, pk=None):
        task = self.get_object()
        serializer = TaskReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.reorder_task(
            task=task,
            new_position=serializer.validated_data["position"],
            updated_by=request.user,
        )
        task = selectors.get_by_id(task.id)
        return Response(TaskDetailSerializer(task).data)

    @action_endpoint_schema(
        summary="Установить теги задачи",
        description="Устанавливает список тегов для задачи. Максимум 20 тегов. Доступно creator, assignee, admin, owner.",
        tags=["tasks"],
        method="POST",
        request_examples=[
            OpenApiExample(
                name="SetTagsRequest",
                value={"tag_ids": [1, 2, 3]},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    def set_tags(self, request, project_pk=None, pk=None):
        task = self.get_object()
        serializer = TaskSetTagsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag_services.set_task_tags(
            task=task,
            tag_ids=serializer.validated_data["tag_ids"],
            updated_by=request.user,
        )
        task = selectors.get_by_id(task.id)
        return Response(TaskDetailSerializer(task).data)
