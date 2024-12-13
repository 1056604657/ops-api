from django.urls import path
from . import views

urlpatterns = [
   path('rds-management/', views.RdsManagementViewSet.as_view({'get': 'list', 'post': 'create'})),
   path('rds-backup/', views.RdsBackupViewSet.as_view({'get': 'list', 'post': 'create'})),
   path('k8s/clusters/', views.K8sViewSet.as_view({'get': 'get_k8s_cluster_list'})),
   path('k8s/resources/', views.K8sViewSet.as_view({'get': 'get_k8s_resource'})),
   path('k8s/namespaces/', views.K8sViewSet.as_view({'get': 'get_k8s_namespace'})),
   path('k8s/pods/', views.K8sViewSet.as_view({'get': 'get_k8s_pod'})),
   path('k8s/get-resource-yaml/', views.K8sViewSet.as_view({'get': 'get_k8s_resource_yaml'})),
   path('k8s/pod-logs/', views.K8sViewSet.as_view({'get': 'get_k8s_pod_logs'})),
   path('k8s/apply-yaml', views.K8sViewSet.as_view({'post': 'apply_resource_from_yaml'})),
   path('k8s/restart-workload/', views.K8sViewSet.as_view({'post': 'restart_workload'})),
   path('k8s/delete-workload/', views.K8sViewSet.as_view({'post': 'delete_workload'})),
   path('k8s/scale-workload/', views.K8sViewSet.as_view({'get': 'scale_workload'})),
   path('k8s/set-deployment-image/', views.K8sViewSet.as_view({'get': 'set_deployment_image'})),
   path('k8s/get-latest-image/', views.K8sViewSet.as_view({'get': 'get_latest_image'})),
   #path('k8s/pod-terminal-info/', views.K8sViewSet.as_view({'get': 'get_pod_terminal_info'})),
   path('k8s/delete-pod', views.K8sViewSet.as_view({'post': 'delete_pod'})),
   path('k8s/get-configmap-secret-data/', views.K8sViewSet.as_view({'get': 'get_configmap_secret_data'})),
]
