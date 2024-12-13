from rest_framework import serializers
from apps.cmdb.models import Resource

class RdsManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'  