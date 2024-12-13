from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from apps.devops.k8s.terminal import PodTerminalConsumer

# WebSocket路由配置
websocket_urlpatterns = [
    re_path(
        r'ws/k8s/terminal/(?P<namespace>[^/]+)/(?P<pod_name>[^/]+)/$', 
        PodTerminalConsumer.as_asgi()
    ),
]

# 应用路由配置
application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})