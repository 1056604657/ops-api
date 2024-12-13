from kubernetes import client, config
from kubernetes.stream import stream
from channels.generic.websocket import WebsocketConsumer
from channels.auth import AuthMiddlewareStack
import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs, unquote
import threading
import json
import logging

logger = logging.getLogger(__name__)

class PodTerminalConsumer(WebsocketConsumer):
    """
    Kubernetes Pod终端WebSocket消费者类
    用于建立与K8s Pod的终端交互连接
    """
    
    def connect(self):
        """
        建立websocket连接时的处理函数
        在前端调用new WebSocket()时会触发此函数
        """
        try:
            # 获取并解析查询参数
            query_string = self.scope.get('query_string', b'').decode()
            logger.debug(f"Query string: {query_string}")
            
            params = dict(param.split('=') for param in query_string.split('&') if param)
            logger.debug(f"Parsed params: {params}")
            
            # 从查询参数中获取token并解码URL编码
            token = unquote(params.get('token', ''))
            if not token:
                logger.error("Token not found in params")
                raise ValueError("未提供认证token")
            
            # token验证成功，接受连接
            self.accept()
            
            # 获取连接参数
            self.namespace = self.scope['url_route']['kwargs'].get('namespace')
            self.pod_name = self.scope['url_route']['kwargs'].get('pod_name')
            self.container = params.get('container')
            self.context = params.get('context')

            # 初始化k8s客户端
            config.load_kube_config(context=self.context)
            self.api = client.CoreV1Api()

            # 构建终端执行命令
            # 这个命令会：
            # 1. 设置终端环境变量TERM
            # 2. 优先尝试使用bash
            # 3. 如果没有bash则使用sh
            exec_command = [
                '/bin/sh', 
                '-c', 
                'TERM=xterm-256color; export TERM; ' +  # 设置终端类型
                '[ -x /bin/bash ] && ' +               # 检查是否有bash
                '([ -x /usr/bin/script ] && /usr/bin/script -q -c "/bin/bash" /dev/null || exec /bin/bash) || ' +  # 尝试使用bash
                'exec /bin/sh'                         # 如果没有bash则使用sh
            ]
            
            # 创建到Pod的流式连接
            self.resp = stream(
                self.api.connect_get_namespaced_pod_exec,  # K8s API方法
                self.pod_name,        # Pod名称
                self.namespace,       # 命名空间
                command=exec_command, # 要执行的命令
                container=self.container,  # 容器名称
                stderr=True,     # 捕获错误输出
                stdin=True,      # 开启标准输入
                stdout=True,     # 捕获标准输出
                tty=True,        # 分配伪终端
                _preload_content=False,  # 使用流式传输而不是一次性加载
            )

            # 连接建立后设置终端大小
            # 4 是控制通道，用于发送终端大小等控制信息
            self.resp.write_channel(4,json.dumps({
                "Height": 40,     # 设置更大的高度
                "Width": 260      # 设置更宽的宽度
            }))

            # 启动后台线程监听Pod的输出
            self.running = True  # 控制线程运行的标志
            threading.Thread(target=self._watch_response).start()  # 启动监听线程
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            self.close(code=4003)
            return

    def disconnect(self, close_code):
        """
        处理websocket连接断开
        在连接关闭时清理资源
        """
        self.running = False  # 停止监听线程
        if hasattr(self, 'resp'):
            self.resp.close()  # 关闭与Pod的连接

    def receive(self, text_data=None, bytes_data=None):
        """
        处理从前端接收到的消息
        当用户在终端输入内容时会触发此函数
        """
        try:
            # 解析前端发送的JSON数据
            data = json.loads(text_data)
            
            # 处理终端大小调整
            if 'resize' in data:
                rows = data['resize'].get('rows', 40)
                cols = data['resize'].get('cols', 660)
                self.resp.write_channel(4, json.dumps({
                    "Height": rows,
                    "Width": cols
                }))
                return
                
            # 处理输入内容
            input_data = data.get('input', '')
            self.resp.write_stdin(input_data)
            
        except Exception as e:
            # 如果发生错误，发送错误信息给前端
            self.send(text_data=json.dumps({
                'error': str(e)
            }))

    def _watch_response(self):
        """
        监听Pod输出的后台线程函数
        持续读取Pod的输出并发送给前端
        """
        while self.running:  # 当连接保持时持续运行
            try:
                # 读取标准输出并发送给前端
                stdout = self.resp.read_stdout()
                if stdout:  # 如果有输出
                    self.send(text_data=json.dumps({
                        'output': stdout  # 发送标准输出
                    }))
                
                # 读取标准错误并发送给前端
                stderr = self.resp.read_stderr()
                if stderr:  # 如果有错误输出
                    self.send(text_data=json.dumps({
                        'error': stderr  # 发送错误输出
                    }))
                    
            except Exception as e:
                # 发生错误时，发送错误信息给前端并退出循环
                self.send(text_data=json.dumps({
                    'error': str(e)
                }))
                break