# Generated by Django 3.2 on 2024-10-29 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accountmanagement', '0003_auto_20241029_0940'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounttype',
            name='query_password',
            field=models.CharField(default='', max_length=100, verbose_name='查询密码'),
        ),
    ]