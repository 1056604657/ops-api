from rest_framework import serializers
from rest_framework_jwt import serializers as jwt_serializers
from .models import Roles, Permissions, UserInfo, OpLogs
import logging
from django.core.cache import cache


class JSONWebTokenSerializer(jwt_serializers.JSONWebTokenSerializer):
    def is_valid(self, raise_exception=None):
        try:
            # 添加基本的参数验证
            if not self.initial_data:
                raise serializers.ValidationError('缺少认证信息')
                
            username = self.initial_data.get('username')
            if not username:
                raise serializers.ValidationError('用户名不能为空')
                
            # 可以添加缓存检查
            cache_key = f"jwt_auth_attempt_{username}"
            attempt_count = cache.get(cache_key, 0)
            
            if attempt_count > 5:  # 防止暴力破解
                raise serializers.ValidationError('尝试次数过多，请稍后再试')
                
            # 调用父类方法
            result = super().is_valid(
                raise_exception=raise_exception if raise_exception is not None else True
            )
            
            if result:
                cache.delete(cache_key)  # 登录成功，清除尝试次数
            else:
                cache.set(cache_key, attempt_count + 1, timeout=300)  # 5分钟过期
                
            return result
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"JWT验证错误: {str(e)}")
            raise


class UsersSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)

    class Meta:
        ordering = ("id",)
        model = UserInfo
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class PermissionsSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True)

    class Meta:
        model = Permissions
        fields = '__all__'


class opLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpLogs
        fields = '__all__'