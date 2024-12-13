from rest_framework import serializers
from . import models


class ModelGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModelGroup
        fields = '__all__'


class ModelSerializer(serializers.ModelSerializer):
    icon = serializers.CharField(required=False)
    tag = serializers.JSONField(required=False)

    class Meta:
        model = models.Model
        fields = '__all__'


class FieldGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FieldGroup
        fields = '__all__'


class FieldsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    cname = serializers.CharField(required=True)

    class Meta:
        model = models.Fields
        fields = '__all__'


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Resource
        fields = '__all__'


class ResourceRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ResourceRelated
        fields = '__all__'

# class HostServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.HostService
#         fields = '__all__'


class HostServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HostService
        fields = '__all__'



class HostDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HostDetails
        fields = '__all__'

class HostRpmSerializer(serializers.ModelSerializer):
    agent_id = serializers.CharField(write_only=True, required=False)
    host_ip = serializers.CharField(source='related_agent.host_ip', read_only=True)

    class Meta:
        model = models.HostRpm
        fields = ['agent_id', 'host_ip', 'rpm_name', 'architecture', 'version', 'vendor', 'description']

    def create(self, validated_data):
        agent_id = validated_data.pop('agent_id', None)
        if agent_id:
            host_details, _ = models.HostDetails.objects.get_or_create(agent_id=agent_id)
            validated_data['related_agent'] = host_details
        return super().create(validated_data)

    def update(self, instance, validated_data):
        agent_id = validated_data.pop('agent_id', None)
        if agent_id:
            host_details, _ = models.HostDetails.objects.get_or_create(agent_id=agent_id)
            instance.related_agent = host_details
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['agent_id'] = instance.related_agent.agent_id if instance.related_agent else None
        return ret
    

class HostProcessSerializer(serializers.ModelSerializer):
    host_ip = serializers.CharField(source='related_agent.host_ip', read_only=True)

    class Meta:
        model = models.HostProcess
        fields = '__all__'


class HostPortSerializer(serializers.ModelSerializer):
    host_ip = serializers.CharField(source='related_agent.host_ip', read_only=True)
    
    class Meta:
        model = models.HostPort
        fields = '__all__'

