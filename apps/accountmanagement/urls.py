from django.urls import path
from . import views

urlpatterns = [
   path('account_manage/', views.AccountManageViewSet.as_view({'get': 'list', 'post': 'create'})),
   path('account_manage/<int:pk>', views.AccountManageViewSet.as_view({'put': 'update', "delete": "destroy"})),
   path('account_type/', views.AccountTypeViewSet.as_view({'get': 'list', 'post': 'create'})),
   path('account_type/<int:pk>/', views.AccountTypeViewSet.as_view({'put': 'update', "delete": "destroy"})),
]