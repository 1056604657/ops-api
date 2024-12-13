from rest_framework import serializers
from . import models


class AccountManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountManage
        fields = '__all__'

class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountType
        fields = '__all__'
