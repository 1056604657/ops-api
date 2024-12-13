from django.db import models
from .user.models import UserInfo


# 角色表
class Roles(models.Model):
    name = models.CharField(verbose_name="名称", max_length=45, default="")
    remarks = models.CharField(verbose_name="描述", max_length=1024, null=True, blank=True)

    class Meta:
        db_table = "system_roles"


# 用户关联角色
class UserRoles(models.Model):
    user = models.IntegerField(verbose_name="用户ID")
    role = models.IntegerField(verbose_name="角色ID")

    class Meta:
        db_table = "system_user_roles"


# 权限，包括菜单和标签等数据
class Permissions(models.Model):
    title = models.CharField(verbose_name="标题", max_length=45, blank=True)
    name = models.CharField(verbose_name="名称", max_length=45, blank=True)
    icon = models.CharField(verbose_name="图标", max_length=45, blank=True)
    sort = models.IntegerField(verbose_name="展示顺序", default=0)
    parent = models.IntegerField(verbose_name="父级", default=0)  # 0 表示顶级菜单
    type = models.IntegerField(verbose_name="权限类型", default=1)  # 1 菜单，2 标签
    component = models.CharField(verbose_name="组件地址", max_length=256, blank=True)
    alias = models.CharField(verbose_name="别名", max_length=256, blank=True)
    path = models.CharField(verbose_name="路由地址", max_length=256, blank=True)  # 访问的路径地址
    hidden = models.BooleanField(verbose_name="是否隐藏", default=False)
    external_link = models.BooleanField(verbose_name="是否外链", default=False)
    permission = models.CharField(verbose_name="权限标识", max_length=128, blank=True)  # 用于页面元素的权限管控
    cache = models.BooleanField(verbose_name="是否缓存", default=False)
    redirect = models.CharField(verbose_name="跳转地址", max_length=256, blank=True)

    class Meta:
        db_table = "system_permissions"


# 角色权限关联表
class RolePermissions(models.Model):
    role = models.IntegerField(verbose_name="角色ID")
    permission = models.IntegerField(verbose_name="权限ID")

    class Meta:
        db_table = "system_role_permissions"


# 操作日志表
class OpLogs(models.Model):
    id = models.AutoField(primary_key=True)
    re_time = models.CharField(max_length=32, verbose_name='请求时间')
    re_user = models.CharField(max_length=32, verbose_name='操作人')
    re_ip = models.CharField(max_length=32, verbose_name='请求IP')
    re_url = models.CharField(max_length=255, verbose_name='请求url')
    re_method = models.CharField(max_length=11, verbose_name='请求方法')
    re_content = models.TextField(null=True, verbose_name='请求参数')
    rp_content = models.TextField(null=True, verbose_name='响应参数')
    access_time = models.IntegerField(verbose_name='响应耗时/ms')

    class Meta:
        db_table = 'op_logs'