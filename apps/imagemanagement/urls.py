from django.urls import path
from . import views

urlpatterns = [
   path('image_manage/', views.ImageManageViewSet.as_view({'get': 'list', 'post': 'create'})),
]