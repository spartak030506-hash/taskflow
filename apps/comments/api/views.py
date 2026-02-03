from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects import selectors as project_selectors
from apps.tasks import selectors as task_selectors
from core.exceptions import NotFoundError

from .. import selectors, services
from ..models import Comment
from .permissions import (
    CanCreateComment,
    CanDeleteComment,
    CanEditComment,
    CanViewComment,
)
from .serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentListSerializer,
    CommentUpdateSerializer,
)


class CommentViewSet(viewsets.GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentDetailSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated(), CanViewComment()]
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateComment()]
        if self.action == 'retrieve':
            return [IsAuthenticated(), CanViewComment()]
        if self.action == 'partial_update':
            return [IsAuthenticated(), CanViewComment(), CanEditComment()]
        if self.action == 'destroy':
            return [IsAuthenticated(), CanViewComment(), CanDeleteComment()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CommentListSerializer
        if self.action == 'create':
            return CommentCreateSerializer
        if self.action == 'partial_update':
            return CommentUpdateSerializer
        return CommentDetailSerializer

    def get_project(self):
        project_id = self.kwargs.get('project_pk')
        return project_selectors.get_by_id(project_id)

    def get_task(self):
        task_id = self.kwargs.get('task_pk')
        task = task_selectors.get_by_id(task_id)

        project_id = self.kwargs.get('project_pk')
        if task.project_id != int(project_id):
            raise NotFoundError('Задача не найдена в этом проекте')

        return task

    def get_queryset(self):
        task = self.get_task()
        return selectors.filter_by_task(task)

    def get_object(self):
        comment_id = self.kwargs.get('pk')
        comment = selectors.get_by_id(comment_id)

        task_id = self.kwargs.get('task_pk')
        if comment.task_id != int(task_id):
            raise NotFoundError('Комментарий не найден в этой задаче')

        self.check_object_permissions(self.request, comment)
        return comment

    def list(self, request, project_pk=None, task_pk=None):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, project_pk=None, task_pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = self.get_task()
        comment = services.create_comment(
            task=task,
            author=request.user,
            content=serializer.validated_data['content'],
        )
        comment = selectors.get_by_id(comment.id)
        return Response(
            CommentDetailSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, project_pk=None, task_pk=None, pk=None):
        comment = self.get_object()
        serializer = CommentDetailSerializer(comment)
        return Response(serializer.data)

    def partial_update(self, request, project_pk=None, task_pk=None, pk=None):
        comment = self.get_object()
        serializer = CommentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_comment(
            comment=comment,
            content=serializer.validated_data['content'],
        )
        comment = selectors.get_by_id(comment.id)
        return Response(CommentDetailSerializer(comment).data)

    def destroy(self, request, project_pk=None, task_pk=None, pk=None):
        comment = self.get_object()
        services.delete_comment(comment=comment)
        return Response(status=status.HTTP_204_NO_CONTENT)
