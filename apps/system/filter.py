from django_filters import rest_framework as filters
from .user.models import UserInfo
from .models import Roles, Permissions, OpLogs


class UserInfoFilter(filters.FilterSet):
    username = filters.CharFilter(field_name='username', lookup_expr='icontains')

    class Meta:
        model = UserInfo
        fields = ()
        search_fields = ('username',)


class RolesFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Roles
        fields = ()
        search_fields = ('name',)


class PermissionsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Permissions
        fields = ()
        search_fields = ('name',)


class OplogFilter(filters.FilterSet):
    re_time = filters.CharFilter(field_name='re_time', lookup_expr='icontains')
    re_uer = filters.CharFilter(field_name='re_user', lookup_expr='icontains')

    class Meta:
        model = OpLogs
        fields = ['re_time', 're_user']