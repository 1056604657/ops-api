# Generated by Django 3.2 on 2024-09-20 20:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FieldGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='名称')),
                ('model', models.IntegerField(verbose_name='模型')),
                ('sort', models.IntegerField(default=0, verbose_name='顺序')),
                ('remarks', models.CharField(blank=True, max_length=1024, null=True, verbose_name='描述')),
            ],
            options={
                'db_table': 'cmdb_model_field_group',
            },
        ),
        migrations.CreateModel(
            name='HostDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_id', models.CharField(default='', max_length=128, unique=True, verbose_name='agentID')),
                ('host_ip', models.CharField(default='', max_length=128, verbose_name='主机IP')),
                ('host_name', models.CharField(default='', max_length=128, verbose_name='主机名称')),
                ('platform', models.CharField(default='', max_length=128, verbose_name='操作系统')),
                ('version', models.CharField(default='', max_length=128, verbose_name='操作系统版本')),
                ('status', models.CharField(default='', max_length=128, verbose_name='主机状态')),
            ],
            options={
                'verbose_name': '主机基本信息',
                'verbose_name_plural': '主机基本信息',
                'db_table': 'cmdb_host_details',
            },
        ),
        migrations.CreateModel(
            name='HostService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_ip', models.CharField(default='', max_length=128, verbose_name='主机IP')),
                ('host_name', models.CharField(default='', max_length=128, verbose_name='主机名称')),
                ('service_command', models.JSONField(default=dict, verbose_name='服务启动命令')),
            ],
            options={
                'verbose_name': '主机服务信息',
                'verbose_name_plural': '主机服务信息',
                'db_table': 'cmdb_host_service',
            },
        ),
        migrations.CreateModel(
            name='ImageManage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=128, verbose_name='镜像名称')),
                ('num_images', models.IntegerField(default=0, verbose_name='镜像数量')),
                ('created_at', models.DateTimeField(verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(verbose_name='更新时间')),
                ('path', models.CharField(default='', max_length=128, verbose_name='镜像路径')),
                ('domain_name', models.CharField(default='', max_length=128, verbose_name='域名')),
                ('namespace', models.CharField(default='', max_length=128, verbose_name='命名空间')),
                ('tags', models.JSONField(blank=True, null=True, verbose_name='镜像标签')),
            ],
            options={
                'db_table': 'cmdb_image_manage',
            },
        ),
        migrations.CreateModel(
            name='Model',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='名称')),
                ('icon', models.CharField(max_length=45, verbose_name='图标')),
                ('tag', models.JSONField(blank=True, null=True, verbose_name='标签')),
                ('group', models.IntegerField(verbose_name='分组')),
            ],
            options={
                'db_table': 'cmdb_model',
            },
        ),
        migrations.CreateModel(
            name='ModelGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='名称')),
                ('sort', models.IntegerField(default=0, verbose_name='顺序')),
                ('remarks', models.CharField(blank=True, max_length=1024, null=True, verbose_name='描述')),
            ],
            options={
                'db_table': 'cmdb_model_group',
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.IntegerField(verbose_name='模型')),
                ('data', models.JSONField(verbose_name='数据')),
                ('tag', models.JSONField(blank=True, null=True, verbose_name='标签')),
            ],
            options={
                'db_table': 'cmdb_resource',
            },
        ),
        migrations.CreateModel(
            name='ResourceRelated',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.IntegerField(verbose_name='源数据ID')),
                ('target', models.IntegerField(verbose_name='目标数据ID')),
            ],
            options={
                'db_table': 'cmdb_resource_related',
            },
        ),
        migrations.CreateModel(
            name='HostRpm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rpm_name', models.CharField(default='', max_length=128, verbose_name='rpm包名称')),
                ('architecture', models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='架构')),
                ('version', models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='版本')),
                ('vendor', models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='供应商')),
                ('description', models.TextField(blank=True, default='', null=True, verbose_name='描述')),
                ('related_agent', models.ForeignKey(db_column='agent_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='cmdb.hostdetails', to_field='agent_id', verbose_name='关联的主机详情')),
            ],
            options={
                'verbose_name': '主机rpm包信息',
                'verbose_name_plural': '主机rpm包信息',
                'db_table': 'cmdb_host_rpm',
            },
        ),
        migrations.CreateModel(
            name='Fields',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=128, verbose_name='英文标识')),
                ('cname', models.CharField(default='', max_length=128, verbose_name='名称')),
                ('type', models.CharField(max_length=128, verbose_name='类型')),
                ('is_unique', models.BooleanField(default=False, verbose_name='是否唯一')),
                ('required', models.BooleanField(default=False, verbose_name='必填')),
                ('prompt', models.CharField(blank=True, max_length=1024, null=True, verbose_name='用户提示')),
                ('group', models.IntegerField(verbose_name='分组')),
                ('model', models.IntegerField(verbose_name='模型')),
                ('is_list', models.BooleanField(default=True, verbose_name='是否列表展示')),
                ('default', models.CharField(blank=True, max_length=512, null=True, verbose_name='默认值')),
                ('configuration', models.JSONField(blank=True, null=True, verbose_name='自定义配置')),
            ],
            options={
                'db_table': 'cmdb_model_fields',
                'unique_together': {('name', 'model')},
            },
        ),
    ]
