import json
import time
from django.utils.deprecation import MiddlewareMixin
from ..serializers import opLogsSerializer


class OpLogs(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        re_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        response = self.get_response(request)
        end_time = time.time()
        elapsed_time = round((end_time - start_time) * 1000)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            re_ip = x_forwarded_for.split(",")[0]
        else:
            re_ip = request.META.get('REMOTE_ADDR')
        if request.user.is_authenticated and not request.path.startswith('/api/v1/system/'):
            request_data = None
            response_data = None
            try:
                request_data = json.loads(request.body)
            except:
                pass
            try:
                response_data = json.loads(response.content)
            except:
                pass
            log_data = {
                're_time': re_time,
                're_user': request.user.username,
                're_method': request.method,
                're_url': request.path,
                're_ip': re_ip,
                're_content': json.dumps(request_data),
                'rp_content': json.dumps(response_data),
                'access_time': elapsed_time
            }
            op_log_serializer = opLogsSerializer(data=log_data)
            op_log_serializer.is_valid(raise_exception=True)
            op_log_serializer.save()
        return response