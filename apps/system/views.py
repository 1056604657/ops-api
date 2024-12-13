from apps.system.models import Roles, Permissions, UserRoles, RolePermissions, OpLogs
from .serializers import RolesSerializer, PermissionsSerializer, UsersSerializer, opLogsSerializer
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from pkg.custom_model_view_set import CustomModelViewSet
from rest_framework_jwt import views as jwt_views
from .serializers import JSONWebTokenSerializer
from rest_framework.views import APIView
from django.http import JsonResponse
from apps.system.models import UserInfo
from django.db import transaction
from . import filter, models
from rest_framework import status
from django.db.models import Q
import logging


class ObtainJSONWebToken(jwt_views.ObtainJSONWebToken):
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info('开始处理JWT认证请求')
        try:
            response = super().post(request, *args, **kwargs)
            logger.info('JWT认证请求处理完成')
            return response
        except Exception as e:
            logger.error(f'JWT认证失败: {str(e)}')
            raise


## 获取用户信息
class GetInfoView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,*args,**kwargs):
        res = {
            'code': 200,
            'message': '获取用户信息成功',
            'data': ''
        }
        try:
            userinfo = list(UserInfo.objects.filter(username=request.user.username).values('id','username','email'))
            if len(userinfo) > 0:
                res['data'] = userinfo[0]
            else:
                res['data'] = {}
        except Exception as e:
            res["code"] = 400
            res["message"] = f"获取用户信息失败,{e}"
        return JsonResponse(res)


# 用户管理
class UsersViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = UserInfo.objects.all()
    serializer_class = UsersSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.UserInfoFilter

    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": [],
            "message": "success"
        }
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                for user in serializer.data:
                    user["roles"] = [r[0] for r in list(UserRoles.objects.filter(user=user.get("id")).values_list("role"))]
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            res["data"] = serializer.data
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询用户列表失败，{e}"
        return JsonResponse(res)

    def create(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "message": "success",
            "data": ""
        }
        try:
            with transaction.atomic():
                roles = request.data.get("roles", "")
                request.data.pop("roles")
                user = UserInfo.objects.create_user(**request.data)
                if len(roles) > 0:
                    add_user_roles = []
                    for role in roles:
                        add_user_roles.append(UserRoles(user=user.id, role=role))
                    UserRoles.objects.bulk_create(add_user_roles)
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"创建用户失败，{e}"
        return JsonResponse(res)

    def update(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": "",
            "message": "success"
        }
        try:
            with transaction.atomic():
                # 更新用户信息
                partial = kwargs.pop('partial', False)
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                if getattr(instance, '_prefetched_objects_cache', None):
                    instance._prefetched_objects_cache = {}
                # 更新用户角色关联信息
                current_roles = [r[0] for r in list(UserRoles.objects.filter(user=serializer.data["id"]).values_list("role"))]
                delete_roles = list(set(current_roles) - set(request.data.get("roles")))  # 需要删除的角色ID
                UserRoles.objects.filter(user=serializer.data["id"], role__in=delete_roles).delete()
                add_roles = list(set(request.data.get("roles")) - set(current_roles))  # 需要关联的角色ID
                add_user_roles = []
                for role in add_roles: add_user_roles.append(UserRoles(user=serializer.data["id"], role=role))
                UserRoles.objects.bulk_create(add_user_roles)
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"更新用户信息失败，{e}"
        return JsonResponse(res)

    def destroy(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": [],
            "message": "success"
        }
        try:
            with transaction.atomic():
                # 删除用户
                UserInfo.objects.filter(id=kwargs.get("pk")).delete()
                # 删除用户绑定的角色关联
                UserRoles.objects.filter(user=kwargs.get("pk")).delete()
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"删除用户失败，{e}"
        return JsonResponse(res)


# 角色管理
class RolesViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Roles.objects.get_queryset().order_by("id")
    serializer_class = RolesSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.RolesFilter

    def list(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "data": [],
            "message": "success"
        }
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                for role in serializer.data:
                    role["permissions"] = [p[0] for p in list(RolePermissions.objects.filter(role=role.get("id")).values_list("permission"))]
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            res["data"] = serializer.data
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询角色列表失败，{e}"
        return JsonResponse(res)


# 权限管理
class PermissionsViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Permissions.objects.all()
    serializer_class = PermissionsSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.PermissionsFilter


# 生成菜单树
class TreeMenuView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "message": "success",
            "data": []
        }
        try:
            # 递归获取菜单树
            def recursion_menu(menu, roles=None):
                if roles is not None:
                    r_string = []
                    for r in roles:
                        r_string.append(str(r))
                    menuRaw = Permissions.objects.raw(f"""select system_permissions.* from system_permissions left join system_role_permissions on system_permissions.id = system_role_permissions.permission where system_role_permissions.role in ({','.join(r_string)}) and system_permissions.parent = {menu["id"]} and system_permissions.type = 1 order by system_permissions.`sort`;""")
                    m_list = []
                    for mr in menuRaw:
                        d = {}
                        for mc in menuRaw.columns:
                            d[mc] = getattr(mr, mc)
                        m_list.append(d)
                else:
                    m_list = list(Permissions.objects.filter(parent=menu["id"], type=1).order_by("sort").values())
                tmp_m_list = []
                for i in m_list:
                    tmp_m_list.append(i)
                    recursion_menu(i, roles)
                menu["children"] = tmp_m_list
                return menu

            # 查询用户角色
            user = UserInfo.objects.get(username=request.user.username)
            if user.is_admin:
                roles = None
                top_menu_list = list(Permissions.objects.filter(type=1, parent=0).order_by("sort").values())
            else:
                roles = [r[0] for r in list(UserRoles.objects.filter(user=user.id).values_list("role"))]

                # 查询当前角色的权限
                permissions = list(
                    set([p[0] for p in list(RolePermissions.objects.filter(role__in=roles).values_list("permission"))]))
                top_menu_list = list(
                    Permissions.objects.filter(id__in=permissions, type=1, parent=0).order_by("sort").values())
            for i in top_menu_list:
                res["data"].append(recursion_menu(i, roles))
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"获取菜单树失败，{e}"
        return JsonResponse(res)


# 全部权限数据
class PermissionTreeView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "message": "success",
            "data": []
        }
        try:
            title = request.GET.get("title", "")
            if title == "":
                # 递归获取菜单树
                def recursion_menu(menu):
                    children_list = list(Permissions.objects.filter(parent=menu["id"]).order_by("sort").values())
                    if len(children_list) > 0:
                        menu["children"] = children_list
                        for m in children_list:
                            recursion_menu(m)
                    return menu
                top_menu_list = list(Permissions.objects.filter(parent=0).order_by("sort").values())
                for i in top_menu_list:
                    res["data"].append(recursion_menu(i))
            else:
                res["data"] = list(Permissions.objects.filter(title__icontains=title).values())
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"获取菜单树失败，{e}"
        return JsonResponse(res)


# 更新角色权限
class UpdateRolePermissionView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "message": "success",
            "data": []
        }
        try:
            with transaction.atomic():
                # 取消多余的权限关联
                current_permissions = [p[0] for p in list(RolePermissions.objects.filter(role=kwargs.get("pk")).values_list("permission"))]
                delete_permissions = list(set(current_permissions) - set(request.data.get("permissions")))
                RolePermissions.objects.filter(role=kwargs.get("pk"), permission__in=delete_permissions).delete()

                # 添加新的权限关联
                add_permissions = list(set(request.data.get("permissions")) - set(current_permissions))
                add_role_permissions = []
                for perm in add_permissions:
                    add_role_permissions.append(RolePermissions(role=kwargs.get("pk"), permission=perm))
                RolePermissions.objects.bulk_create(add_role_permissions)
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"更新角色权限失败，{e}"
        return JsonResponse(res)


# 获取当前用户的页面标签权限
class UserPermissionsView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        res = {
            "code": 20000,
            "message": "success",
            "data": ""
        }
        try:
            user = UserInfo.objects.get(username=request.user.username)
            if user.is_admin:
                res["data"] = ["*:*:*"]
            else:
                roles = [r[0] for r in list(UserRoles.objects.filter(user=user.id).values_list("role"))]
                permissions = list(set([p[0] for p in list(RolePermissions.objects.filter(role__in=roles).values_list("permission"))]))
                res["data"] = [p[0] for p in list(Permissions.objects.filter(id__in=permissions, type=2).exclude(permission="").values_list("permission"))]
        except Exception as e:
            res["code"] = 40000
            res["message"] = f"查询当前用户的页面标签权限失败，{e}"
        return JsonResponse(res)


class OpLogsViewSet(CustomModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = OpLogs.objects.order_by('-id')
    serializer_class = opLogsSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = filter.OplogFilter

    def list(self, request, *args, **kwargs):
        data = self.request.query_params.get('data', None)
        if data is not None:
            queryset = models.OpLogs.objects.filter(Q(re_time__icontains=data) | Q(re_user__icontains=data) ).values()
            page = self.paginate_queryset(queryset)
        else:
            queryset = models.OpLogs.objects.all()
            page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "code": 20000,
            "data": serializer.data,
            "message": "success"
        }
        return JsonResponse(data, status=status.HTTP_200_OK)