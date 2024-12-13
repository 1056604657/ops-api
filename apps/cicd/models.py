from django.db import models
from django.utils import timezone
# 存储创建的pipeline作业的配置
class PipelineJob(models.Model):
    language = models.CharField(max_length=100, verbose_name="语言")
    service_name = models.CharField(max_length=100, verbose_name="服务名称")
    config = models.JSONField(verbose_name="作业配置")
    jenkinsfile = models.TextField(verbose_name="Jenkinsfile")
    yaml_file = models.TextField(verbose_name="Yaml文件", default="")
    created_at = models.DateTimeField(verbose_name="创建时间", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="更新时间", default=timezone.now)

    class Meta:
        db_table = "cicd_pipeline_job"
        verbose_name = "Pipeline作业配置"
