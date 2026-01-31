from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users import selectors as user_selectors

from . import selectors, services
from .models import Project
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

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = services.create_project(
            owner=request.user,
            **serializer.validated_data,
        )
        project = selectors.get_by_id(project.id)
        return Response(
            ProjectDetailSerializer(project).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_project(
            project=project,
            **serializer.validated_data,
        )
        project = selectors.get_by_id(project.id)
        return Response(ProjectDetailSerializer(project).data)

    def destroy(self, request, pk=None):
        project = self.get_object()
        services.delete_project(project=project)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        project = self.get_object()
        services.archive_project(project=project)
        project = selectors.get_by_id(project.id)
        return Response(ProjectDetailSerializer(project).data)

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

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        project = self.get_object()
        services.leave_project(project=project, user=request.user)
        return Response({'detail': 'Вы покинули проект'})
