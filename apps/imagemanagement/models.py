from django.db import models
from django.utils import timezone

class ImageManage(models.Model):
    name = models.CharField(max_length=128,default="", verbose_name="镜像名称",null=True, blank=True)
    num_images = models.IntegerField(default=0, verbose_name="镜像数量",null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="创建时间",null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="更新时间",null=True, blank=True)
    path = models.CharField(max_length=128,default="", verbose_name="镜像路径",null=True, blank=True)
    domain_name = models.CharField(max_length=128,default="", verbose_name="域名",null=True, blank=True)
    namespace = models.CharField(max_length=128,default="", verbose_name="命名空间",null=True, blank=True)
    tags = models.JSONField(verbose_name="镜像标签", null=True, blank=True)
    region = models.CharField(max_length=128,default="", verbose_name="区域",null=True, blank=True)
    class Meta:
        db_table = "imagemanagement_image_manage"