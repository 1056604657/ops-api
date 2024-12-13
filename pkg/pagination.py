from django.http import JsonResponse
from rest_framework.pagination import PageNumberPagination
from rest_framework import status


class NewPageNumberPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 10000
    page_size_query_param = 'limit'
    page_query_param = 'page'

    def get_paginated_response(self, data):
        data = {
            "code": 20000,
            "data": {
                "total": self.page.paginator.count,
                "list": data
            },
            "message": "success"
        }
        return JsonResponse(data=data, status=status.HTTP_200_OK)
