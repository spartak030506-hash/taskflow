from django.urls import path

from .views import TaskViewSet

task_list = TaskViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

task_detail = TaskViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

task_status = TaskViewSet.as_view(
    {
        "post": "change_status",
    }
)

task_assign = TaskViewSet.as_view(
    {
        "post": "assign",
    }
)

task_reorder = TaskViewSet.as_view(
    {
        "post": "reorder",
    }
)

task_set_tags = TaskViewSet.as_view(
    {
        "post": "set_tags",
    }
)

urlpatterns = [
    path(
        "projects/<int:project_pk>/tasks/",
        task_list,
        name="task-list",
    ),
    path(
        "projects/<int:project_pk>/tasks/<int:pk>/",
        task_detail,
        name="task-detail",
    ),
    path(
        "projects/<int:project_pk>/tasks/<int:pk>/status/",
        task_status,
        name="task-status",
    ),
    path(
        "projects/<int:project_pk>/tasks/<int:pk>/assign/",
        task_assign,
        name="task-assign",
    ),
    path(
        "projects/<int:project_pk>/tasks/<int:pk>/reorder/",
        task_reorder,
        name="task-reorder",
    ),
    path(
        "projects/<int:project_pk>/tasks/<int:pk>/tags/",
        task_set_tags,
        name="task-set-tags",
    ),
]
