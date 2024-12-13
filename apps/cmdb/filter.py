from django_filters import rest_framework as filters
from .models import ModelGroup, Model, FieldGroup, Fields, Resource


class ModelGroupFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')  # name 字段，可以进行模糊搜素

    class Meta:
        model = ModelGroup
        fields = ()  # 精确搜索
        search_fields = ('name',)


class ModelFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')  # name 字段，可以进行模糊搜素

    class Meta:
        model = Model
        fields = ()  # 精确搜索
        search_fields = ('name',)


class FieldGroupFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')  # name 字段，可以进行模糊搜素

    class Meta:
        model = FieldGroup
        fields = ()  # 精确搜索
        search_fields = ('name',)


class FieldsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')  # name 字段，可以进行模糊搜素

    class Meta:
        model = Fields
        fields = ()  # 精确搜索
        search_fields = ('name',)


class ResourceFilter(filters.FilterSet):
    data = filters.CharFilter(field_name='data', lookup_expr='icontains')  # name 字段，可以进行模糊搜素

    class Meta:
        model = Resource
        fields = ['data']
        # fields = ('model',)  # 精确搜索
        # search_fields = ('name',)


