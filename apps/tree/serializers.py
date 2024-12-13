from rest_framework import serializers
from . import models


class ServiceTreeSerializer(serializers.ModelSerializer):
    tags = serializers.JSONField(required=False)

    class Meta:
        model = models.ServiceTreeModel
        fields = '__all__'


class TreeRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TreeRelatedModel
        fields = '__all__'