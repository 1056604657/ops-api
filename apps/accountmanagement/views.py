import xlrd
from io import BytesIO
from django.db.models import Q
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from pkg.custom_model_view_set import CustomModelViewSet
from . import models, serializers, filter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from rest_framework import status
from pkg.has_resource_verify import has_resource_verify
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models.functions import Lower
import subprocess
import os
import logging
from rest_framework.response import Response
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkswr.v2.region.swr_region import SwrRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkswr.v2 import *
import json
import requests
import time
from cryptography.fernet import Fernet
import base64
from django.conf import settings

# 设置日志记录器
logger = logging.getLogger(__name__)

# 添加密码加密解密的工具类
class PasswordCrypto:
    def __init__(self):
        # 使用 Django 的 SECRET_KEY 生成加密密钥
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        self.cipher_suite = Fernet(key)

    def encrypt(self, password):
        if not password:
            return password
        return self.cipher_suite.encrypt(password.encode()).decode()

    def decrypt(self, encrypted_password):
        if not encrypted_password:
            return encrypted_password
        try:
            return self.cipher_suite.decrypt(encrypted_password.encode()).decode()
        except:
            return "******"  # 解密失败返回星号

class AccountTypeViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = models.AccountType.objects.all()
    serializer_class = serializers.AccountTypeSerializer

    # 增加账号类型
    def create(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to create account type"
        }
        account_type_name = request.data.get('account_type_name')
        description = request.data.get('description')
        properties = request.data.get('properties', [])
        query_password = request.data.get('query_password')  # 获取查询密码

        # 验证属性列表格式
        if not isinstance(properties, list):
            res["code"] = 40000
            res["message"] = "properties must be a list"
            return JsonResponse(res)

        # 验证每个属性是否包含必要的字段
        for prop in properties:
            if not isinstance(prop, dict) or 'name' not in prop or 'key' not in prop:
                res["code"] = 40000
                res["message"] = "每个属性必须包含 name 和 key 字段"
                return JsonResponse(res)

        if models.AccountType.objects.filter(account_type_name=account_type_name).exists():
            res["code"] = 40000
            res["message"] = "account type name already exists"
            return JsonResponse(res)

        # 创建账号类型时包含查询密码
        models.AccountType.objects.create(
            account_type_name=account_type_name,
            description=description,
            properties=properties,
            query_password=query_password,  # 添加查询密码
            created_at=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )
        return JsonResponse(res)

    # 获取所有账号类型
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "code": 20000,
            "data": serializer.data,
            "message": "success to get account types"
        }
        return JsonResponse(data)
    
    # 修改账号类型的名称、描述和属性
    def update(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to update account type"
        }   
        account_type_name = request.data.get('account_type_name')
        description = request.data.get('description')
        properties = request.data.get('properties')
        query_password = request.data.get('query_password')
        account_type_id = kwargs.get('pk')

        # 验证属性列表格式
        if properties is not None:
            if not isinstance(properties, list):
                logger.error(f"属性格式错误: {properties}")
                res["code"] = 40000
                res["message"] = "properties must be a list"
                return JsonResponse(res)

            # 验证每个属性是否包含必要的字段
            for prop in properties:
                if not isinstance(prop, dict) or 'name' not in prop or 'key' not in prop:
                    logger.error(f"属性字段缺失: {prop}")
                    res["code"] = 40000
                    res["message"] = "每个属性必须包含 name 和 key 字段"
                    return JsonResponse(res)

        update_data = {
            'account_type_name': account_type_name,
            'description': description
        }
        if properties is not None:
            update_data['properties'] = properties
        if query_password is not None:
            update_data['query_password'] = query_password

        try:
            # 使用ID查询而不是名称
            instance = models.AccountType.objects.get(id=account_type_id)
            logger.info(f"找到待更新记录: {instance.account_type_name} -> {account_type_name}")
            
            # 检查新名称是否与其他记录冲突
            if models.AccountType.objects.exclude(id=account_type_id).filter(account_type_name=account_type_name).exists():
                logger.error(f"账号类型名称已存在: {account_type_name}")
                res["code"] = 40000
                res["message"] = "account type name already exists"
                return JsonResponse(res)

            # 更新记录
            models.AccountType.objects.filter(id=account_type_id).update(**update_data)
            logger.info(f"更新成功: {update_data}")
        except models.AccountType.DoesNotExist:
            logger.error(f"未找到账号类型记录，ID: {account_type_id}")
            res["code"] = 40000
            res["message"] = "account type not found"
        except Exception as e:
            logger.error(f"更新失败: {str(e)}")
            res["code"] = 40000
            res["message"] = str(e)

        return JsonResponse(res)

    # 删除账号类型
    def destroy(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to delete account type"
        }
        try:
            instance = self.get_object()
            # 检查是否有关联的账号记录
            if models.AccountManage.objects.filter(account_type=instance).exists():
                res["code"] = 40000
                res["message"] = "该账号类型下存在账号记录，无法删除"
                return JsonResponse(res)
            instance.delete()
        except Exception as e:
            res["code"] = 40000
            res["message"] = str(e)
        return JsonResponse(res)

class AccountManageViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = models.AccountManage.objects.all()
    serializer_class = serializers.AccountManageSerializer
    password_crypto = PasswordCrypto()

    def _get_password_keys(self, account_type_id):
        """获取指定账号类型中所有包含'密码'的属性的key"""
        try:
            account_type = models.AccountType.objects.get(id=account_type_id)
            password_props = [
                prop for prop in account_type.properties 
                if isinstance(prop.get('name'), str) and '密码' in prop.get('name')
            ]
            return {prop['name']: prop['key'] for prop in password_props}
        except models.AccountType.DoesNotExist:
            return {}

    def _process_password_fields(self, data, account_type_id, encrypt=True):
        """处理数据中的密码字段"""
        if not isinstance(data, dict):
            return data
        
        password_keys = self._get_password_keys(account_type_id)
        processed_data = data.copy()

        for name, key in password_keys.items():
            if key in processed_data:
                value = processed_data[key]
                processed_data[key] = self.password_crypto.encrypt(value) if encrypt else self.password_crypto.decrypt(value)
        
        return processed_data

    def create(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "添加账号成功"
        }
        try:
            request_data = request.data.copy()
            account_type_id = request_data.get('account_type')
            
            if 'data' in request_data and account_type_id:
                request_data['data'] = self._process_password_fields(
                    request_data['data'], 
                    account_type_id, 
                    encrypt=True
                )
            
            serializer = self.get_serializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # 返回时解密密码字段
            response_data = serializer.data.copy()
            if 'data' in response_data:
                response_data['data'] = self._process_password_fields(
                    response_data['data'], 
                    account_type_id, 
                    encrypt=False
                )
            res["data"] = response_data
            
        except Exception as e:
            logger.error(f"创建账号失败: {str(e)}")
            res["code"] = 40000
            res["message"] = str(e)

        return JsonResponse(res)

    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": [],
            "message": "获取账号列表成功"
        }
        try:
            account_type_id = request.query_params.get('account_type')
            show_password = request.query_params.get('show_password') == 'true'
            account_id = request.query_params.get('id')  # 获取特定账号ID
            
            queryset = self.get_queryset()
            if account_type_id:
                queryset = queryset.filter(account_type_id=account_type_id)
            if account_id:
                queryset = queryset.filter(id=account_id)

            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

            # 处理密码字段
            for item in data:
                if 'data' in item and item.get('account_type'):
                    if show_password:
                        # 如果请求显示密码，解密所有密码字段
                        item['data'] = self._process_password_fields(
                            item['data'], 
                            item['account_type'], 
                            encrypt=False
                        )
                    else:
                        # 如果不显示密码，保持加密状态
                        password_keys = self._get_password_keys(item['account_type'])
                        for _, key in password_keys.items():
                            if key in item['data']:
                                # 保持加密状态，不做解密处理
                                continue
            
            res["data"] = data
            
        except Exception as e:
            logger.error(f"获取账号列表失败: {str(e)}")
            res["code"] = 40000
            res["message"] = str(e)

        return JsonResponse(res)

    def update(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "更新账号成功"
        }
        try:
            instance = self.get_object()
            request_data = request.data.copy()
            account_type_id = request_data.get('account_type')

            if 'data' in request_data and account_type_id:
                request_data['data'] = self._process_password_fields(
                    request_data['data'], 
                    account_type_id, 
                    encrypt=True
                )
            
            serializer = self.get_serializer(instance, data=request_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            response_data = serializer.data.copy()
            if 'data' in response_data:
                response_data['data'] = self._process_password_fields(
                    response_data['data'], 
                    account_type_id, 
                    encrypt=False
                )
            res["data"] = response_data
            
        except Exception as e:
            res["code"] = 40000
            res["message"] = str(e)
        return JsonResponse(res)

    def destroy(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "删除账号成功"
        }
        try:
            instance = self.get_object()
            instance.delete()  # 直接调用模型实例的 delete 方法
        except Exception as e:
            logger.error(f"删除账号失败: {str(e)}")
            res["code"] = 40000
            res["message"] = str(e)
        return JsonResponse(res)