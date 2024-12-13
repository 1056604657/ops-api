from django.db import models


#账号类型
class AccountType(models.Model):
    account_type_name = models.CharField(max_length=100, verbose_name="账号类型名称", default="")
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    properties = models.JSONField(verbose_name="账号属性", default=list, blank=True)
    #查询密码
    query_password = models.CharField(max_length=100, verbose_name="查询密码", default="")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = "accountmanagement_account_type"
        verbose_name = "账号类型"


#具体账号管理表
class AccountManage(models.Model):
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    data = models.JSONField(verbose_name="账号数据")

    class Meta:
        db_table = "accountmanagement_account_manage"
        verbose_name = "账号管理"
