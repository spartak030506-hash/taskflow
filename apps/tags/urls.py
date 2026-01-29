from django.urls import path

from .views import TagViewSet

tag_list = TagViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

tag_detail = TagViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path(
        'projects/<int:project_pk>/tags/',
        tag_list,
        name='tag-list',
    ),
    path(
        'projects/<int:project_pk>/tags/<int:pk>/',
        tag_detail,
        name='tag-detail',
    ),
]
