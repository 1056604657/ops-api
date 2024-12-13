from kubernetes import client, config
from datetime import datetime, timezone
import json
from prettytable import PrettyTable
from typing import List, Dict, Union

def format_timestamp(timestamp) -> str:
    """格式化时间戳"""
    if not timestamp:
        return "N/A"
    if isinstance(timestamp, str):
        return timestamp
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def print_events(events: List[Dict], limit: int = None, output_format: str = 'table') -> None:
    """
    输出事件信息

    Args:
        events: 事件列表
        limit: 显示最近的事件数量
        output_format: 输出格式 ('table' 或 'json')
    """
    if isinstance(events, str):  # 如果是错误信息
        print(f"\033[91m错误: {events}\033[0m")
        return

    # 限制事件数量
    if limit:
        events = events[:limit]

    if output_format.lower() == 'json':
        # JSON 输出
        print(json.dumps(events, indent=2, ensure_ascii=False))
        return

    # 表格输出
    table = PrettyTable()
    table.field_names = [
        "类型", "原因", "对象", "名称", "命名空间", 
        "消息", "组件", "次数", "最后发生时间"
    ]
    
    table.align = "l"
    table.max_width = 50
    
    for event in events:
        color = "\033[93m" if event['type'] == "Warning" else "\033[92m"
        
        message = event['message']
        if len(message) > 50:
            message = message[:47] + "..."
            
        row = [
            f"{color}{event['type']}\033[0m",
            event['reason'],
            event['object_kind'],
            event['object_name'],
            event['namespace'],
            message,
            event['component'] or "N/A",
            event['count'],
            format_timestamp(event['last_timestamp'])
        ]
        table.add_row(row)
    
    print(f"\n总共 {len(events)} 个事件:")
    print(f"Warning: {sum(1 for e in events if e['type'] == 'Warning')} 个")
    print(f"Normal: {sum(1 for e in events if e['type'] == 'Normal')} 个")
    print("\n事件详情:")
    print(table)

def list_cluster_events(
    context: str, 
    namespace: str = None, 
    limit: int = None, 
    output_format: str = 'table'
) -> Union[List[Dict], str]:
    """
    获取集群事件信息
    """
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()
        
        if namespace:
            events = v1.list_namespaced_event(namespace=namespace)
        else:
            events = v1.list_event_for_all_namespaces()
            
        event_list = []
        for event in events.items:
            last_timestamp = event.last_timestamp if event.last_timestamp else event.metadata.creation_timestamp
            first_timestamp = event.first_timestamp if event.first_timestamp else event.metadata.creation_timestamp
            
            # 将时间戳转换为字符串，以便 JSON 序列化
            event_info = {
                'name': event.metadata.name,
                'namespace': event.metadata.namespace,
                'type': event.type,
                'reason': event.reason,
                'message': event.message,
                'component': event.source.component if event.source else None,
                'host': event.source.host if event.source else None,
                'object_kind': event.involved_object.kind,
                'object_name': event.involved_object.name,
                'count': event.count,
                'first_timestamp': format_timestamp(first_timestamp),
                'last_timestamp': format_timestamp(last_timestamp),
            }
            event_list.append(event_info)
            
        event_list.sort(
            key=lambda x: x['last_timestamp'] or datetime.min.replace(tzinfo=timezone.utc), 
            reverse=True
        )

        # 限制事件数量
        if limit:
            event_list = event_list[:limit]

        return event_list
        
    except Exception as e:
        return f"获取事件失败: {str(e)}"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='获取 Kubernetes 集群事件')
    parser.add_argument('--context', type=str, default='dev', help='Kubernetes 集群上下文')
    parser.add_argument('--namespace', type=str, help='指定命名空间')
    parser.add_argument('--limit', type=int, help='显示最近的事件数量')
    parser.add_argument('--format', type=str, choices=['table', 'json'], default='table', 
                        help='输出格式 (table 或 json)')
    
    args = parser.parse_args()
    
    # 获取事件
    events = list_cluster_events(
        context=args.context,
        namespace=args.namespace,
        limit=args.limit,
        output_format=args.format
    )

    # 根据格式输出结果
    if args.format == 'json':
        print(json.dumps(events, indent=2, ensure_ascii=False))
    else:
        print_events(events)