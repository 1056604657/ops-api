import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkswr.v2.region.swr_region import SwrRegion
from huaweicloudsdkswr.v2 import *

def test_get_latest_image(account, region, namespace, repository):
    # 读取配置文件
    with open('/Users/babyyy/工作/JD/CMDB平台/ops_api/agent/config/hz_jiache_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 获取认证信息
    ak = config[account]["ak"]
    sk = config[account]["sk"]
    
    # 创建认证对象
    credentials = BasicCredentials(ak, sk)
    
    # 创建客户端
    client = SwrClient.new_builder() \
        .with_credentials(credentials) \
        .with_region(SwrRegion.value_of(region)) \
        .build()
    
    # 创建请求
    request = ListRepositoryTagsRequest()
    request.namespace = namespace
    request.repository = repository
    request.limit = "1"
    request.offset = "0"
    request.order_column = "updated_at"
    request.order_type = "desc"
    
    # 发送请求
    response = client.list_repository_tags(request)
    
    # 解析响应并返回需要的信息
    response_dict = json.loads(str(response.body))
    return {
        "tag": response_dict[0]["Tag"],
        "path": response_dict[0]["path"]
    }

if __name__ == "__main__":
    result = test_get_latest_image(account="hz_jiache", region="cn-north-4", namespace="jdocloud", repository="appstoremanager-v2")
    print(result)