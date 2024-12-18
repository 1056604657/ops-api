# Generated by Django 3.2 on 2024-11-19 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PipelineJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=100, verbose_name='语言')),
                ('service_name', models.CharField(max_length=100, verbose_name='服务名称')),
                ('config', models.JSONField(verbose_name='作业配置')),
                ('jenkinsfile', models.TextField(verbose_name='Jenkinsfile')),
            ],
            options={
                'verbose_name': 'Pipeline作业配置',
                'db_table': 'cicd_pipeline_job',
            },
        ),
    ]
