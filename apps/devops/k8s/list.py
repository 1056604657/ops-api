import time
from kubernetes import client, dynamic, config
from kubernetes.client import api_client
from typing import Optional, List, Dict, Any
from kubernetes.dynamic.exceptions import ResourceNotFoundError
import yaml
from datetime import datetime, timezone
from kubernetes.client.rest import ApiException
import socket
import base64

#列出config文件中的所有context name
def list_cluster():
    config.load_kube_config()
    contexts, _ = config.list_kube_config_contexts()
    context_names = [context['name'] for context in contexts]
    return context_names

#根据集群列出当前集群下所有的命名空间
def list_namespaces(context: str):
    try:
        # 设置socket超时
        socket.setdefaulttimeout(1)
        
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        return [ns.metadata.name for ns in namespaces.items]
    except ApiException as e:
        raise Exception(f"Kubernetes API错误: {e}")
    except socket.timeout:
        raise Exception("连接集群超时")
    except Exception as e:
        raise Exception(f"获取命名空间失败: {e}")
    finally:
        # 恢复默认socket超时
        socket.setdefaulttimeout(None)

def get_container_images(spec):
    """只获取主容器的镜像列表"""
    if hasattr(spec, 'containers'):
        return [container.image for container in spec.containers]
    return []
def calculate_age(creation_timestamp: str) -> str:
    """计算资源的存在时间，并格式化为合适的字符串"""
    creation_time = datetime.fromisoformat(creation_timestamp.replace("Z", "+00:00"))  # 转换为datetime对象
    current_time = datetime.now(timezone.utc)  # 获取当前时间
    age = current_time - creation_time  # 计算时间差

    # 获取天、小时、分钟和秒
    days = age.days
    hours, remainder = divmod(age.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # 根据时间差的大小返回不同的格式
    if days > 0:
        return f"{days}d"  # 以天为单位
    elif hours > 0:
        return f"{hours}h{minutes}m"  # 以小时和分钟为单位
    elif minutes > 0:
        return f"{minutes}m{seconds}s"  # 以分钟和秒为单位
    else:
        return f"{seconds}s"  # 以秒为单位

def get_pod_status_and_time(pod_status) -> tuple:
    """
    获取Pod的状态和结束时间
    返回: (状态, 错误信息, 结束时间)
    """
    # 初始化返回值
    overall_state = "Running"  # 默认状态
    error_msg = None
    finished_at = None
    
    # 1. 首先检查pod的phase
    if hasattr(pod_status, 'phase'):
        # 处理Failed状态
        if pod_status.phase == 'Failed':
            if hasattr(pod_status, 'reason') and pod_status.reason == 'Evicted':
                overall_state = 'Evicted'
                error_msg = pod_status.message if hasattr(pod_status, 'message') else 'Pod被逐'
                finished_at = pod_status.startTime if hasattr(pod_status, 'startTime') else None
                return overall_state, error_msg, finished_at
    
    # 2. 优先检查初始化容器状态
    if hasattr(pod_status, 'initContainerStatuses') and pod_status.initContainerStatuses:
        for init_container in pod_status.initContainerStatuses:
            if hasattr(init_container, 'state'):
                state = init_container.state
                
                # 检查等待状态
                if hasattr(state, 'waiting') and state.waiting:
                    waiting = state.waiting
                    reason = waiting.reason if hasattr(waiting, 'reason') else ''
                    
                    # 处理特定的等待状态
                    if reason in ['ImagePullBackOff', 'ErrImagePull']:
                        overall_state = f'Init:{reason}'
                        error_msg = waiting.message if hasattr(waiting, 'message') else f'初始化容器镜像拉取失败: {init_container.image}'
                        return overall_state, error_msg, finished_at
                    elif reason == 'CrashLoopBackOff':
                        overall_state = f'Init:CrashLoopBackOff'
                        error_msg = waiting.message if hasattr(waiting, 'message') else '初始化容器反复崩'
                        if hasattr(init_container, 'lastState') and init_container.lastState:
                            last_state = init_container.lastState
                            if hasattr(last_state, 'terminated') and last_state.terminated:
                                finished_at = last_state.terminated.finishedAt
                        return overall_state, error_msg, finished_at
    
    # 3. 检查主容器状态
    if not pod_status.containerStatuses:
        return "Pending", "No containers", None
        
    for container_status in pod_status.containerStatuses:
        # 检查容器当前状态
        if hasattr(container_status, 'state'):
            state = container_status.state
            
            # 优先处理等待状态
            if hasattr(state, 'waiting') and state.waiting:
                waiting = state.waiting
                reason = waiting.reason if hasattr(waiting, 'reason') else ''
                
                # 处理特定的等待状态
                if reason == 'CrashLoopBackOff':
                    overall_state = 'CrashLoopBackOff'
                    error_msg = waiting.message if hasattr(waiting, 'message') else '容器反复崩溃'
                    # 获取上一次的终止时间
                    if hasattr(container_status, 'lastState') and container_status.lastState:
                        last_state = container_status.lastState
                        if hasattr(last_state, 'terminated') and last_state.terminated:
                            finished_at = last_state.terminated.finishedAt
                    return overall_state, error_msg, finished_at
                elif reason in ['ImagePullBackOff', 'ErrImagePull']:
                    overall_state = reason
                    error_msg = waiting.message if hasattr(waiting, 'message') else f'镜像拉取失败: {container_status.image}'
                    return overall_state, error_msg, finished_at
                else:
                    overall_state = reason
                    error_msg = waiting.message if hasattr(waiting, 'message') else '容器等待中'
                    return overall_state, error_msg, finished_at
                    
            # 处理运行状态
            elif hasattr(state, 'running') and state.running:
                if not container_status.ready:
                    overall_state = 'NotReady'
                    error_msg = '容器运行但未就绪'
                    
            # 处理终止状态
            elif hasattr(state, 'terminated') and state.terminated:
                terminated = state.terminated
                overall_state = terminated.reason if hasattr(terminated, 'reason') else 'Terminated'
                error_msg = f'容器终止，退出码: {terminated.exitCode}'
                finished_at = terminated.finishedAt if hasattr(terminated, 'finishedAt') else None
        
        # 检查上次状态，获取结束时间（如果还没有设置）
        if not finished_at and hasattr(container_status, 'lastState') and container_status.lastState:
            last_state = container_status.lastState
            if hasattr(last_state, 'terminated') and last_state.terminated:
                terminated = last_state.terminated
                # 只有在异常退出时才记录结束时间
                if terminated.exitCode != 0:
                    finished_at = terminated.finishedAt
    
    return overall_state, error_msg, finished_at

def list_cluster_resources(context: str, resource_kind: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    动态获取指定群中的资源列表，并去除重复的资源
    """

    # 加载配置
    config.load_kube_config(context=context)

    # 创建动态客户端
    dyn_client = dynamic.DynamicClient(api_client.ApiClient())

    # 搜索资源
    api_resources = dyn_client.resources.search(kind=resource_kind)
    
    # 安全地打印API资源信息
    api_versions = []
    for r in api_resources:
        try:
            api_version = f"{r.group_version if hasattr(r, 'group_version') else 'v1'}"
            api_versions.append(api_version)
        except Exception as e:
            print(f"获取API版本信息时出错: {e}")
            continue
    
    print(f"找到的API资源版本: {api_versions}")

    # 如果没有找到任何API版本，直接返回空列表
    if not api_resources:
        print(f"未找到资源类型 {resource_kind} 的任何API版本")
        return []

    # 获取资源
    resources = []
    
    for resource in api_resources:
        try:
            api_version = f"{resource.group_version if hasattr(resource, 'group_version') else 'v1'}"
            print(f"尝试从 API {api_version} 获取 {resource_kind}")
            
            if namespace:
                response = resource.get(namespace=namespace)
            else:
                response = resource.get()
            
            # 如果成功获取到资源，添加到列表中
            resources.extend(response.items)
            print(f"成功从 API {api_version} 获取到 {len(response.items)} 个资源")
            
        except Exception as e:
            # 简化错误信息
            print(f"跳过 API {api_version} (不支持此版本)")
            continue

    # 如果有API版本都失败，返回空列表
    if not resources:
        print(f"所有API版本都无法获取到 {resource_kind} 资源")
        return []

    # 修改去重和返回逻辑
    filtered_resources = []
    for resource in resources:
        if resource_kind == 'Pod':
            # Pod 资源的特殊处理
            containers = resource.status.containerStatuses if resource.status.containerStatuses else []
            
            # 获取容器列表信息
            container_list = []
            if resource.spec.containers:
                for container in resource.spec.containers:
                    container_info = {
                        'name': container.name,
                        'image': container.image,
                        'ports': [{'containerPort': port.containerPort, 'protocol': port.protocol} 
                                 for port in container.ports] if container.ports else [],
                        'resources': container.resources.to_dict() if container.resources else {}
                    }
                    container_list.append(container_info)
            
            # 获取Pod状态信息
            overall_state, error_msg, finished_at = get_pod_status_and_time(resource.status)
            
            # 如果有结束时间，转换为年龄格式
            if finished_at:
                finished_at = calculate_age(finished_at)
            
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'node': resource.spec.nodeName,
                'age': calculate_age(resource.metadata.creationTimestamp),
                'hostIp': resource.status.hostIP,
                'podIp': resource.status.podIP,
                'creationTimestamp': resource.metadata.creationTimestamp,
                'state': overall_state,
                'error_msg': error_msg,
                'restart_count': sum(container.restartCount for container in containers) if containers else 0,
                'image': containers[0].image if containers else '',
                'ready': all(container.ready for container in containers) if containers else False,
                'finishedAt': finished_at,
                'containers': container_list
            }
        elif resource_kind == 'Deployment':
            # 获取容器信息
            containers = []
            if resource.spec.template.spec.containers:
                for container in resource.spec.template.spec.containers:
                    container_info = {
                        'name': container.name,
                        'image': container.image,
                        'ports': [{'containerPort': port.containerPort, 'protocol': port.protocol} 
                                 for port in container.ports] if container.ports else []
                    }
                    containers.append(container_info)
            
            # Deployment 资源的处理
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'creationTimestamp': resource.metadata.creationTimestamp,
                'images': get_container_images(resource.spec.template.spec),  # 只返回主容器镜像列表
                'selector': resource.spec.selector.matchLabels if resource.spec.selector and resource.spec.selector.matchLabels else {},
                'replicas': resource.spec.replicas if resource.spec.replicas else 0,
                'available_replicas': resource.status.availableReplicas if resource.status.availableReplicas else 0,
                'strategy': resource.spec.strategy.type if resource.spec.strategy and resource.spec.strategy.type else '',
                'restartPolicy': resource.spec.template.spec.restartPolicy if resource.spec.template.spec.restartPolicy else '',
                'containers': containers  # 添加容器列表
            }
        elif resource_kind == 'StatefulSet':
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'creationTimestamp': resource.metadata.creationTimestamp,
                'image': get_container_images(resource.spec.template.spec),
                'replicas': resource.spec.replicas if resource.spec.replicas else 0,
                'ready_replicas': resource.status.readyReplicas if resource.status.readyReplicas else 0,
                'current_replicas': resource.status.currentReplicas if resource.status.currentReplicas else 0,
                'updated_replicas': resource.status.updatedReplicas if resource.status.updatedReplicas else 0,
            }
        elif resource_kind == 'DaemonSet':
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'creationTimestamp': resource.metadata.creationTimestamp,
                'images': get_container_images(resource.spec.template.spec),
                'desired_number_scheduled': resource.status.desiredNumberScheduled if resource.status.desiredNumberScheduled else 0,
                'current_number_scheduled': resource.status.currentNumberScheduled if resource.status.currentNumberScheduled else 0,
                'number_available': resource.status.numberAvailable if resource.status.numberAvailable else 0,
            }
        elif resource_kind == 'Service':
            # Service 资源的处理
            ports_info = []
            if hasattr(resource.spec, 'ports') and resource.spec.ports:
                for port in resource.spec.ports:
                    if resource.spec.type == 'NodePort':
                        ports_info.append({
                            'port': port.port,
                            'target_port': str(port.targetPort) if port.targetPort else '',
                            'protocol': port.protocol if port.protocol else '',
                            'nodePort': port.nodePort if port.nodePort else ''
                        })
                    else:
                        ports_info.append({
                            'port': port.port,
                            'target_port': str(port.targetPort) if port.targetPort else '',
                            'protocol': port.protocol if port.protocol else ''
                        })
                
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'creationTimestamp': resource.metadata.creationTimestamp,
                'type': resource.spec.type if resource.spec.type else '',
                'cluster_ip': resource.spec.clusterIP if resource.spec.clusterIP else '',
                'ports': ports_info,
                'selector': dict(resource.spec.selector) if resource.spec.selector else {}
            }
        elif resource_kind == 'ConfigMap':
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'creationTimestamp': resource.metadata.creationTimestamp,
                'data': resource.data if resource.data else ''
            }
        else:
            # 默认处理方式，只返回本信息
            filtered_data = {
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'creationTimestamp': resource.metadata.creationTimestamp
            }
        
        # 使用元组作为键来去重
        key = (resource.metadata.namespace, resource.metadata.name)
        if key not in {(item['namespace'], item['name']) for item in filtered_resources}:
            filtered_resources.append(filtered_data)
            
    return filtered_resources

# namespaces = list_namespaces('test')
# print(namespaces)

#根据deployment和namespace获取deployment的pod列表
def list_deployment_pods(context: str, deployment: str, namespace: str):
    """获取指定deployment下的所有pod"""
    config.load_kube_config(context=context)
    v1 = client.CoreV1Api()
    
    # 获取所有pod
    pods = v1.list_namespaced_pod(namespace)
    deployment_pods = []
    
    # 筛选属于指定deployment的pod
    for pod in pods.items:
        if pod.metadata.owner_references:
            for owner in pod.metadata.owner_references:
                if owner.kind == 'ReplicaSet' and deployment in pod.metadata.name:
                    # 获取容器信息
                    containers = []
                    if pod.status.container_statuses:
                        for container in pod.status.container_statuses:
                            container_info = {
                                'name': container.name,
                                'image': container.image,
                                'ready': container.ready,
                                'restart_count': container.restart_count,
                                'state': next(iter(container.state.to_dict().keys())),  # 获取容器状态
                            }
                            containers.append(container_info)
                    
                    pod_info = {
                        'name': pod.metadata.name,
                        'status': pod.status.phase,
                        'ready': all(container.ready for container in pod.status.container_statuses) if pod.status.container_statuses else False,
                        'ip': pod.status.pod_ip,
                        'node': pod.spec.node_name,
                        'create_time': pod.metadata.creation_timestamp,
                        'containers': containers  # 添加容器列表
                    }
                    deployment_pods.append(pod_info)
    
    return deployment_pods

#根据statefulset和namespace获取statefulset的pod和相应的container列表
def list_statefulset_pods(context: str, statefulset: str, namespace: str):
    """
    获取指定statefulset下的所有pod和容器信息
    
    Args:
        context: k8s集群上下文
        statefulset: StatefulSet名称
        namespace: 命名空间
    
    Returns:
        list: pod信息列表，包含容器详情
    """
    config.load_kube_config(context=context)
    v1 = client.CoreV1Api()
    
    # 获取所有pod
    pods = v1.list_namespaced_pod(namespace)
    statefulset_pods = []
    
    # 筛选属于指定statefulset的pod
    for pod in pods.items:
        if pod.metadata.owner_references:
            for owner in pod.metadata.owner_references:
                if owner.kind == 'StatefulSet' and owner.name == statefulset:
                    # 获取容器信息
                    containers = []
                    if pod.status.container_statuses:
                        for container in pod.status.container_statuses:
                            container_info = {
                                'name': container.name,
                                'image': container.image,
                                'ready': container.ready,
                                'restart_count': container.restart_count,
                                'state': next(iter(container.state.to_dict().keys())),  # 获取容器状态
                                'started': container.started if hasattr(container, 'started') else None,
                                'last_state': container.last_state.to_dict() if container.last_state else None
                            }
                            containers.append(container_info)
                    
                    # 构建pod信息
                    pod_info = {
                        'name': pod.metadata.name,
                        'status': pod.status.phase,
                        'ready': all(container.ready for container in pod.status.container_statuses) if pod.status.container_statuses else False,
                        'ip': pod.status.pod_ip,
                        'node': pod.spec.node_name,
                        'create_time': pod.metadata.creation_timestamp,
                        'containers': containers,
                        'ordinal_index': int(pod.metadata.name.split('-')[-1])  # StatefulSet特有的序号
                    }
                    statefulset_pods.append(pod_info)
    
    # 按照序号排序
    statefulset_pods.sort(key=lambda x: x['ordinal_index'])
    return statefulset_pods
    

def get_resource_yaml(context: str, resource_kind: str, resource_name: str, namespace: Optional[str] = None) -> str:
    """
    获取指定k8s资源的yaml格式配置
    
    Args:
        context: k8s集群上下文
        resource_kind: 资源类型(如Pod, Deployment等)
        resource_name: 资源名称
        namespace: 命名空间(可选)
    
    Returns:
        str: 资源的yaml格式字符串
    """
    try:
        # 加载配置
        config.load_kube_config(context=context)
        
        # 创建动态客户端
        dyn_client = dynamic.DynamicClient(api_client.ApiClient())
        
        # 搜索资源API
        api_resources = dyn_client.resources.search(kind=resource_kind)
        if not api_resources:
            raise ValueError(f"未找到资源类型 {resource_kind}")
            
        # 获取资源对象
        resource = api_resources[0]
        try:
            if namespace:
                response = resource.get(name=resource_name, namespace=namespace)
            else:
                response = resource.get(name=resource_name)
                
            # 取资源对象后，过滤不需要的字段
            resource_dict = response.to_dict()
            
            # 删除不需要展示的元数据字段
            if 'metadata' in resource_dict:
                metadata = resource_dict['metadata']
                fields_to_remove = [
                    'uid',
                    'resourceVersion',
                    'selfLink',
                    'generation',
                    'managedFields',
                    'ownerReferences',
                    'creationTimestamp'
                ]
                for field in fields_to_remove:
                    metadata.pop(field, None)
            
            # 删除状态信息
            if 'status' in resource_dict:
                del resource_dict['status']
            #print(resource_dict)

            # 处理字符串中的 \n
            def process_newlines(data):
                if isinstance(data, dict):
                    return {k: process_newlines(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [process_newlines(i) for i in data]
                elif isinstance(data, str):
                    if '\n' in data:  # 只对包含换行符的字符串使用特殊处理
                        decoded = data.encode().decode('unicode-escape')
                        return decoded
                    return data  # 普通字符串直接返回
                return data

            # 处理数据中的换行符
            resource_dict = process_newlines(resource_dict)
            
            class MyDumper(yaml.Dumper):
                def represent_scalar(self, tag, value, style=None):
                    # 只对包含换行符的字符串使用 | 样式
                    if isinstance(value, str) and '\n' in value:
                        style = '|'
                    else:
                        style = None
                    return super().represent_scalar(tag, value, style)
            
            # 转换为yaml格式
            return yaml.dump(
                resource_dict,
                Dumper=MyDumper,
                default_flow_style=False,
                allow_unicode=True,
                indent=2
            )
            
        except ResourceNotFoundError:
            return f"未找到资源 {resource_kind}/{resource_name}"
        except Exception as e:
            return f"获取资源时发生错误: {str(e)}"
            
    except Exception as e:
        return f"操作失败: {str(e)}"



def get_pod_logs(context: str, pod_name: str, namespace: str, container_name: str = None, 
                 previous: bool = False, tail_lines: int = None) -> str:
    """
    获取指定pod的日志
    
    Args:
        context: k8s集群上下文
        pod_name: Pod名称
        namespace: 命名空间
        container_name: 容器名称（如果Pod中有多个容器）
        previous: 是否获取上一个容器实例的日志（当容器重启时有用）
        tail_lines: 回最后的日志行
    
    Returns:
        str: pod的日志内容
    """
    try:
        # 加载配置
        config.load_kube_config(context=context)
        
        # 创建API客户端
        v1 = client.CoreV1Api()
        
        # 获取日志
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            previous=previous,
            tail_lines=tail_lines,  # 修改回 tail_lines
            # timestamps=True
        )
        
        return logs
        
    except Exception as e:
        return f"获取日志失败: {str(e)}"



def get_configmap_secret_data(context: str, resource_name: str, namespace: str, resource_type: str = 'ConfigMap') -> dict:
    """
    获取指定 ConfigMap 或 Secret 的 data
    
    Args:
        context: k8s集群上下文
        resource_name: ConfigMap或Secret名称
        namespace: 命名空间
        resource_type: 资源类型,可选值为 'ConfigMap' 或 'Secret'
    
    Returns:
        dict: ConfigMap或Secret的data内容
    """
    try:
        # 加载配置
        config.load_kube_config(context=context)
        
        # 创建API客户端
        v1 = client.CoreV1Api()
        
        if resource_type == 'ConfigMap':
            # 获取ConfigMap
            resource = v1.read_namespaced_config_map(resource_name, namespace)
            return resource.data if resource.data else {}
        elif resource_type == 'Secret':
            # 获取Secret
            resource = v1.read_namespaced_secret(resource_name, namespace)
            # Secret的data是base64编码的,需要解码
            if resource.data:
                return {k: base64.b64decode(v).decode('utf-8') 
                       for k, v in resource.data.items()}
            return {}
        else:
            raise ValueError(f"不支持的资源类型: {resource_type}")
            
    except Exception as e:
        raise Exception(f"获取{resource_type}数据失败: {str(e)}")



# pods = list_deployment_pods('dev', 'httpbin', 'default')
# print(pods)


# pods = list_statefulset_pods('dev', 'prometheus-k8s', 'monitoring')
# print(pods)


# if __name__ == "__main__":
#     pods = list_cluster_resources('dev', 'Pod','jdocloud-private')
#     print(f"找到 {len(pods)} 个 Pod")
#     print(pods)

# # print(pods)
# end_test_time = time.time()
# print(f"测试代码执行总耗时: {end_test_time - start_test_time:.4f} 秒")

# deployments = list_cluster_resources('dev', 'Deployment','jdocloud')
# print(f"Found {len(deployments)} deployments")
# print(deployments)

# statefulsets = list_cluster_resources('dev', 'StatefulSet','monitoring')
# print(f"Found {len(statefulsets)} statefulsets")
# print(statefulsets)
# daemonsets = list_cluster_resources('dev', 'DaemonSet','monitoring')
# print(f"Found {len(daemonsets)} daemonsets")
# print(daemonsets)
# services = list_cluster_resources('dev', 'Service', 'default')
# print(f"Found {len(services)} services")
# print(services)

# ingress = list_cluster_resources('dev', 'Ingress')
# print(f"Found {len(ingress)} ingress")
# for ingress in ingress:
#     print(f"Ingress: {ingress.metadata.name}")


# configmaps = list_cluster_resources('dev', 'ConfigMap','default')
# print(f"Found {len(configmaps)} configmaps")
# print(configmaps)
# secret = list_cluster_resources('dev', 'Secret','default')
# print(f"Found {len(secret)} secrets")
# print(secret)
# config_data = get_configmap_secret_data('dev', 'aijidou-com-ssl', 'default', 'Secret')
# print(config_data)

# ns = list_namespaces('dev')
# print(ns)


# pod = list_cluster_resources('dev', 'Pod','default')
# print(f"Found {len(pod)} pods")
# print(pod)
# pod_yaml = get_resource_yaml('dev', 'Service','collect-service','bi-project')
# print(pod_yaml)
configmap_yaml = get_resource_yaml('dev', 'ConfigMap','istio-ca-root-cert','bi-project')
print(configmap_yaml)
# logs = get_pod_logs('dev', 'nfs-client-provisioner-565878766-qm2kd')
# print(logs)

