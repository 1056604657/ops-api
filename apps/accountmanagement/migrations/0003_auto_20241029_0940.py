# Generated by Django 3.2 on 2024-10-29 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accountmanagement', '0002_auto_20241028_1809'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accountmanage',
            options={'verbose_name': '账号管理'},
        ),
        migrations.RemoveField(
            model_name='accountmanage',
            name='description',
        ),
        migrations.AddField(
            model_name='accounttype',
            name='properties',
            field=models.JSONField(blank=True, default=list, verbose_name='账号属性'),
        ),
        migrations.AlterField(
            model_name='accountmanage',
            name='data',
            field=models.JSONField(verbose_name='账号数据'),
        ),
        migrations.AlterModelTable(
            name='accountmanage',
            table='accountmanagement_account_manage',
        ),
    ]