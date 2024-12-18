# Generated by Django 3.2 on 2024-09-23 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imagemanagement', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagemanage',
            name='created_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='imagemanage',
            name='domain_name',
            field=models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='域名'),
        ),
        migrations.AlterField(
            model_name='imagemanage',
            name='name',
            field=models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='镜像名称'),
        ),
        migrations.AlterField(
            model_name='imagemanage',
            name='namespace',
            field=models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='命名空间'),
        ),
        migrations.AlterField(
            model_name='imagemanage',
            name='num_images',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='镜像数量'),
        ),
        migrations.AlterField(
            model_name='imagemanage',
            name='path',
            field=models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='镜像路径'),
        ),
        migrations.AlterField(
            model_name='imagemanage',
            name='updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='更新时间'),
        ),
    ]
