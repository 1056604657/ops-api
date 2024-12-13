from django.urls import path
from . import views

urlpatterns = [
    path('template-generator/generate', 
         views.TemplateGeneratorViewSet.as_view({'post': 'generate'})),
    path('jenkinsjob-list', 
         views.TemplateGeneratorViewSet.as_view({'get': 'get_jenkinsjob_list'})),
    path('job-jenkinsfile', 
         views.TemplateGeneratorViewSet.as_view({'get': 'get_job_jenkinsfile'})),
    path('delete-jenkinsjob', 
         views.TemplateGeneratorViewSet.as_view({'post': 'delete_jenkinsjob'})),
]