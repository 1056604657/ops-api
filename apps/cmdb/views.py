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
from django.db import transaction
from .models import SyncLock

# 模型分组
class ModelGroupViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.ModelGroup.objects.all()
    serializer_class = serializers.ModelGroupSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.ModelGroupFilter

    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                for model_group in serializer.data:
                    model_group["models"] = list(models.Model.objects.filter(group=model_group.get("id")).values())
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            res["data"] = serializer.data
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"获取模型分组失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


# 模型分组
class ModelViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.Model.objects.all()
    serializer_class = serializers.ModelSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.ModelFilter

    def retrieve(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            result = dict(serializer.data)
            field_group_list = list(models.FieldGroup.objects.filter(model=kwargs.get("pk")).values())
            for field_group in field_group_list:
                field_group["fields"] = list(models.Fields.objects.filter(group=field_group.get("id")).values())
            result["field_group"] = field_group_list
            res["data"] = result
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询模型详情失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


# 字段分组
class FieldGroupViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.FieldGroup.objects.all()
    serializer_class = serializers.FieldGroupSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.FieldGroupFilter


# 字段
class FieldsViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.Fields.objects.all()
    serializer_class = serializers.FieldsSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.FieldsFilter


# 资源
class ResourceViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.Resource.objects.all()
    serializer_class = serializers.ResourceSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.ResourceFilter

    def list(self, request, *args, **kwargs):
        model_id = self.request.query_params.get('model', None)
        data = self.request.query_params.get('data', None)
        if model_id is not None:
            queryset = models.Resource.objects.filter(model=model_id).values()
            page = self.paginate_queryset(queryset)
            if data is not None:
                queryset = models.Resource.objects.filter(Q(data__icontains=data) & Q(model=model_id)).values()
                page = self.paginate_queryset(queryset)
        else:
            queryset = models.Resource.objects.all()
            page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "code": 20000,
            "data": serializer.data,
            "message": "success"
        }
        return JsonResponse(data, status=status.HTTP_200_OK)

    def get_data(self, result):
        s, m = has_resource_verify(result)
        if s:
            serializer = self.get_serializer(data=result)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return serializer.data
        else:
            return False

    def create(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            params = request.data.get("data", "")
            if params == "":
                res["code"] = 40000
                res["message"] = "创建资源失败"
            elif isinstance(params, list):
                for d in params:
                    dataValue = {
                        "model": request.data.get("model"),
                        "data": d
                    }
                    existing_data = models.Resource.objects.filter(model=request.data.get("model"), data=d).first()
                    if existing_data:
                        continue
                    try:
                        database_entry = models.Resource.objects.get(model=request.data.get("model"), data__contains=d)
                        database_entry.data = d
                        database_entry.save()
                    except models.Resource.DoesNotExist:
                        result = self.get_data(dataValue)
                        if result:
                            res["data"] = result
                        else:
                            res["code"] = 40000
                            res["message"] = "创建资源错误"
            elif isinstance(params, dict):
                s, m = has_resource_verify(request.data)
                if s:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    res["data"] = serializer.data
                else:
                    res["code"] = 40000
                    res["message"] = m
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"创建资源数据失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            s, m = has_resource_verify(request.data)
            print(s,m)
            if s:
                partial = kwargs.pop('partial', False)
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                if getattr(instance, '_prefetched_objects_cache', None):
                    instance._prefetched_objects_cache = {}
                res["data"] = serializer.data
            else:
                res["code"] = 40000
                res["message"] = m
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"更新资源数据失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


# 资源关联
class ResourceRelatedViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.ResourceRelated.objects.all()
    serializer_class = serializers.ResourceSerializer





## 所有批量导入
class ExcelHostView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def host_excel_data(self, recv_data):
        host_info_list = []
        serializers_all_list = []
        res_data = {}
        res_error_data = []
        data = xlrd.open_workbook(file_contents=recv_data.getvalue())
        sheet = data.sheet_by_index(0)
        rows_count = sheet.nrows
        for row_number in range(1, rows_count):
            one_row_dict = {
                "serverId": sheet.cell_value(row_number, 0),
                "serverName": sheet.cell_value(row_number, 1),
                "softSystem": sheet.cell_value(row_number, 2),
                "softEnvironment": sheet.cell_value(row_number, 3),
                "idc": sheet.cell_value(row_number, 4),
                "region": sheet.cell_value(row_number, 5),
                "serverType": sheet.cell_value(row_number, 6),
                "affiliatedCluster": sheet.cell_value(row_number, 7),
                "cpu": sheet.cell_value(row_number, 8),
                "memory": sheet.cell_value(row_number, 9),
                "disk": sheet.cell_value(row_number, 10),
                "private_ip": sheet.cell_value(row_number, 11),
                "public_ip": sheet.cell_value(row_number, 12),
                "status": sheet.cell_value(row_number, 13),
                "create_time": sheet.cell_value(row_number, 14),
                "descraption": sheet.cell_value(row_number, 15)
            }
            host_info_list.append(one_row_dict)
        for k, value_host in enumerate(host_info_list):
            serializer = serializers.AllServerSerializer(data=value_host)
            print(serializer)
            if serializer.is_valid():
                new_host_obj = serializer.save()
                serializers_all_list.append(new_host_obj)
            else:
                res_error_data.append({'error': f'该{k + 1}行数据有误,其他没有问题的数据，已经添加成功了，请求失败数据改完之后，重新上传这个错误数据，成功的数据不需要上传了'})
        serializer = serializers.AllServerSerializer(instance=serializers_all_list, many=True)
        res_data['data'] = serializer.data
        res_data['error'] = res_error_data
        return res_data

    def post(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            excel_file = request.FILES.get('host_file', None)
            sio = BytesIO()
            for i in excel_file:
                sio.write(i)
            res["data"] = self.host_excel_data(sio)
            return JsonResponse(res)
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"上传文件失败，{e}"
        return JsonResponse(res)


class cmdbPieChart(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (AllowAny,)
    #permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            total_dict = []
            hwCmdb1 = {"pltform": "华为云jdo_hcp3", "data": models.Resource.objects.filter(
                Q(data__icontains="jdo_hcp3")
            ).count()}
            hwCmdb2 = {"pltform": "华为云hz_jiache", "data": models.Resource.objects.filter(
                Q(data__icontains="hz_jiache")
            ).count()}
            hwCmdb3 = {"pltform": "华为云jdo_asterix", "data": models.Resource.objects.filter(
                Q(data__icontains="jdo_asterix")
            ).count()}
            volcanoCmdb = {"pltform": "火山引擎2100366728", "data": models.Resource.objects.filter(
                Q(data__icontains="2100366728")
            ).count()}
            total_dict.append(hwCmdb1)
            total_dict.append(hwCmdb2)
            total_dict.append(hwCmdb3)
            total_dict.append(volcanoCmdb)
            res['data'] = total_dict
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询CMDB饼图数据失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


class cmdbPieType(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (AllowAny,)
    # permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            total_dict = []
            hwc_ecs = {"pltform": "华为云ECS", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="ecs_id")).count()}
            hwc_rds = {"pltform": "华为云RDS", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="rds_id")).count()}
            hwc_elp = {"pltform": "华为云ELP", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="elp_id")).count()}
            hwc_elb = {"pltform": "华为云ELB", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="elb_id")).count()}
            hwc_cbr = {"pltform": "华为云CBR", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="cbr_id")).count()}
            hwc_redis = {"pltform": "华为云Redis", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="redis_id")).count()}
            hwc_rabbitmq = {"pltform": "华为云RabbitMQ", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="rabbitmq_id")).count()}
            hwc_vpc = {"pltform": "华为云VPC", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="vpc_id")).count()}
            hwc_nat = {"pltform": "华为云NAT", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="nat_id")).count()}
            hwc_dnat = {"pltform": "华为云DNAT", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="dnat_id")).count()}
            hwc_secgrouprule = {"pltform": "华为云安全组规则", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="secgrouprule_id")).count()}
            hwc_ipgroup = {"pltform": "华为云IP组", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="ipgroup_id")).count()}
            hwc_routetable = {"pltform": "华为云路由表", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="routetable_id")).count()}
            hwc_subnet = {"pltform": "华为云子网", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="subnet_id")).count()}
            hwc_snat = {"pltform": "华为云SNAT", "data": models.Resource.objects.exclude(model=25).exclude(model=26).filter(Q(data__icontains="snat_id")).count()}
            volcano_ecs = {"pltform": "火山引擎ECS", "data": models.Resource.objects.filter(Q(data__icontains="vecs_id")).count()}
            total_dict.append(hwc_ecs)
            total_dict.append(hwc_rds)
            total_dict.append(hwc_elp)
            total_dict.append(hwc_elb)
            #total_dict.append(hwc_cbr)
            #total_dict.append(hwc_redis)
            #total_dict.append(hwc_rabbitmq)
            total_dict.append(hwc_vpc)
            total_dict.append(hwc_nat)
            #total_dict.append(hwc_dnat)
            #total_dict.append(hwc_secgrouprule)
            #total_dict.append(hwc_ipgroup)
            #total_dict.append(hwc_routetable)
            #total_dict.append(hwc_subnet)
            #total_dict.append(hwc_snat)
            total_dict.append(volcano_ecs)
            res['data'] = total_dict
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询CMDB资产各类型数据失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


class cmdbTransverseChart(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (AllowAny,)
    # permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            total_dict = []
            txCmdb = {"pltform": "云资源(华为云)", "data": models.Resource.objects.count()}
            aliCmdb = {"pltform": "云资源(阿里云)", "data": models.Resource.objects.filter(Q(data__icontains="阿里云")).count()}
            volcanoCmdb = {"pltform": "云资源(火山引擎)", "data": models.Resource.objects.filter(Q(data__icontains="2100366728")).count()}
            netCmdb = {"pltform": "本地机房", "data": models.Resource.objects.filter(Q(data__icontains="网络设备")).count()}
            secCmdb = {"pltform": "网络设备", "data": models.Resource.objects.filter(Q(data__icontains="安全设备")).count()}
            total_dict.append(txCmdb)
            total_dict.append(aliCmdb)
            total_dict.append(volcanoCmdb)
            total_dict.append(netCmdb)
            total_dict.append(secCmdb)
            res['data'] = total_dict
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询CMDB柱状图数据失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


class cmdbTotalChart(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (AllowAny,)
    # permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            total_cmdb = {
                "total": models.Resource.objects.all().count(),
                "success": models.Resource.objects.filter(Q(data__icontains="ACTIVE") | Q(data__icontains="active") | Q(data__icontains="RUNNING") | Q(data__icontains="Running" ) | Q(data__icontains="rule")| Q(data__icontains="NORMAL") | Q(data__icontains="OK") | Q(data__icontains="available") | Q(data__icontains="ONLINE") ).count(),
                "warning": models.Resource.objects.filter(Q(data__icontains="Stopped") | Q(data__icontains="inactive")).count()
            }
            res['data'] = total_cmdb
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询CMDB总数数据失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)


class serviceClassification(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (AllowAny,)
    # permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            business_queries = [
                {"business": "业务一", "queries": ["交投"]},
                {"business": "业务二", "queries": [  "k8s"]},
                {"business": "业务三", "queries": [  "k8s"]},
                {"business": "业务四", "queries": [ ]},
                {"business": "业务五", "queries": [ ]},
                {"business": "业务六", "queries": [ ]},
                {"business": "业务七", "queries": [ ]},
                {"business": "业务八", "queries": [ ]},
                {"business": "业务九", "queries": [ ]},
                {"business": "业务十", "queries": [ ]},
            ]
            service_statistics = []
            for biz in business_queries:
                q_objects = Q()
                for query in biz["queries"]:
                    q_objects |= Q(data__icontains=query)
                count = models.Resource.objects.filter(q_objects).count()
                service_statistic = {"business": biz["business"], "data": count}
                service_statistics.append(service_statistic)
            res['data'] = service_statistics
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"业务分类数据查询失败，{e}"
        return JsonResponse(res, status=status.HTTP_200_OK)



class ExecuteHuaweiScript(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            sync_lock, created = SyncLock.objects.get_or_create(id=2)
            logger.info(f"当前锁状态: {sync_lock.is_locked}")
            if sync_lock.is_locked:
                return JsonResponse({
                    "code": 40000,
                    "data": "",
                    "message": "有其他用户正在同步资源数据，请等待同步完成"
                }, status=status.HTTP_200_OK)
            
            # 设置同步锁
            sync_lock.is_locked = True
            sync_lock.save()
            logger.info(f"锁状态更新为: {sync_lock.is_locked}")

            # 删除resource表里的所有数据
            models.Resource.objects.all().delete()
            print("正在执行同步脚本")
            
            # 获取完整的认证token
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header:
                raise Exception("未找到认证token")
            
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'agent', 'huawei.py')
            script_path2 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'agent', 'volcano.py')
            
            # 将完整的认证header传递给脚本
            result = subprocess.run(['python3', script_path, auth_header], capture_output=True, text=True)
            rusult2 = subprocess.run(['python3', script_path2], capture_output=True, text=True)  
            
            res["data"] = result.stdout + rusult2.stdout
            if result.stderr:
                print(f"Script error output: {result.stderr}")
                res["message"] = f"脚本执行成功,但有错误输出: {result.stderr}"
            sync_lock.is_locked = False
            sync_lock.save()
        except Exception as e:
            print(f"Error executing script: {str(e)}")
            res["code"] = 40000
            res["message"] = f"执行同步脚本失败: {str(e)}"
            # 确保发生异常时也释放锁
            if 'sync_lock' in locals():
                sync_lock.is_locked = False
                sync_lock.save()
        return JsonResponse(res, status=status.HTTP_200_OK)
    

## 全局搜索
class searchGlobal(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.Resource.objects.all()
    serializer_class = serializers.ResourceSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.ResourceFilter

    def list(self, request, *args, **kwargs):
        data = self.request.query_params.get('data', None)
        if data is not None:
            #queryset = models.Resource.objects.filter(Q(data__icontains=data)).values()
            queryset = models.Resource.objects.annotate(lower_data=Lower('data')).filter(lower_data__icontains=data.lower())
            serializer = self.get_serializer(queryset, many=True)
            queryset_service = models.HostService.objects.annotate(lower_service_command=Lower('service_command')).filter(lower_service_command__icontains=data.lower())
            serializer_service = serializers.HostServiceSerializer(queryset_service, many=True)
            
            queryset_host_details = models.HostDetails.objects.annotate(
                lower_agent_id=Lower('agent_id'),
                lower_host_ip=Lower('host_ip'),
                lower_host_name=Lower('host_name'),
                lower_platform=Lower('platform'),
                lower_version=Lower('version')
            ).filter(
                    Q(lower_agent_id__icontains=data.lower()) |
                    Q(lower_host_ip__icontains=data.lower()) |
                    Q(lower_host_name__icontains=data.lower()) |
                    Q(lower_platform__icontains=data.lower()) |
                    Q(lower_version__icontains=data.lower())
                )
            serializer_host_details = serializers.HostDetailsSerializer(queryset_host_details, many=True)
            queryset_host_rpm = models.HostRpm.objects.annotate(
                lower_agent_id=Lower('related_agent_id'),
                lower_rpm_name=Lower('rpm_name'),
                lower_architecture=Lower('architecture'),
                lower_version=Lower('version'),
                lower_vendor=Lower('vendor'),
                lower_description=Lower('description')
            ).filter(
                    Q(lower_agent_id__icontains=data.lower()) |
                    Q(lower_rpm_name__icontains=data.lower()) |
                    Q(lower_version__icontains=data.lower()) |
                    Q(lower_architecture__icontains=data.lower()) |
                    Q(lower_vendor__icontains=data.lower()) |
                    Q(lower_description__icontains=data.lower())
                )
            serializer_host_rpm = serializers.HostRpmSerializer(queryset_host_rpm, many=True)
            queryset_host_process = models.HostProcess.objects.annotate(
                lower_agent_id=Lower('related_agent_id'),
                lower_name=Lower('name'),
                lower_egroup=Lower('egroup'),
                lower_pid=Lower('pid'),
                lower_ppid=Lower('ppid'),
                lower_cmd=Lower('cmd'),
                lower_argvs=Lower('argvs'),
                lower_vm_size=Lower('vm_size'),
                lower_size=Lower('size'),
                lower_session=Lower('session'),
                lower_priority=Lower('priority'),
                lower_state=Lower('state')
            ).filter(
                    Q(lower_agent_id__icontains=data.lower()) |
                    Q(lower_name__icontains=data.lower()) |
                    Q(lower_egroup__icontains=data.lower()) |
                    Q(lower_pid__icontains=data.lower()) |
                    Q(lower_ppid__icontains=data.lower()) |
                    Q(lower_cmd__icontains=data.lower()) |
                    Q(lower_argvs__icontains=data.lower()) |
                    Q(lower_vm_size__icontains=data.lower()) |
                    Q(lower_size__icontains=data.lower()) |
                    Q(lower_session__icontains=data.lower()) |
                    Q(lower_priority__icontains=data.lower()) |
                    Q(lower_state__icontains=data.lower())
                )
            serializer_host_process = serializers.HostProcessSerializer(queryset_host_process, many=True)

            queryset_host_port = models.HostPort.objects.annotate(
                lower_related_agent_id=Lower('related_agent_id'),
                lower_local_ip=Lower('local_ip'),
                lower_local_port=Lower('local_port'),
                lower_remote_ip=Lower('remote_ip'),
                lower_remote_port=Lower('remote_port'),
                lower_protocol=Lower('protocol'),
                lower_process=Lower('process'),
                lower_pid=Lower('pid'),
                lower_state=Lower('state')
            ).filter(
                    Q(lower_related_agent_id__icontains=data.lower()) |
                    Q(lower_local_ip__icontains=data.lower()) |
                    Q(lower_local_port__icontains=data.lower()) |
                    Q(lower_remote_ip__icontains=data.lower()) |
                    Q(lower_remote_port__icontains=data.lower()) |
                    Q(lower_protocol__icontains=data.lower()) |
                    Q(lower_process__icontains=data.lower()) |
                    Q(lower_pid__icontains=data.lower()) |
                    Q(lower_state__icontains=data.lower())
                )
            serializer_host_port = serializers.HostPortSerializer(queryset_host_port, many=True)









            combined_list = serializer.data + serializer_service.data + serializer_host_details.data + serializer_host_rpm.data + serializer_host_process.data + serializer_host_port.data
            for item in combined_list:
                if 'model' in item:  
                    model_id = item['model']
                    model_name = self.get_model_name(model_id)  
                    item['model_name'] = "模型资源" + model_name 
                elif 'rpm_name' in item:
                    item['model_name'] = "主机RPM包信息"
                elif 'session' in item:
                    item['model_name'] = "主机进程信息"
                elif 'host_name' in item:
                    item['model_name'] = "主机基本信息"
                elif 'remote_port' in item:
                    item['model_name'] = "主机端口信息"
                else:
                    item['model_name'] = "未知"



            data = {
                "code": 20000,
                "data": {
                    "total": len(combined_list),
                    "list": combined_list
                },
                "message": "success111"
            }
            return JsonResponse(data, status=status.HTTP_200_OK)

    def get_model_name(self, model_id):
        try:
            model = models.Model.objects.get(id=model_id)
            return model.name
        except models.Model.DoesNotExist:
            return None
        

logger = logging.getLogger(__name__)
#保存每台主机上的服务名称
class HostServiceView(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    

    def list(self, request, *args, **kwargs):
        queryset = models.HostService.objects.all()
        serializer = serializers.HostServiceSerializer(queryset, many=True)
        data = {
            "code": 20000,
            "data": serializer.data,
            "message": "success"
        }
        return JsonResponse(data, status=status.HTTP_200_OK)

    
    def create(self, request, *args, **kwargs):
        try:
            data = request.data  # 假设每次只发送一条数据
            logger.debug(f"接收到的数据: {data}")

            host_ip = data["host_ip"]
            service_command = data["service_command"]

            if not host_ip or not service_command:
                return Response({"error": "缺少必要的数据"}, status=status.HTTP_400_BAD_REQUEST)

            # 将 service_command 直接存储为 JSON
            existing_record = models.HostService.objects.filter(host_ip=host_ip).first()

            if existing_record:
                serializer = serializers.HostServiceSerializer(existing_record, data=data)
            else:
                serializer = serializers.HostServiceSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "数据保存成功",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"数据验证失败: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"处理请求时发生错误: {str(e)}")
            return Response({"error": "服务器内部错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        






#wazuh搜集的每台主机上的基本信息
class HostDetailsView(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    

    def list(self, request, *args, **kwargs):
        queryset = models.HostDetails.objects.all()
        serializer = serializers.HostDetailsSerializer(queryset, many=True)
        data = {
            "code": 20000,
            "data": serializer.data,
            "message": "success"
        }
        return JsonResponse(data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        try:
            wazuh_url = "https://172.16.15.148:55000/security/user/authenticate"
            auth = ('wazuh-wui', 'MyS3cr37P450r.*-')
            res = requests.post(wazuh_url, auth=auth, verify=False)
            token = res.json()["data"]["token"]

            # 使用token获取agents数据
            agents_url = "https://172.16.15.148:55000/agents"
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(agents_url, headers=headers, verify=False)
            agents_data = response.json()["data"]["affected_items"]

            # 处理并保存每个agent的数据
            saved_data = []
            for agent in agents_data:
                data = {
                    "agent_id": agent.get("id"),
                    "host_ip": agent.get("ip"),
                    "host_name": agent.get("name"),
                    "platform": agent.get("os", {}).get("platform"),
                    "version": agent.get("os", {}).get("version"),
                    "status": agent.get("status")
                }
                existing_record = models.HostDetails.objects.filter(agent_id=data['agent_id']).first()
            
                if existing_record:
                    if not all(getattr(existing_record, key) == value for key, value in data.items()):
                        serializer = serializers.HostDetailsSerializer(existing_record, data=data)
                        if serializer.is_valid():
                            serializer.save()
                            saved_data.append(serializer.data)
                    else:
                        # 数据没有变化，不需要更新
                        saved_data.append(serializers.HostDetailsSerializer(existing_record).data)
                else:
                    serializer = serializers.HostDetailsSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        saved_data.append(serializer.data)
                    else:
                        print(f"数据验证失败: {serializer.errors}")

            res = {
                "code": 20000,
                "data": saved_data,
                "message": "数据已成功从Wazuh API获取并保存"
            }
            return JsonResponse(res, status=status.HTTP_201_CREATED)
        except Exception as e:
            res = {
                "code": 40000,
                "data": "",
                "message": f"获取或保存数据时发生错误: {str(e)}"
            }
            return JsonResponse(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

#wazuh搜集的每台主机上的rpm包信息
class HostRpmViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    

    def list(self, request, *args, **kwargs):
        related_agent_id = request.query_params.get('id', None)
        print("related_agent_id:",related_agent_id)
        queryset = models.HostRpm.objects.all()

        if related_agent_id is not None:
            queryset = queryset.filter(related_agent__agent_id=related_agent_id)

        serializer = serializers.HostRpmSerializer(queryset, many=True)
        data = {
            "code": 2000000000000000000000,
            "data": serializer.data,
            "message": "success"
        }
        return JsonResponse(data, status=status.HTTP_200_OK)
    
    #获得某台主机上的rpm包信息
    def retrieve(self, request, pk=None):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        if pk is not None:
            print("pk:",pk)
            rpm = models.HostRpm.objects.filter(related_agent_id=pk)
            if rpm.exists():
                serializer = serializers.HostRpmSerializer(rpm, many=True)
                res["data"] = serializer.data
                return JsonResponse(res, status=status.HTTP_200_OK)
            else:
                res["message"] = "没有找到对应的RPM信息"
                return JsonResponse(res, status=status.HTTP_404_NOT_FOUND)

        else:
            res["message"] = "无效的ID"
            return JsonResponse(res, status=status.HTTP_400_BAD_REQUEST)
        



#更新每台主机上的rpm包信息（无需使用，使用全局更新）
    def create(self, request, *args, **kwargs):
        try:
            wazuh_url = "https://172.16.15.148:55000/security/user/authenticate"
            auth = ('wazuh-wui', 'MyS3cr37P450r.*-')
            res = requests.post(wazuh_url, auth=auth, verify=False)
            token = res.json()["data"]["token"]

            agents_url = "https://172.16.15.148:55000/experimental/syscollector/packages"
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(agents_url, headers=headers, verify=False)
            agents_data = response.json()["data"]["affected_items"]

            saved_data = []
            for agent in agents_data:
                data = {
                    "agent_id": agent.get("agent_id"),
                    "rpm_name": agent.get("name"), 
                    "architecture": agent.get("architecture"),
                    "version": agent.get("version"),
                    "vendor": agent.get("vendor"),
                    "description": agent.get("description")
                }
            
                existing_record = models.HostRpm.objects.filter(
                related_agent__agent_id=data['agent_id'],
                rpm_name=data['rpm_name']
                ).first()
            
                if existing_record:
                    serializer = serializers.HostRpmSerializer(existing_record, data=data)
                else:
                    serializer = serializers.HostRpmSerializer(data=data)
                
                if serializer.is_valid():
                    serializer.save()
                    saved_data.append(serializer.data)
                else:
                    print("Serializer errors:", serializer.errors)

            res = {
                "code": 20000,
                "data": saved_data,
                "message": "rpm包信息已成功从Wazuh API获取并保存"
            }
            return JsonResponse(res, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"获取或保存数据时发生错误: {str(e)}")
            res = {
                "code": 40000,
                "data": "",
                "message": f"获取或保存数据时发生错误: {str(e)}"
            }
            return JsonResponse(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class HostProcessViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.HostProcess.objects.all()
    serializer_class = serializers.HostProcessSerializer

    def retrieve(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get host process"
        }
        pk = kwargs.get('pk')
        queryset = self.get_queryset()
        if pk is not None:
            queryset = queryset.filter(related_agent__agent_id=pk)
        serializer = self.get_serializer(queryset, many=True)
        res["data"] = serializer.data
        return JsonResponse(res, status=status.HTTP_200_OK)





class UpdateAllHostDetailsView(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def fetch(self, request, *args, **kwargs):
        try:
            # 获取或创建同步锁记录
            sync_lock, created = SyncLock.objects.get_or_create(id=1)
            logger.info(f"当前锁状态: {sync_lock.is_locked}")
            if sync_lock.is_locked:
                return JsonResponse({
                    "code": 40000,
                    "data": "",
                    "message": "有其他用户正在同步数据，请等待同步完成"
                }, status=status.HTTP_200_OK)
            
            # 设置同步锁
            logger.info(f"上次锁更新时间: {sync_lock.locked_at}")
            sync_lock.is_locked = True
            sync_lock.save()
            logger.info(f"锁状态更新为: {sync_lock.is_locked}")
            # 进行数据同步操作
            # ...（原有的同步逻辑代码）
            wazuh_url = "https://172.16.15.148:55000/security/user/authenticate"
            auth = ('wazuh-wui', 'MyS3cr37P450r.*-')
            res = requests.post(wazuh_url, auth=auth, verify=False)
            token = res.json()["data"]["token"]
            max_retries = 3
            AGENT_data = []
            RPM_data = []
            PROCESS_data = []
            PORT_data = []
            # 获取所有主机信息
            agents_url = "https://172.16.15.148:55000/agents"
            headers = {'Authorization': f'Bearer {token}'}
            for attempt in range(max_retries):
                try:
                    response_agents = requests.get(agents_url, headers=headers, verify=False)
                    response_agents.raise_for_status()
                    agents_data = response_agents.json()["data"]["affected_items"]
                    break  # 成功后退出循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取主机信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取所有主机上安装的rpm包的信息
            agents_url = "https://172.16.15.148:55000/experimental/syscollector/packages?limit=1000&wait_for_complete=true"
            for attempt in range(max_retries):
                try:
                    response_rpm = requests.get(agents_url, headers=headers, verify=False)
                    response_rpm.raise_for_status()
                    rpm_data = response_rpm.json()["data"]["affected_items"]
                    break  # 成功后退出循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取rpm信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取所有主机上安装的进程的信息
            agents_url = "https://172.16.15.148:55000/experimental/syscollector/processes?limit=1000&wait_for_complete=true"
            for attempt in range(max_retries):
                try:
                    response_process = requests.get(agents_url, headers=headers, verify=False)
                    response_process.raise_for_status()
                    process_data = response_process.json()["data"]["affected_items"]
                    break  # 成功后退出循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取进程信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取所有主机上安装的端口的信息
            agents_url = "https://172.16.15.148:55000/experimental/syscollector/ports?limit=1000&wait_for_complete=true"
            for attempt in range(max_retries):
                try:
                    response_port = requests.get(agents_url, headers=headers, verify=False)
                    response_port.raise_for_status()
                    port_data = response_port.json()["data"]["affected_items"]
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取端口信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

            # 处理并保存每个agent的主机信息和rpm包的信息
            for agent in agents_data:
                agent_info = {
                    "agent_id": agent.get("id"),
                    "host_ip": agent.get("ip"),
                    "host_name": agent.get("name"),
                    "platform": agent.get("os", {}).get("platform"),
                    "version": agent.get("os", {}).get("version"),
                    "status": agent.get("status")
                }
                AGENT_data.append(agent_info)
            for rpm in rpm_data:
                rpm_info = {
                    "agent_id": rpm.get("agent_id"),
                    "rpm_name": rpm.get("name"), 
                    "architecture": rpm.get("architecture"),
                    "version": rpm.get("version"),
                    "vendor": rpm.get("vendor"),
                    "description": rpm.get("description")
                }
                RPM_data.append(rpm_info)

            for process in process_data:
                process_info = {
                    "related_agent": process.get("agent_id"),
                    "name": process.get("name"),
                    "egroup": process.get("egroup"),
                    "pid": process.get("pid"),
                    "ppid": process.get("ppid"),
                    "cmd": process.get("cmd"),
                    "argvs": process.get("argvs"),
                    "vm_size": process.get("vm_size"),
                    "size": process.get("size"),
                    "session": process.get("session"),
                    "priority": process.get("priority"),
                    "state": process.get("state")
                }
                PROCESS_data.append(process_info)
            for port in port_data:
                port_info = {
                    "related_agent": port.get("agent_id"),
                    "local_ip": port.get("local", {}).get("ip"),
                    "local_port": port.get("local", {}).get("port"),
                    "remote_ip": port.get("remote", {}).get("ip"),
                    "remote_port": port.get("remote", {}).get("port"),
                    "process": port.get("process"),
                    "pid": port.get("pid"),
                    "state": port.get("state"),
                    "protocol": port.get("protocol")
                }
                PORT_data.append(port_info)
            
            # 删除已存在的数据
            models.HostDetails.objects.all().delete()
            models.HostRpm.objects.all().delete()
            models.HostProcess.objects.all().delete()
            models.HostPort.objects.all().delete()
            # 保存新拿到的数据
            serializer_agent = serializers.HostDetailsSerializer(data=AGENT_data, many=True)
            if serializer_agent.is_valid():
                serializer_agent.save()
                print("保存主机信息")
            else:
                print("Serializer errors:", serializer_agent.errors)
            
            serializer_rpm = serializers.HostRpmSerializer(data=RPM_data, many=True)
            if serializer_rpm.is_valid():
                serializer_rpm.save()
                print("保存rpm信息")
            else:
                print("Serializer errors:", serializer_rpm.errors)
            
            serializer_process = serializers.HostProcessSerializer(data=PROCESS_data, many=True)
            if serializer_process.is_valid():
                serializer_process.save()
                print("保存进程信息")
            else:
                print("Serializer errors:", serializer_process.errors)

            serializer_port = serializers.HostPortSerializer(data=PORT_data, many=True)
            if serializer_port.is_valid():
                serializer_port.save()
                print("保存端口信息")
            else:
                print(f"端口信息验证失败: {serializer_port.errors}")

            # 同步完成，释放锁
            sync_lock.is_locked = False
            sync_lock.save()

            res = {
                "code": 20000,
                "data": AGENT_data,
                "message": "同步成功"
            }
            return JsonResponse(res, status=status.HTTP_200_OK)

        except Exception as e:
            try:
                sync_lock.is_locked = False
                sync_lock.save()
            except:
                pass
            print(f"同步过程中发生错误: {str(e)}")
            res = {
                "code": 40000,
                "data": "",
                "message": f"同步过程中发生错误: {str(e)}"
            }
            return JsonResponse(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










#更新数据库中每台主机上的主机信息，rpm包信息，进程信息
class UpdateAllHostDetailsViewBack(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    #删除原来的数据，更新每台主机上的主机信息和rpm包信息
    def fetch(self, request, *args, **kwargs):
        try:
            # 调用Wazuh API获取所有主机信息
            wazuh_url = "https://172.16.15.148:55000/security/user/authenticate"
            auth = ('wazuh-wui', 'MyS3cr37P450r.*-')
            res = requests.post(wazuh_url, auth=auth, verify=False)
            token = res.json()["data"]["token"]
            max_retries = 3
            AGENT_data = []
            RPM_data = []
            PROCESS_data = []
            PORT_data = []
            # 获取所有主机信息
            agents_url = "https://172.16.15.148:55000/agents"
            headers = {'Authorization': f'Bearer {token}'}
            for attempt in range(max_retries):
                try:
                    response_agents = requests.get(agents_url, headers=headers, verify=False)
                    response_agents.raise_for_status()
                    agents_data = response_agents.json()["data"]["affected_items"]
                    break  # 成功后退出循环
                except Exception as e:
                    if attempt < max_retries - 1:  # 还有剩余尝试次数
                        continue
                    else:
                        return Response({"error": "获取主机信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取所有主机上安装的rpm包的信息
            agents_url = "https://172.16.15.148:55000/experimental/syscollector/packages?limit=1000&wait_for_complete=true"
            for attempt in range(max_retries):
                try:
                    response_rpm = requests.get(agents_url, headers=headers, verify=False)
                    response_rpm.raise_for_status()
                    rpm_data = response_rpm.json()["data"]["affected_items"]
                    break  # 成功后退出循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取rpm信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取所有主机上安装的进程的信息
            agents_url = "https://172.16.15.148:55000/experimental/syscollector/processes?limit=1000&wait_for_complete=true"
            for attempt in range(max_retries):
                try:
                    response_process = requests.get(agents_url, headers=headers, verify=False)
                    response_process.raise_for_status()
                    process_data = response_process.json()["data"]["affected_items"]
                    break  # 成功后退出循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取进程信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取所有主机上安装的端口的信息
            agents_url = "https://172.16.15.148:55000/experimental/syscollector/ports?limit=1000&wait_for_complete=true"
            for attempt in range(max_retries):
                try:
                    response_port = requests.get(agents_url, headers=headers, verify=False)
                    response_port.raise_for_status()
                    port_data = response_port.json()["data"]["affected_items"]
                    break  # 成功后退出循环 
                except Exception as e:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return Response({"error": "获取端口信息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

            # 处理并保存每个agent的主机信息和rpm包的信息
            for agent in agents_data:
                agent_info = {
                    "agent_id": agent.get("id"),
                    "host_ip": agent.get("ip"),
                    "host_name": agent.get("name"),
                    "platform": agent.get("os", {}).get("platform"),
                    "version": agent.get("os", {}).get("version"),
                    "status": agent.get("status")
                }
                AGENT_data.append(agent_info)
            for rpm in rpm_data:
                rpm_info = {
                    "agent_id": rpm.get("agent_id"),
                    "rpm_name": rpm.get("name"), 
                    "architecture": rpm.get("architecture"),
                    "version": rpm.get("version"),
                    "vendor": rpm.get("vendor"),
                    "description": rpm.get("description")
                }
                RPM_data.append(rpm_info)

            for process in process_data:
                process_info = {
                    "related_agent": process.get("agent_id"),
                    "name": process.get("name"),
                    "egroup": process.get("egroup"),
                    "pid": process.get("pid"),
                    "ppid": process.get("ppid"),
                    "cmd": process.get("cmd"),
                    "argvs": process.get("argvs"),
                    "vm_size": process.get("vm_size"),
                    "size": process.get("size"),
                    "session": process.get("session"),
                    "priority": process.get("priority"),
                    "state": process.get("state")
                }
                PROCESS_data.append(process_info)
            for port in port_data:
                port_info = {
                    "related_agent": port.get("agent_id"),
                    "local_ip": port.get("local", {}).get("ip"),
                    "local_port": port.get("local", {}).get("port"),
                    "remote_ip": port.get("remote", {}).get("ip"),
                    "remote_port": port.get("remote", {}).get("port"),
                    "process": port.get("process"),
                    "pid": port.get("pid"),
                    "state": port.get("state"),
                    "protocol": port.get("protocol")
                }
                PORT_data.append(port_info)
            
            # 删除已存在的数据
            models.HostDetails.objects.all().delete()
            models.HostRpm.objects.all().delete()
            models.HostProcess.objects.all().delete()
            models.HostPort.objects.all().delete()
            # 保存新拿到的数据
            serializer_agent = serializers.HostDetailsSerializer(data=AGENT_data, many=True)
            if serializer_agent.is_valid():
                serializer_agent.save()
                print("保存主机信息")
            else:
                print("Serializer errors:", serializer_agent.errors)
            
            serializer_rpm = serializers.HostRpmSerializer(data=RPM_data, many=True)
            if serializer_rpm.is_valid():
                serializer_rpm.save()
                print("保存rpm信息")
            else:
                print("Serializer errors:", serializer_rpm.errors)
            
            serializer_process = serializers.HostProcessSerializer(data=PROCESS_data, many=True)
            if serializer_process.is_valid():
                serializer_process.save()
                print("保存进程信息")
            else:
                print("Serializer errors:", serializer_process.errors)

            serializer_port = serializers.HostPortSerializer(data=PORT_data, many=True)
            if serializer_port.is_valid():
                serializer_port.save()
                print("保存端口信息")
            else:
                print("Serializer errors:", serializer_port.errors)
            #返回主机详情信息
            res = {
                "code": 20000,
                "data": AGENT_data,
                "message": "success"
            }
            return JsonResponse(res, status=status.HTTP_200_OK)
        except Exception as e:
            res = {
                "code": 40000,
                "data": "",
                "message": f"获取或保存数据时发生错误: {str(e)}"
            }
            return JsonResponse(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HostHardwareViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get host hardware"
        }
        wazuh_url = "https://172.16.15.148:55000/security/user/authenticate"
        auth = ('wazuh-wui', 'MyS3cr37P450r.*-')
        response = requests.post(wazuh_url, auth=auth, verify=False)
        token = response.json()["data"]["token"]
        agent_id = kwargs.get('pk')
        url = f"https://172.16.15.148:55000/syscollector/{agent_id}/hardware?wait_for_complete=true"
        print("url:",url)   
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers, verify=False)
        data = response.json()["data"]["affected_items"]
        print("data:",data)
        res["data"] = data
        return JsonResponse(res, status=status.HTTP_200_OK)

class HostPortViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.HostPort.objects.all()
    serializer_class = serializers.HostPortSerializer

    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get host port"
        }
        pk = kwargs.get('pk')
        queryset = self.get_queryset()
        if pk is not None:
            queryset = queryset.filter(related_agent__agent_id=pk)
        serializer = self.get_serializer(queryset, many=True)
        res["data"] = serializer.data
        return JsonResponse(res, status=status.HTTP_200_OK)


