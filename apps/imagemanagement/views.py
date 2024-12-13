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

#镜像管理
class ImageManageViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.ImageManage.objects.all()
    serializer_class = serializers.ImageManageSerializer

    with open('/Users/babyyy/工作/JD/CMDB平台/ops_api/agent/config/hz_jiache_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    #镜像存储
    def create(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to create images"
        }
        results = []    
        account_summary = {} 
        image_dict_list = []
        for account_key, account_info in self.config.items(): 
            ak = account_info["ak"]
            sk = account_info["sk"]
            regions = account_info["regions"]
            account_summary[account_key] = 0 
            #删除已存在的记录
            models.ImageManage.objects.all().delete()

            for region_key in regions.keys(): 
                print("region_key:",region_key)
                credentials = BasicCredentials(ak, sk)
                client = SwrClient.new_builder() \
                    .with_credentials(credentials) \
                    .with_region(SwrRegion.value_of(region_key)) \
                    .build()
                try:
                    request = ListReposDetailsRequest()
                    request.limit = 5000
                    response = client.list_repos_details(request)
                    repos = response.body

                    if repos is None:  # 检查 repos 是否为 None
                        print("该地区没有找到任何镜像",region_key)
                        continue  # 跳过当前循环，继续下一个 region_key

                    for image in repos:
                        image_dict = image.to_dict()
                        name = image_dict['name']
                        domain_name = image_dict['domain_name']
                        namespace = image_dict['namespace']
                        num_images = image_dict['num_images']
                        path = image_dict['path']
                        tags = image_dict['tags']
                        total_range = image_dict['total_range']
                        created_at = image_dict['created_at']
                        updated_at = image_dict['updated_at']

                        image_dict = {
                            "name": name,
                            "domain_name": domain_name,
                            "namespace": namespace,
                            "num_images": num_images,
                            "path": path,
                            "tags": tags,
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "region": region_key
                        }
                        image_dict_list.append(image_dict)
                    account_summary[account_key] += total_range
                except Exception as e:
                    print(f"imagecreateError: {e}")

            #序列化后存到数据库
            serializer = self.get_serializer(data=image_dict_list, many=True)  # 添加 many=True 参数
            if serializer.is_valid():
                serializer.save()
                results.append(serializer.data)
            else:
                print("数据验证失败:", serializer.errors)
                    


        for account, count in account_summary.items():
            print(f"账号 {account} 下一共查询到 {count} 个镜像")
        res["data"] = account_summary
        return JsonResponse(res, status=status.HTTP_200_OK)


    def list(self, request, *args, **kwargs):
        # 获取所有镜像数据
        logging.info(f"Request headers: {request.headers}") 
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "code": 20000,
            "data": serializer.data,
            "message": "success to get images"
        }
        return JsonResponse(data, status=status.HTTP_200_OK)


class LatestImageSearchViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = models.ImageManage.objects.all()
    serializer_class = serializers.ImageManageSerializer
    with open('/Users/babyyy/工作/JD/CMDB平台/ops_api/agent/config/hz_jiache_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get latest images"
        }
        #通过参数中的账号在config里找到对应的ak和sk
        account = request.query_params.get("domain_name")
        region = request.query_params.get("region")
        namespace = request.query_params.get("namespace")
        repository = request.query_params.get("repository")
        ak = self.config[account]["ak"]
        sk = self.config[account]["sk"]
        
        credentials = BasicCredentials(ak, sk)

        client = SwrClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(SwrRegion.value_of(region)) \
            .build()
        request = ListRepositoryTagsRequest()
        request.namespace = namespace
        request.repository = repository
        request.limit = "1"
        request.offset = "0"
        request.order_column = "updated_at"
        request.order_type = "desc"
        response = client.list_repository_tags(request)
        print(response)
        res["data"] = response.body
        return JsonResponse(res, status=status.HTTP_200_OK)
    


