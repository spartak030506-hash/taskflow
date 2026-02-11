from django.urls import path

from .views import CommentViewSet

comment_list = CommentViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

comment_detail = CommentViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

urlpatterns = [
    path(
        "projects/<int:project_pk>/tasks/<int:task_pk>/comments/",
        comment_list,
        name="comment-list",
    ),
    path(
        "projects/<int:project_pk>/tasks/<int:task_pk>/comments/<int:pk>/",
        comment_detail,
        name="comment-detail",
    ),
]
