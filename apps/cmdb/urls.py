from django.urls import path
from . import views

urlpatterns = [
    ## 模型分组
    path('model-group', views.ModelGroupViewSet.as_view({"get": "list", "post": "create"})),
    path('model-group/<int:pk>', views.ModelGroupViewSet.as_view({"put": "update", "delete": "destroy"})),
    ## 模型
    path('model', views.ModelViewSet.as_view({"get": "list", "post": "create"})),
    path('model/<int:pk>', views.ModelViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    ## 字段分组
    path('field-group', views.FieldGroupViewSet.as_view({"get": "list", "post": "create"})),
    path('field-group/<int:pk>', views.FieldGroupViewSet.as_view({"put": "update", "delete": "destroy"})),
    ## 字段
    path('fields', views.FieldsViewSet.as_view({"get": "list", "post": "create"})),
    path('fields/<int:pk>', views.FieldsViewSet.as_view({"put": "update", "delete": "destroy"})),
    ## 资源
    path('resource', views.ResourceViewSet.as_view({"get": "list", "post": "create"})),
    path('resource/<int:pk>', views.ResourceViewSet.as_view({"put": "update", "delete": "destroy"})),
    ## 资源关联
    path("resource-related", views.ResourceRelatedViewSet.as_view({"get": "list", "post": "create"})),
    path("resource-related/<int:pk>", views.ResourceRelatedViewSet.as_view({"put": "update", "delete": "destroy"})),
    # 数据展示
    path("pie-cmdb", views.cmdbPieChart.as_view()),
    path("type-cmdb", views.cmdbPieType.as_view()),
    path("tran-cmdb", views.cmdbTransverseChart.as_view()),
    path("cmdb-total", views.cmdbTotalChart.as_view()),
    path("histogram-cmdb", views.serviceClassification.as_view()),
    path('execute-huawei-script/', views.ExecuteHuaweiScript.as_view(), name='execute_huawei_script'),
    path("cmdb-search", views.searchGlobal.as_view({"get": "list"})),
    path('host-service', views.HostServiceView.as_view({"get": "list", "post": "create"})),
    path('host-details', views.HostDetailsView.as_view({"get": "list", "post": "create"})),
    path('update-all-host-details', views.UpdateAllHostDetailsView.as_view({"get": "fetch"})),
    path('host-rpm', views.HostRpmViewSet.as_view({"get": "list", "post": "create"})),
    path('host-rpm/<str:pk>', views.HostRpmViewSet.as_view({"get": "retrieve"})),
    path('host-process/<str:pk>', views.HostProcessViewSet.as_view({"get": "retrieve"})),  
    path('host-hardware/<str:pk>', views.HostHardwareViewSet.as_view({"get": "list"})),
    path('host-port/<str:pk>', views.HostPortViewSet.as_view({"get": "list"})),
]
