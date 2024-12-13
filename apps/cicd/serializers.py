from rest_framework import serializers
from . import models


class PipelineJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PipelineJob
        fields = '__all__'
    