from django.urls import path,include
from rest_framework_jwt.views import obtain_jwt_token
from apps.cmdb import urls as cmdb_url
from apps.tree import urls as tree_url
from apps.system import urls as system_urls
from apps.imagemanagement import urls as imagemanagement_url
from apps.accountmanagement import urls as accountmanagement_url
from apps.devops import urls as devops_url
from apps.cicd import urls as cicd_url
from rest_framework.documentation import include_docs_urls
from rest_framework.permissions import AllowAny
from apps.system.views import ObtainJSONWebToken
from apps.account import urls as account_url

API_VERSION = 'api/v1'

urlpatterns = [
    ## API文档
    path(f'{API_VERSION}/docs', include_docs_urls(title='运维系统API文档', permission_classes=[])),
    ## 登录认证
    path('get-jwt-token', ObtainJSONWebToken.as_view(permission_classes=(AllowAny,))),
    ## CMDB
    path(f'{API_VERSION}/cmdb/', include(cmdb_url)),
    ## 服务树
    path(f'{API_VERSION}/tree/', include(tree_url)),
    ## RBAC
    path(f'{API_VERSION}/system/', include(system_urls)),
    ## 镜像管理
    path(f'{API_VERSION}/imagemanagement/', include(imagemanagement_url)),
    ## 账号管理
    path(f'{API_VERSION}/accountmanagement/', include(accountmanagement_url)),
    ## 运维管理
    path(f'{API_VERSION}/devops/', include(devops_url)),
    ## CICD
    path(f'{API_VERSION}/cicd/', include(cicd_url)),
    ## 高德
    path(f'{API_VERSION}/account/', include(account_url)),
]