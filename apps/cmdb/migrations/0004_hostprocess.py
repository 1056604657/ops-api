# Generated by Django 3.2 on 2024-09-23 10:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cmdb', '0003_remove_hostdetails_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='HostProcess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=128, null=True, verbose_name='进程名称')),
                ('egroup', models.CharField(default='', max_length=128, null=True, verbose_name='进程组')),
                ('pid', models.CharField(default='', max_length=128, null=True, verbose_name='进程ID')),
                ('ppid', models.CharField(default='', max_length=128, null=True, verbose_name='父进程ID')),
                ('cmd', models.CharField(default='', max_length=128, null=True, verbose_name='进程命令')),
                ('argvs', models.CharField(default='', max_length=128, null=True, verbose_name='进程参数')),
                ('vm_size', models.CharField(default='', max_length=128, null=True, verbose_name='进程虚拟内存大小')),
                ('size', models.CharField(default='', max_length=128, null=True, verbose_name='进程实际内存大小')),
                ('session', models.CharField(default='', max_length=128, null=True, verbose_name='进程会话ID')),
                ('priority', models.CharField(default='', max_length=128, null=True, verbose_name='进程优先级')),
                ('state', models.CharField(default='', max_length=128, null=True, verbose_name='进程状态')),
                ('related_agent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='cmdb.hostdetails', to_field='agent_id', verbose_name='关联的主机详情')),
            ],
            options={
                'verbose_name': '主机进程信息',
                'verbose_name_plural': '主机进程信息',
                'db_table': 'cmdb_host_process',
            },
        ),
    ]
