from rest_framework import serializers
from . import models


class ImageManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ImageManage
        fields = '__all__'
