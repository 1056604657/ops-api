import xlrd
from io import BytesIO
from django.db.models import Q
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from pkg.custom_model_view_set import CustomModelViewSet
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
import time
from cryptography.fernet import Fernet
import base64
from django.conf import settings





class GaodeViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # 增加账号类型
    def gaodekeylist(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info("Starting request to forward service")

        try:
            # 禁用代理
            response = requests.get(
                "http://127.0.0.1:7000/forward/",
                proxies={"http": None, "https": None}  # 禁用所有代理
            )
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content: {response.content}")

            if response.status_code != 200:
                return Response({
                    "code": response.status_code,
                    "message": "Failed to retrieve data"
                })

            original_data = response.json()
            if original_data.get("code") != 0:
                return Response({
                    "code": original_data.get("code"),
                    "message": original_data.get("message")
                })

            res = {
                "code": 0,
                "data": original_data.get("data", []),
                "message": "success to get gaode key list"
            }
            return Response(res)

        except Exception as e:
            logger.error(f"Error during request: {str(e)}")
            return Response({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            })
