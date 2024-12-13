from django.urls import path, re_path
from . import views

urlpatterns = [
    # 服务树
    path("", views.ServiceTreeViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:pk>", views.ServiceTreeViewSet.as_view({"put": "update", "delete": "destroy"})),
    # 服务树关联
    path("related", views.TreeRelatedViewSet.as_view({"get": "list", "post": "create"})),
    path("related/<int:pk>", views.TreeRelatedViewSet.as_view({"put": "update", "delete": "destroy"})),
    # 查询关联的资产
    path("get-reloated-resource/<int:pk>", views.GetNodeResourceAPIView.as_view()),
]
