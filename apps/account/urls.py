from django.urls import path
from . import views

urlpatterns = [
   path('gaodekeylist/', views.GaodeViewSet.as_view({'get': 'gaodekeylist'})),
   ]