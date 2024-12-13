import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import DatabaseError


logger = logging.getLogger("django")

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        view = context["view"]
        if isinstance(exc, DatabaseError):
            logger.error('[%s] %s' % (view, exc))
            response = Response({"errmsg": "请检查服务器和数据库链接或表是否存在！"}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    return response