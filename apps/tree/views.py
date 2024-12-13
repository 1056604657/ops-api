from django.http import JsonResponse
from pkg.custom_model_view_set import CustomModelViewSet
from . import models, serializers
from pkg.recursion_service_tree import recursion_service_tree
from rest_framework.views import APIView
from apps.cmdb.models import Resource
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction


# 服务树结构
class ServiceTreeViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.ServiceTreeModel.objects.all()
    serializer_class = serializers.ServiceTreeSerializer

    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            top_tree_list = list(models.ServiceTreeModel.objects.filter(parent=0).values())
            for node in top_tree_list:
                node["children"] = list(models.ServiceTreeModel.objects.filter(parent=node["id"]).values())
                node["children"] = recursion_service_tree.set_childrens(node["id"], node["children"])
            res["data"] = top_tree_list
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"获取树结构失败，{e}"
        return JsonResponse(res)

    def destroy(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            delete_related = request.GET.get("delete_related", "0")
            instance = self.get_object()
            with transaction.atomic():
                if delete_related == "1":
                    models.TreeRelatedModel.objects.filter(tree_id=instance.id).delete()
                tree_related_count = models.TreeRelatedModel.objects.filter(tree_id=instance.id).count()
                node_children_count = models.ServiceTreeModel.objects.filter(parent=instance.id).count()
                if tree_related_count > 0:
                    res["code"] = 40000
                    res["message"] = f"删除树节点失败，当前节点存在资源关联情况，无法直接删除。"
                elif node_children_count > 0:
                    res["code"] = 40000
                    res["message"] = f"删除树节点失败，当前节点存在子节点，无法直接删除。"
                else:
                    self.perform_destroy(instance)
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"删除树节点失败，{e}"
        return JsonResponse(res)


# 服务器关联资源
class TreeRelatedViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.TreeRelatedModel.objects.all()
    serializer_class = serializers.TreeRelatedSerializer

    def create(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            c = models.TreeRelatedModel.objects.filter(tree_id=request.data.get("tree_id"),
                                                       target_id=request.data.get("target_id"),
                                                       type=request.data.get("type")).count()
            if c == 0:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                res["data"] = serializer.data
        except Exception as e:
            res["code"] = 40000
            res["message"] = "新建资源关联失败，{}".format(e)
        return JsonResponse(res)

    def destroy(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            models.TreeRelatedModel.objects.filter(tree_id=kwargs.get("pk"), target_id=request.GET.get("target_id"),
                                                   type=request.GET.get("type")).delete()
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"删除资源关联失败，{e}"
        return JsonResponse(res)


# 查询节点关联的数据
class GetNodeResourceAPIView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, *args, **kwargs):
        model_id = request.GET.get("model")
        data = request.GET.get("data")

        if model_id is None:
            return JsonResponse({"code": 40000, "message": "参数 model 没有传递"})
        resource_id_list = list(models.TreeRelatedModel.objects.filter(tree_id=pk, type=model_id).values_list("target_id", flat=True))
        if data is not None:
            contact_list = list(Resource.objects.filter(id__in=resource_id_list, model=model_id, data__icontains=data).values())
        else:
            contact_list = list(Resource.objects.filter(id__in=resource_id_list, model=model_id).values())
        paginator = Paginator(contact_list, 10)
        page = request.GET.get('page')

        try:
            contacts = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            contacts = paginator.page(1)
        response_data = {
            "total": paginator.count,
            "list": list(contacts.object_list),
        }
        return JsonResponse({"code": 20000, "data": response_data, "message": "success"})