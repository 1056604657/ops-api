from django.db import models
from django.utils import timezone


# 树结构表
class ServiceTreeModel(models.Model):
    label = models.CharField(verbose_name="名称", max_length=128)
    name = models.CharField(verbose_name="标识", max_length=128, unique=True)
    parent = models.IntegerField(verbose_name="父级ID")  # 0 表示顶级
    level = models.IntegerField(verbose_name="层级")
    tags = models.JSONField(verbose_name="tag标签", null=True, blank=True)
    create_time = models.DateTimeField(verbose_name="创建时间", default=timezone.now)
    update_time = models.DateTimeField(verbose_name="创建时间", auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        db_table = "tree_list"
        verbose_name = "服务树"
        verbose_name_plural = "服务树"


# 树对应其他服务关联表
class TreeRelatedModel(models.Model):
    tree_id = models.IntegerField(verbose_name="服务树节点ID")
    target_id = models.IntegerField(verbose_name="资源ID")
    type = models.IntegerField(verbose_name="资源类型")  # 1 则是关联的CMDB
    create_time = models.DateTimeField(verbose_name="创建时间", default=timezone.now)
    update_time = models.DateTimeField(verbose_name="创建时间", auto_now=True)

    class Meta:
        db_table = "tree_related"
        verbose_name = "服务树资源关联表"
        verbose_name_plural = "服务树资源关联表"