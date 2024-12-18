# Generated by Django 3.2 on 2024-09-20 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(max_length=128, unique=True, verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=255, null=True, unique=True, verbose_name='email')),
                ('name', models.CharField(blank=True, max_length=128, null=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='是否可用')),
                ('is_admin', models.BooleanField(default=False, verbose_name='是否管理员')),
                ('create_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'system_user',
            },
        ),
        migrations.CreateModel(
            name='OpLogs',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('re_time', models.CharField(max_length=32, verbose_name='请求时间')),
                ('re_user', models.CharField(max_length=32, verbose_name='操作人')),
                ('re_ip', models.CharField(max_length=32, verbose_name='请求IP')),
                ('re_url', models.CharField(max_length=255, verbose_name='请求url')),
                ('re_method', models.CharField(max_length=11, verbose_name='请求方法')),
                ('re_content', models.TextField(null=True, verbose_name='请求参数')),
                ('rp_content', models.TextField(null=True, verbose_name='响应参数')),
                ('access_time', models.IntegerField(verbose_name='响应耗时/ms')),
            ],
            options={
                'db_table': 'op_logs',
            },
        ),
        migrations.CreateModel(
            name='Permissions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=45, verbose_name='标题')),
                ('name', models.CharField(blank=True, max_length=45, verbose_name='名称')),
                ('icon', models.CharField(blank=True, max_length=45, verbose_name='图标')),
                ('sort', models.IntegerField(default=0, verbose_name='展示顺序')),
                ('parent', models.IntegerField(default=0, verbose_name='父级')),
                ('type', models.IntegerField(default=1, verbose_name='权限类型')),
                ('component', models.CharField(blank=True, max_length=256, verbose_name='组件地址')),
                ('alias', models.CharField(blank=True, max_length=256, verbose_name='别名')),
                ('path', models.CharField(blank=True, max_length=256, verbose_name='路由地址')),
                ('hidden', models.BooleanField(default=False, verbose_name='是否隐藏')),
                ('external_link', models.BooleanField(default=False, verbose_name='是否外链')),
                ('permission', models.CharField(blank=True, max_length=128, verbose_name='权限标识')),
                ('cache', models.BooleanField(default=False, verbose_name='是否缓存')),
                ('redirect', models.CharField(blank=True, max_length=256, verbose_name='跳转地址')),
            ],
            options={
                'db_table': 'system_permissions',
            },
        ),
        migrations.CreateModel(
            name='RolePermissions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.IntegerField(verbose_name='角色ID')),
                ('permission', models.IntegerField(verbose_name='权限ID')),
            ],
            options={
                'db_table': 'system_role_permissions',
            },
        ),
        migrations.CreateModel(
            name='Roles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=45, verbose_name='名称')),
                ('remarks', models.CharField(blank=True, max_length=1024, null=True, verbose_name='描述')),
            ],
            options={
                'db_table': 'system_roles',
            },
        ),
        migrations.CreateModel(
            name='UserRoles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.IntegerField(verbose_name='用户ID')),
                ('role', models.IntegerField(verbose_name='角色ID')),
            ],
            options={
                'db_table': 'system_user_roles',
            },
        ),
    ]
