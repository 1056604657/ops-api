from kubernetes import client, config, dynamic
from kubernetes.client import api_client
import datetime
import pytz
from typing import Dict, Any

def restart_workload(context: str, name: str, namespace: str = "default", kind: str = "Deployment") -> Dict[str, Any]:
    """
    重启指定的工作负载（Deployment/StatefulSet/DaemonSet）
    
    Args:
        context: k8s集群上下文
        name: 资源名称
        namespace: 命名空间，默认为default
        kind: 资源类型，支持 Deployment、StatefulSet、DaemonSet
        
    Returns:
        Dict: 包含操作结果的字典
    """
    try:
        # 加载k8s配置
        config.load_kube_config(context=context)
            
        # 创建动态客户端
        dynamic_client = dynamic.DynamicClient(api_client.ApiClient())
        
        # 验证资源类型
        supported_kinds = ["Deployment", "StatefulSet", "DaemonSet"]
        if kind not in supported_kinds:
            return {
                "success": False,
                "message": f"不支持的资源类型: {kind}，仅支持 {', '.join(supported_kinds)}"
            }
        
        # 获取API资源
        api = dynamic_client.resources.get(api_version="apps/v1", kind=kind)
        
        # 获取当前资源
        resource = api.get(name=name, namespace=namespace)
        
        if not resource:
            return {
                "success": False,
                "message": f"未找到 {kind}: {name} 在命名空间 {namespace}"
            }
            
        # 准备patch数据
        patch_data = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.datetime.now(tz=pytz.UTC).isoformat()
                        }
                    }
                }
            }
        }
        
        # 执行patch操作
        patched_resource = api.patch(
            body=patch_data,
            name=name,
            namespace=namespace,
            content_type="application/strategic-merge-patch+json",
            force=True  
        )
        
        return {
            "success": True,
            "message": f"已重启 {kind}: {name}",
            "data": {
                "namespace": namespace,
                "name": name,
                "kind": kind,
                "restarted_at": datetime.datetime.now(tz=pytz.UTC).isoformat(),
                "resource": patched_resource.to_dict()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"重启 {kind} 失败: {str(e)}",
            "error": str(e)
        }


def delete_workload(context: str, name: str, namespace: str = "default", kind: str = "Deployment") -> Dict[str, Any]:
    """
    删除指定的工作负载（Deployment/StatefulSet/DaemonSet/ConfigMap等）
    
    Args:
        context: k8s集群上下文
        name: 资源名称
        namespace: 命名空间，默认为default
        kind: 资源类型，如Deployment、StatefulSet、DaemonSet、ConfigMap等
        
    Returns:
        Dict: 包含操作结果的字典
    """
    try:
        # 加载k8s配置
        config.load_kube_config(context=context)
            
        # 创建动态客户端
        dynamic_client = dynamic.DynamicClient(api_client.ApiClient())
        
        # 根据资源类型确定API版本
        api_version = "apps/v1" if kind in ["Deployment", "StatefulSet", "DaemonSet"] else "v1"
        
        # 获取API资源
        api = dynamic_client.resources.get(api_version=api_version, kind=kind)
        
        try:
            # 直接尝试删除，不管资源是否存在
            api.delete(name=name, namespace=namespace)
            message = f"已删除 {kind}: {name}"
        except Exception as e:
            # 如果是404错误，说明资源本来就不存在，也算成功
            if "404" in str(e):
                message = f"{kind}: {name} 不存在或已被删除"
            else:
                # 其他错误则抛出异常
                raise e
        
        result = {
            "success": True,
            "message": message,
            "data": {
                "namespace": namespace,
                "name": name,
                "kind": kind,
                "deleted_at": datetime.datetime.now(tz=pytz.UTC).isoformat()
            }
        }
        
    except Exception as e:
        result = {
            "success": False,
            "message": f"删除 {kind} 失败: {str(e)}",
            "error": str(e)
        }
    
    return result


def scale_workload(context: str, name: str, replicas: int, namespace: str = "default", kind: str = "Deployment") -> Dict[str, Any]:
    """
    扩缩容工作负载（支持 Deployment 和 StatefulSet）
    
    Args:
        context: k8s集群上下文
        name: 资源名称
        replicas: 期望的副本数
        namespace: 命名空间，默认为default
        kind: 资源类型，支持 Deployment 和 StatefulSet
        
    Returns:
        Dict: 包含操作结果的字典
    """
    try:
        # 验证资源类型
        supported_kinds = ["Deployment", "StatefulSet"]
        if kind not in supported_kinds:
            return {
                "success": False,
                "message": f"不支持的资源类型: {kind}，仅支持 {', '.join(supported_kinds)}"
            }
            
        # 加载k8s配置
        config.load_kube_config(context=context)
            
        # 创建动态客户端
        dynamic_client = dynamic.DynamicClient(api_client.ApiClient())
        
        # 获取API资源
        api = dynamic_client.resources.get(api_version="apps/v1", kind=kind)
        
        try:
            # 获取当前资源
            resource = api.get(name=name, namespace=namespace)
            current_replicas = resource.spec.replicas
            
            # 准备patch数据
            patch_data = {
                "spec": {
                    "replicas": replicas
                }
            }
            
            # 执行patch操作
            patched_resource = api.patch(
                body=patch_data,
                name=name,
                namespace=namespace,
                content_type="application/strategic-merge-patch+json"
            )
            result = {
                "success": True,
                "message": f"已将 {kind}: {name} 的副本数从 {current_replicas} 调整为 {replicas}",
                "data": {
                    "namespace": namespace,
                    "name": name,
                    "kind": kind,
                    "updated_at": datetime.datetime.now(tz=pytz.UTC).isoformat()
                }
            }
            
        except Exception as e:
            if "404" in str(e):
                result = {
                    "success": False,
                    "message": f"{kind}: {name} 不存在",
                    "error": str(e)
                }
            else:
                raise e
                
    except Exception as e:
        result = {
            "success": False,
            "message": f"扩缩容 {kind} 失败: {str(e)}",
            "error": str(e)
        }
    
    return result


def set_deployment_image(context: str, deployment_name: str, container_name: str, tag: str, namespace: str = "default") -> Dict[str, Any]:
    # 加载kubeconfig配置，这里指定了context
    config.load_kube_config(context=context)

    # 创建API实例
    apps_v1 = client.AppsV1Api()

    # 获取现有的Deployment对象
    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

    # 检查是否找到了指定的容器
    container_found = False
    for container in deployment.spec.template.spec.containers:
        if container.name == container_name:
            # 分离出原始镜像名（不包含标签）
            original_image_name = container.image.split(':')[0]
            # 构建新的镜像名
            new_image = f"{original_image_name}:{tag}"
            container.image = new_image
            container_found = True
            break

    if not container_found:
        return {
            "success": False,
            "message": f"未找到名为 {container_name} 的容器",
            "data": None
        }

    # 应用更改
    api_response = apps_v1.patch_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=deployment
    )

    result = {
        "success": True,
        "message": f"已将 {deployment_name} 中的 {container_name} 容器的镜像版本设置为 {tag}",
        "data": api_response.to_dict()
    }
    return result


def delete_pod(context: str, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
    config.load_kube_config(context=context)
    core_v1 = client.CoreV1Api()
    try:
        core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {
            "success": True,
            "message": f"已删除Pod: {pod_name}",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"删除Pod失败: {str(e)}",
            "error": str(e)
        }








# if __name__ == "__main__":
    # 测试扩缩容
    #测试 Deployment
    # result1 = scale_workload(
    #     context="dev",
    #     name="httpbin",
    #     replicas=1,
    #     namespace="default",
    #     kind="Deployment"
    # )
    # print("Deployment 扩缩容结果:", result1)
    #测试删除pod
    # result2 = delete_pod(
    #     context="dev",
    #     pod_name="nfs-client-provisioner-565878766-c24bxk",
    #     namespace="default"
    # )
    # print("删除pod结果:", result2)
    # 测试 StatefulSet
    # result2 = scale_workload(
    #     context="dev",
    #     name="order-statefulset",
    #     replicas=1,
    #     namespace="jdocloud",
    #     kind="StatefulSet"
    # )
    # print("StatefulSet 扩缩容结果:", result2)

    # 测试设置deployment的镜像版本
    # result3 = set_deployment_image(
    #     context="dev",
    #     deployment_name="httpbin",
    #     tag="v1.0.13412412343242",
    #     namespace="default",
    #     container_name="httpbin232423"
    # )
    # print("设置deployment镜像版本结果:", result3)