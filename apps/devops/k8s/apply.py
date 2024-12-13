import time
from kubernetes import client, dynamic, config
from kubernetes.client import api_client
from typing import Optional, List, Dict, Any
from kubernetes.dynamic.exceptions import ResourceNotFoundError
import yaml
from kubernetes.client.rest import ApiException

def apply_resource_from_yaml(
    yaml_content: str, 
    context: str
) -> List[Dict[str, Any]]:
    """
    从yaml内容部署或更新k8s资源，支持多个资源
    
    Args:
        yaml_content: yaml格式的资源定义内容
        context: k8s集群上下文名称
        
    Returns:
        List[Dict]: 包含每个资源操作结果的列表
    """
    results = []
    try:
        config.load_kube_config(context=context)
        
        dynamic_client = dynamic.DynamicClient(api_client.ApiClient())
        
        for resource_dict in yaml.safe_load_all(yaml_content):
            try:
                api_version = resource_dict.get("apiVersion")
                kind = resource_dict.get("kind")
                metadata = resource_dict.get("metadata", {})
                resource_name = metadata.get("name")
                namespace = metadata.get("namespace", "default")
                
                if "metadata" in resource_dict:
                    clean_metadata = resource_dict["metadata"].copy()
                    fields_to_remove = [
                        "resourceVersion",
                        "uid",
                        "creationTimestamp",
                        "generation",
                        "managedFields",
                        "selfLink"
                    ]
                    for field in fields_to_remove:
                        clean_metadata.pop(field, None)
                    resource_dict["metadata"] = clean_metadata
                
                # 获取资源API
                api_resource = dynamic_client.resources.get(
                    api_version=api_version,
                    kind=kind
                )
                
                try:
                    # 尝试创建资源
                    api_resource.create(
                        body=resource_dict,
                        namespace=namespace
                    )
                    results.append({
                        "success": True,
                        "message": f"已创建{kind}资源: {resource_name}",
                        "operation": "create"
                    })
                except ApiException as e:
                    if e.status == 409:  # 资源已存在
                        # 更新资源
                        api_resource.patch(
                            body=resource_dict,
                            name=resource_name,
                            namespace=namespace,
                            content_type="application/merge-patch+json"
                        )
                        results.append({
                            "success": True,
                            "message": f"已更新{kind}资源: {resource_name}",
                            "operation": "update"
                        })
                    else:
                        results.append({
                            "success": False,
                            "message": f"API错误: {e.status}\nReason: {e.reason}\nBody: {e.body}",
                            "error": str(e)
                        })
                        
            except Exception as e:
                results.append({
                    "success": False,
                    "message": f"处理资源时出错: {str(e)}",
                    "error": str(e)
                })
                
    except Exception as e:
        results.append({
            "success": False,
            "message": f"未知错误: {str(e)}",
            "error": str(e)
        })
    
    return results

# 测试代码（在函数定义之外）
if __name__ == "__main__":
    yaml_content = """
apiVersion: v1
kind: Service
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: '{"apiVersion":"v1","kind":"Service","metadata":{"annotations":{},"name":"collect-service","namespace":"default"},"spec":{"ports":[{"name":"port8080","nodePort":31893,"port":8080,"protocol":"TCP","targetPort":8080},{"name":"port9999","nodePort":31154,"port":9999,"protocol":"TCP","targetPort":9999}],"selector":{"app":"collect-service"},"type":"NodePort"}}

      '
  name: collect-service
  namespace: default
spec:
  externalTrafficPolicy: Cluster
  ports:
  - name: port8080
    nodePort: 31843
    port: 8080
    protocol: TCP
    targetPort: 8080
  - name: port9999
    nodePort: 31144
    port: 9999
    protocol: TCP
    targetPort: 9999
  selector:
    app: collect-service
  sessionAffinity: None
  type: NodePort
"""

    result = apply_resource_from_yaml(
        yaml_content=yaml_content,
        context="dev"
    )
    print(result)