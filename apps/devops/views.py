from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from pkg.custom_model_view_set import CustomModelViewSet
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.cmdb.models import Resource
from .serializers import RdsManagementSerializer
from django.http import JsonResponse
import os
import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkrds.v3.region.rds_region import RdsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkrds.v3 import *
from .k8s.list import *
from .k8s.apply import *
from .k8s.action import *
from .k8s.image import *
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import partial




class RdsManagementViewSet(CustomModelViewSet):
    """
    RDS管理视图集
    用于管理和查询RDS资源
    """
    
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = RdsManagementSerializer
    queryset = Resource.objects.filter(model=4)

    @action(detail=False, methods=['get'])
    def list(self, request):
        """
        获取RDS资源列表
        
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [RDS资源列表],
                "message": "success to get model four resources"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get model four resources"
        }
        resources = self.get_queryset()
        serializer = self.get_serializer(resources, many=True)
        res["data"] = serializer.data
        return JsonResponse(res)
    
class RdsBackupViewSet(CustomModelViewSet):
    """
    RDS备份管理视图集
    用于管理RDS备份操作
    """
    
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = RdsManagementSerializer
    queryset = Resource.objects.filter(model=5)
    
    # 获取项目根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 配置文件路径
    hz_jiache_config_path = os.path.join(BASE_DIR, 'agent/config/hz_jiache_config.json')
    
    with open(hz_jiache_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    def list(self, request, *args, **kwargs):
        """
        获取RDS备份列表
        
        Args:
            request.query_params:
                account: 华为云账号
                region: 区域
                rds_id: RDS实例ID
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [备份列表],
                "message": "success to get backup list"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get backup list"
        }
        account = request.query_params.get("account")
        region = request.query_params.get("region")
        
        regions_reverse = {v: k for k, v in self.config[account]["regions"].items()}
        region_id = regions_reverse.get(region)
        
        rds_id = request.query_params.get("rds_id")
        ak = self.config[account]["ak"]
        sk = self.config[account]["sk"]

        credentials = BasicCredentials(ak, sk)

        client = RdsClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(RdsRegion.value_of(region_id)) \
            .build()
        
        request = ListBackupsRequest()
        request.instance_id = rds_id
        request.limit = 10
        response = client.list_backups(request)
        res["data"] = response.to_dict()
        return JsonResponse(res)



    #获取参数region,account,rds_id,backup_name，创建备份
    @action(detail=False, methods=['post'])
    def create(self, request):
        """
        创建RDS备份
        
        Args:
            request.query_params:
                account: 华为云账号
                region: 区域
                rds_id: RDS实例ID
                backup_name: 备份名称
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [备份创建结果],
                "message": "success to create backup"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to create backup"
        }
        account = request.query_params.get("account")
        region = request.query_params.get("region")
        
        regions_reverse = {v: k for k, v in self.config[account]["regions"].items()}
        region_id = regions_reverse.get(region)
        
        rds_id = request.query_params.get("rds_id")
        ak = self.config[account]["ak"]
        sk = self.config[account]["sk"]
        backup_name = request.query_params.get("backup_name")
        credentials = BasicCredentials(ak, sk)

        client = RdsClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(RdsRegion.value_of(region_id)) \
            .build()

        request = CreateManualBackupRequest()
        request.body = CreateManualBackupRequestBody(
            name=backup_name,
            instance_id=rds_id
        )
        response = client.create_manual_backup(request)
        #print(response)
        res["data"] = response.to_dict()
        return JsonResponse(res)



class K8sViewSet(CustomModelViewSet):
    """
    Kubernetes资源管理视图集
    用于管理和操作Kubernetes集群资源
    """
    
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = RdsManagementSerializer
    queryset = Resource.objects.filter(model=5)



    #获取k8s集群列表
    @action(detail=False, methods=['get'])
    def get_k8s_cluster_list(self, request):
        """
        获取Kubernetes集群列表
        
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [集群列表],
                "message": "success to get k8s cluster list"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get k8s cluster list"
        }
        try:
            cluster_list = list_cluster()
            res["data"] = cluster_list
        except Exception as e:
            res["code"] = 50000  # 使用适当的错误码
            res["message"] = f"获取集群列表失败: {str(e)}"
        return JsonResponse(res)




    #获取k8s集群某种资源，参数为集群名，资源类型和可选的命名空间
    @action(detail=False, methods=['get'])
    def get_k8s_resource(self, request):
        """
        获取指定类型的Kubernetes资源列表
        
        Args:
            request.query_params:
                context: 集群上下文
                resource_kind: 资源类型
                namespace: 命名空间(可选)
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [资源列表],
                "message": "success to get k8s resource"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get k8s resource"
        }
        try:
            context = request.query_params.get("context")
            resource_kind = request.query_params.get("resource_kind")
            namespace = request.query_params.get("namespace")
            resources = list_cluster_resources(context, resource_kind, namespace)
            
            serializable_resources = []
            for resource in resources:
                try:
                    # 深度遍历字典，将所有值转换为基本类型
                    def convert_to_serializable(obj):
                        if isinstance(obj, dict):
                            return {k: convert_to_serializable(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_to_serializable(i) for i in obj]
                        else:
                            # 对于其他类型，转换为字符串
                            return str(obj) if hasattr(obj, '__dict__') else obj

                    serializable_resource = convert_to_serializable(dict(resource))
                    serializable_resources.append(serializable_resource)
                except Exception as e:
                    print(f"处理资源时出错: {str(e)}")
                    print(f"问题资源: {resource}")
                    
            res["data"] = serializable_resources
            return JsonResponse(res)
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取资源列表失败: {str(e)}"
            return JsonResponse(res)


    #获取k8s集群下所有命名空间
    @action(detail=False, methods=['get'])
    def get_k8s_namespace(self, request):
        """
        获取集群的命名空间列表
        
        Args:
            request.query_params:
                context: 集群上下文
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [命名空间列表],
                "message": "success to get k8s namespace"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get k8s namespace"
        }
        try:
            context = request.query_params.get("context")
            
            # 创建一个新的线程池，设置较短的超时时间
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(list_namespaces, context)
                try:
                    # 减少超时时间到1秒
                    namespaces = future.result(timeout=1)
                    res["data"] = namespaces
                except TimeoutError:
                    # 取消执行中的任务
                    future.cancel()
                    res["code"] = 50000
                    res["message"] = "连接集群超时(1秒)"
                    return JsonResponse(res)
                except Exception as e:
                    future.cancel()
                    res["code"] = 50000
                    res["message"] = f"连接集群失败: {str(e)}"
                    return JsonResponse(res)
                
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取命名空间列表失败: {str(e)}"
        return JsonResponse(res)


    #获取k8s集群下指定deployment的pod列表
    @action(detail=False, methods=['get'])
    def get_k8s_pod(self, request):
        """
        获取指定Deployment的Pod列表
        
        Args:
            request.query_params:
                context: 集群上下文
                deployment: Deployment名称
                namespace: 命名空间
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [Pod列表],
                "message": "success to get k8s pod"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get k8s pod"
        }
        try:
            context = request.query_params.get("context")
            deployment = request.query_params.get("deployment")
            namespace = request.query_params.get("namespace")
            pods = list_deployment_pods(context, deployment, namespace)
            res["data"] = pods
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取Pod列表失败: {str(e)}"
        return JsonResponse(res)



    #获取某个资源的yaml
    @action(detail=False, methods=['get'])
    def get_k8s_resource_yaml(self, request):
        """
        获取指定资源的YAML配置
        
        Args:
            request.query_params:
                context: 集群上下文
                resource_kind: 资源类型
                resource_name: 资源名称
                namespace: 命名空间
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": "YAML内容",
                "message": "success to get k8s resource yaml"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get k8s resource yaml"
        }
        try:
            context = request.query_params.get("context")
            resource_kind = request.query_params.get("resource_kind")
            resource_name = request.query_params.get("resource_name")
            namespace = request.query_params.get("namespace")
            yaml = get_resource_yaml(context, resource_kind, resource_name, namespace)
            res["data"] = yaml
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取资源YAML失败: {str(e)}"
        return JsonResponse(res)


    #获取某个pod的日志
    @action(detail=False, methods=['get'])
    def get_k8s_pod_logs(self, request):
        """
        获取指定Pod的日志
        
        Args:
            request.query_params:
                context: 集群上下文
                pod_name: Pod名称
                namespace: 命名空间
                container_name: 容器名称(可选)
                previous: 是否获取上一个容器的日志(可选)
                tail_lines: 返回的日志行数(可选)
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": "日志内容",
                "message": "success to get k8s pod logs"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get k8s pod logs"
        }
        try:
            context = request.query_params.get("context")
            pod_name = request.query_params.get("pod_name")
            namespace = request.query_params.get("namespace")
            
            container_name = request.query_params.get("container_name", None)
            previous = request.query_params.get("previous", None)
            tail_lines = request.query_params.get("tail_lines", None)
            
            if tail_lines is not None:
                try:
                    tail_lines = int(tail_lines)
                except ValueError:
                    tail_lines = None
                    
            if previous is not None:
                previous = previous.lower() == 'true'
            
            logs = get_pod_logs(
                context=context, 
                pod_name=pod_name, 
                namespace=namespace, 
                container_name=container_name, 
                previous=previous, 
                tail_lines=tail_lines
            )
            res["data"] = logs
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取Pod日志失败: {str(e)}"
        return JsonResponse(res)
    


    #创建k8s资源
    @action(detail=False, methods=['post'])
    def apply_resource_from_yaml(self, request):
        """
        通过YAML创建或更新资源
        
        Args:
            request.data:
                context: 集群上下文
                yaml_content: YAML配置内容
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [创建结果],
                "message": "success to create k8s resource"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to create k8s resource"
        }
        try:
            context = request.data.get("context")
            yaml_content = request.data.get("yaml_content")
            
            if not yaml_content:
                raise ValueError("yaml_content不能为空")
            if not context:
                raise ValueError("context不能为空")
                
            apply_result = apply_resource_from_yaml(yaml_content, context)
            
            # 检查结果中是否有失败的操作
            has_error = any(not item["success"] for item in apply_result)
            if has_error:
                error_messages = [item["message"] for item in apply_result if not item["success"]]
                res["code"] = 50000
                res["message"] = "部分或全部资源创建失败: " + "; ".join(error_messages)
            else:
                res["message"] = "所有资源创建成功"
                
            res["data"] = apply_result

        except Exception as e:
            res["code"] = 50000
            res["message"] = f"创建资源失败: {str(e)}"
        return JsonResponse(res)



    #重启k8s资源
    @action(detail=False, methods=['post'])
    def restart_workload(self, request):
        """
        重启工作负载
        
        Args:
            request.query_params:
                context: 集群上下文
                name: 资源名称
                namespace: 命名空间
                kind: 资源类型
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [重启结果],
                "message": "success to restart k8s workload"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to restart k8s workload"
        }
        try:
            context = request.query_params.get("context")
            name = request.query_params.get("name")
            namespace = request.query_params.get("namespace")
            kind = request.query_params.get("kind")
            restart_result = restart_workload(context, name, namespace, kind)
            res["data"] = restart_result
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"重启工作负载失败: {str(e)}"
        return JsonResponse(res)
    


    #删除k8s资源
    @action(detail=False, methods=['post'])
    def delete_workload(self, request):
        """
        删除工作负载
        
        Args:
            request.query_params:
                context: 集群上下文
                name: 资源名称
                namespace: 命名空间
                kind: 资源类型
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [删除结果],
                "message": "success to delete k8s workload"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to delete k8s workload"
        }
        try:
            context = request.query_params.get("context")
            name = request.query_params.get("name")
            namespace = request.query_params.get("namespace")
            kind = request.query_params.get("kind")
            delete_result = delete_workload(context, name, namespace, kind)
            res["data"] = delete_result
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"删除工作负载失败: {str(e)}"
        return JsonResponse(res)
    


    #扩缩容k8s资源
    @action(detail=False, methods=['get'])
    def scale_workload(self, request):
        """
        扩缩容工作负载
        
        Args:
            request.query_params:
                context: 集群上下文
                name: 资源名称
                namespace: 命名空间
                kind: 资源类型
                replicas: 期望的副本数
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [扩缩容结果],
                "message": "success to scale workload"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to scale workload"
        }
        try:
            context = request.query_params.get("context")
            name = request.query_params.get("name")
            namespace = request.query_params.get("namespace")
            kind = request.query_params.get("kind")
            replicas = request.query_params.get("replicas")
            
            if not replicas:
                raise ValueError("replicas参数不能为空")
            
            try:
                replicas = int(replicas)
            except ValueError:
                raise ValueError("replicas必须是有效的整数")
            
            scale_result = scale_workload(context, name, replicas, namespace, kind)
            res["data"] = scale_result
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"扩缩容失败: {str(e)}"
        return JsonResponse(res)
    


    #设置deployment的镜像版本
    @action(detail=False, methods=['get'])
    def set_deployment_image(self, request):
        """
        设置Deployment的镜像版本
        
        Args:
            request.query_params:
                context: 集群上下文
                deployment_name: Deployment名称
                container_name: 容器名称
                tag: 镜像标签
                namespace: 命名空间
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [设置结果],
                "message": "success to set deployment image"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to set deployment image"
        }
        try:
            context = request.query_params.get("context")
            deployment_name = request.query_params.get("deployment_name")
            container_name = request.query_params.get("container_name")
            tag = request.query_params.get("tag")
            namespace = request.query_params.get("namespace")
            
            # 验证必要参数
            if not all([context, deployment_name, container_name, tag, namespace]):
                raise ValueError("缺少必要的参数")
            
            set_deployment_image_result = set_deployment_image(context, deployment_name, container_name, tag, namespace)
            res["data"] = set_deployment_image_result
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"设置镜像版本失败: {str(e)}"
        return JsonResponse(res)


    #获取镜像仓库列表
    @action(detail=False, methods=['get'])
    def get_latest_image(self, request):
        """
        获取最新的镜像版本列表
        
        Args:
            request.query_params:
                image_path: 镜像路径
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [镜像版本列表],
                "message": "success to get image repo list"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to get image repo list"
        }
        try:
            image_path = request.query_params.get("image_path")
            # 对image_path进行URL解码
            decoded_image_path = unquote(image_path)
            print(decoded_image_path)
            image_repo_list = get_latest_image(decoded_image_path)
            res["data"] = image_repo_list
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取镜像仓库列表失败: {str(e)}"
        return JsonResponse(res)

    # @action(detail=False, methods=['get'])
    # def get_pod_terminal_info(self, request):
    #     """
    #     获取Pod终端连接所需的信息，返回带认证token的WebSocket URL
        
    #     参数:
    #         context: k8s集群上下文
    #         pod_name: Pod名称
    #         namespace: 命名空间
    #         container: 容器名称(可选)
    #     """
    #     res = {
    #         "code": 20000,
    #         "data": {},
    #         "message": "success to get pod terminal info"
    #     }
        
    #     try:
    #         # 获取请求参数
    #         context = request.query_params.get("context")
    #         pod_name = request.query_params.get("pod_name")
    #         namespace = request.query_params.get("namespace")
    #         container = request.query_params.get("container")
            
    #         # 获取当前请求的token
    #         auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    #         if auth_header.startswith('Bearer '):
    #             token = auth_header.split(' ')[1]
    #         else:
    #             raise ValueError("未找到有效的认证token")
            
    #         # 构建WebSocket URL
    #         base_url = "ws://localhost:8000"
    #         ws_path = f"/ws/k8s/terminal/{namespace}/{pod_name}/"
            
    #         # 构建查询参数，包含token
    #         query_params = [
    #             f"token={token}",
    #             f"context={context}"
    #         ]
    #         if container:
    #             query_params.append(f"container={container}")
            
    #         # 组合完整的WebSocket URL
    #         websocket_url = f"{base_url}{ws_path}?{'&'.join(query_params)}"
            
    #         # 获取Pod信息
    #         config.load_kube_config(context=context)
    #         v1 = client.CoreV1Api()
    #         pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
    #         # 构建返回数据
    #         pod_info = {
    #             "name": pod.metadata.name,
    #             "namespace": pod.metadata.namespace,
    #             "status": pod.status.phase,
    #             "containers": [
    #                 {
    #                     "name": container.name,
    #                     "ready": container.ready if hasattr(container, 'ready') else False
    #                 }
    #                 for container in pod.spec.containers
    #             ]
    #         }
            
    #         res["data"] = {
    #             "websocket_url": websocket_url,  # 带token的WebSocket URL
    #             "pod_info": pod_info
    #         }
            
    #     except ValueError as ve:
    #         res["code"] = 40000
    #         res["message"] = str(ve)
    #         return JsonResponse(res, status=400)
            
    #     except Exception as e:
    #         res["code"] = 50000
    #         res["message"] = f"获取Pod终端信息失败: {str(e)}"
    #         return JsonResponse(res, status=500)
            
    #     return JsonResponse(res)
        


    @action(detail=False, methods=['post'])
    def delete_pod(self, request):
        """
        删除指定的Pod
        
        Args:
            request.query_params:
                context: 集群上下文
                pod_name: Pod名称
                namespace: 命名空间
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [删除结果],
                "message": "success to delete pod"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "success to delete pod"
        }
        try:
            context = request.query_params.get("context")
            pod_name = request.query_params.get("pod_name")
            namespace = request.query_params.get("namespace")
            delete_result = delete_pod(context, pod_name, namespace)
            
            # 根据delete_pod函数的返回结果设置响应代码
            if delete_result["success"]:
                res["data"] = delete_result
                res["message"] = delete_result["message"]
            else:
                res["code"] = 50000
                res["message"] = delete_result["message"]
                res["data"] = delete_result
                
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"删除Pod失败: {str(e)}"
        return JsonResponse(res)
    



    #获取configmap或secret的data
    @action(detail=False, methods=['get'])
    def get_configmap_secret_data(self, request):
        """
        获取ConfigMap或Secret的数据
        
        Args:
            request.query_params:
                context: 集群上下文
                resource_name: 资源名称
                namespace: 命名空间
                resource_type: 资源类型(ConfigMap或Secret)
                
        Returns:
            JsonResponse: {
                "code": 20000,
                "data": [资源数据],
                "message": "成功获取configmap或secret数据"
            }
        """
        res = {
            "code": 20000,
            "data": "",
            "message": "成功获取configmap或secret数据"
        }
        try:
            context = request.query_params.get("context")
            resource_name = request.query_params.get("resource_name")
            namespace = request.query_params.get("namespace")
            resource_type = request.query_params.get("resource_type")
            
            data = get_configmap_secret_data(context, resource_name, namespace, resource_type)
            res["data"] = data
            res["message"] = f"成功获取{resource_type}数据，资源名称为{resource_name}"
            
        except Exception as e:
            res["code"] = 50000
            res["message"] = f"获取ConfigMap或Secret数据失败: {str(e)}"
        return JsonResponse(res, json_dumps_params={'ensure_ascii': False})