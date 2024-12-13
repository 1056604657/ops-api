from django.db import models
from django.utils import timezone

# 模型分组
class ModelGroup(models.Model):
    name = models.CharField(verbose_name="名称", max_length=128)
    sort = models.IntegerField(verbose_name="顺序", default=0)
    remarks = models.CharField(verbose_name="描述", max_length=1024, null=True, blank=True)

    class Meta:
        db_table = "cmdb_model_group"


# 模型
class Model(models.Model):
    name = models.CharField(verbose_name="名称", max_length=128)
    icon = models.CharField(verbose_name="图标", max_length=45)
    tag = models.JSONField(verbose_name="标签", null=True, blank=True)
    group = models.IntegerField(verbose_name="分组")

    class Meta:
        db_table = "cmdb_model"


# 字段分组
class FieldGroup(models.Model):
    name = models.CharField(verbose_name="名称", max_length=128)
    model = models.IntegerField(verbose_name="模型")
    sort = models.IntegerField(verbose_name="顺序", default=0)
    remarks = models.CharField(verbose_name="描述", max_length=1024, null=True, blank=True)

    class Meta:
        db_table = "cmdb_model_field_group"


# 字段
class Fields(models.Model):
    name = models.CharField(verbose_name="英文标识", max_length=128, default="")
    cname = models.CharField(verbose_name="名称", max_length=128, default="")
    type = models.CharField(verbose_name="类型", max_length=128)  # 字段存放的数据，是什么类型，例如：字符串(string)，整数(int)...
    is_unique = models.BooleanField(verbose_name="是否唯一", default=False)
    required = models.BooleanField(verbose_name="必填", default=False)
    prompt = models.CharField(verbose_name="用户提示", max_length=1024, null=True, blank=True)
    group = models.IntegerField(verbose_name="分组")
    model = models.IntegerField(verbose_name="模型")
    is_list = models.BooleanField(verbose_name="是否列表展示", default=True)
    default = models.CharField(verbose_name="默认值", max_length=512, null=True, blank=True)
    configuration = models.JSONField(verbose_name="自定义配置", null=True, blank=True)

    class Meta:
        db_table = "cmdb_model_fields"
        unique_together = ('name', 'model',)


# 资源
class Resource(models.Model):
    model = models.IntegerField(verbose_name="模型")
    data = models.JSONField(verbose_name="数据")
    tag = models.JSONField(verbose_name="标签", null=True, blank=True)

    class Meta:
        db_table = "cmdb_resource"


# 资源关联
class ResourceRelated(models.Model):
    source = models.IntegerField(verbose_name="源数据ID")
    target = models.IntegerField(verbose_name="目标数据ID")

    class Meta:
        db_table = "cmdb_resource_related"

#每台主机上的服务名称
class HostService(models.Model):
    host_ip = models.CharField(max_length=128,default="", verbose_name="主机IP")
    host_name = models.CharField(max_length=128,default="", verbose_name="主机名称")
    service_command = models.JSONField(default=dict, verbose_name="服务启动命令")  # 修改默认值为 callable
    class Meta:
        db_table = "cmdb_host_service"
        verbose_name = "主机服务信息"
        verbose_name_plural = verbose_name




#wazuh搜集的每台主机上的基本信息表
class HostDetails(models.Model):
    agent_id = models.CharField(max_length=128, default="", verbose_name="agentID", unique=True)
    host_ip = models.CharField(max_length=128,default="", verbose_name="主机IP")
    host_name = models.CharField(max_length=128,default="", verbose_name="主机名称")
    platform = models.CharField(max_length=128,default="", verbose_name="操作系统")
    version = models.CharField(max_length=128,default="", verbose_name="操作系统版本")
    status = models.CharField(max_length=128,default="", verbose_name="主机状态")
    class Meta:
        db_table = "cmdb_host_details"
        verbose_name = "主机基本信息"
        verbose_name_plural = verbose_name

#wazuh搜集的每台主机上安装的rpm包
class HostRpm(models.Model):
    related_agent = models.ForeignKey(HostDetails, on_delete=models.CASCADE, verbose_name="关联的主机详情", to_field='agent_id', db_column='agent_id', null=True) 
    rpm_name = models.CharField(max_length=128, default="", verbose_name="rpm包名称")
    architecture = models.CharField(max_length=128, default="", verbose_name="架构", null=True, blank=True) 
    version = models.CharField(max_length=128, default="", verbose_name="版本", null=True, blank=True)  
    vendor = models.CharField(max_length=128, default="", verbose_name="供应商", null=True, blank=True)  
    description = models.TextField(default="", verbose_name="描述", null=True, blank=True)  
    class Meta:
        db_table = "cmdb_host_rpm"
        verbose_name = "主机rpm包信息"
        verbose_name_plural = verbose_name


#wazuh搜集的每台主机上安装的进程
class HostProcess(models.Model):
    related_agent = models.ForeignKey(HostDetails, on_delete=models.CASCADE, verbose_name="关联的主机详情", to_field='agent_id', null=True) 
    name = models.CharField(max_length=128, default="", verbose_name="进程名称", null=True, blank=True)
    egroup = models.CharField(max_length=128, default="", verbose_name="进程组", null=True, blank=True)
    pid = models.CharField(max_length=128, default="", verbose_name="进程ID", null=True, blank=True)
    ppid = models.CharField(max_length=128, default="", verbose_name="父进程ID", null=True, blank=True)
    cmd = models.CharField(max_length=128, default="", verbose_name="进程命令", null=True, blank=True)
    argvs = models.TextField(default="", verbose_name="进程参数", null=True, blank=True)
    vm_size = models.CharField(max_length=128, default="", verbose_name="进程虚拟内存大小", null=True, blank=True)
    size = models.CharField(max_length=128, default="", verbose_name="进程实际内存大小", null=True, blank=True)
    session = models.CharField(max_length=128, default="", verbose_name="进程会话ID", null=True, blank=True)
    priority = models.CharField(max_length=128, default="", verbose_name="进程优先级", null=True, blank=True)
    state = models.CharField(max_length=128, default="", verbose_name="进程状态", null=True, blank=True)
    class Meta:
        db_table = "cmdb_host_process"
        verbose_name = "主机进程信息"
        verbose_name_plural = verbose_name

#wazuh搜集的每台主机上的端口
class HostPort(models.Model):
    related_agent = models.ForeignKey(HostDetails, on_delete=models.CASCADE, verbose_name="关联的主机详情", to_field='agent_id', null=True) 
    local_ip = models.CharField(max_length=128, default="", verbose_name="本地IP", null=True, blank=True)
    local_port = models.CharField(max_length=128, default="", verbose_name="本地端口", null=True, blank=True)
    remote_ip = models.CharField(max_length=128, default="", verbose_name="远程IP", null=True, blank=True)
    remote_port = models.CharField(max_length=128, default="", verbose_name="远程端口", null=True, blank=True)
    process = models.CharField(max_length=128, default="", verbose_name="进程", null=True, blank=True)
    pid = models.CharField(max_length=128, default="", verbose_name="进程ID", null=True, blank=True)
    state = models.CharField(max_length=128, default="", verbose_name="进程状态", null=True, blank=True)
    protocol = models.CharField(max_length=128, default="", verbose_name="协议", null=True, blank=True)
    class Meta:
        db_table = "cmdb_host_port"
        verbose_name = "主机端口信息"
        verbose_name_plural = verbose_name


class SyncLock(models.Model):
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SyncLock(is_locked={self.is_locked}, locked_at={self.locked_at})"