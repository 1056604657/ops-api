from django.urls import path
from . import views

urlpatterns = [
    # 用户相关
    path('user/details', views.GetInfoView.as_view()),
    path('user', views.UsersViewSet.as_view({"get": "list", "post": "create"})),
    path('user/<int:pk>', views.UsersViewSet.as_view({"put": "update", "delete": "destroy"})),
    path('user/permission', views.UserPermissionsView.as_view()),
    # 角色相关
    path('role', views.RolesViewSet.as_view({"get": "list", "post": "create"})),
    path('role/<int:pk>', views.RolesViewSet.as_view({"put": "update", "delete": "destroy"})),
    path('role/permission/<int:pk>', views.UpdateRolePermissionView.as_view()),
    # 权限相关
    path('permission', views.PermissionsViewSet.as_view({"get": "list", "post": "create"})),
    path('permissions', views.TreeMenuView.as_view()),
    path('all-permissions', views.PermissionTreeView.as_view()),
    path('permission/<int:pk>', views.PermissionsViewSet.as_view({"put": "update", "delete": "destroy"})),
    # 操作日志
    path('operation', views.OpLogsViewSet.as_view({"get": "list", "post": "create"}))
]
