import os
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkswr.v2.region.swr_region import SwrRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkswr.v2 import *
import json
import types
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tcr.v20190924 import tcr_client, models


import os

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建配置文件的相对路径
hz_jiache_config_path = os.path.join(current_dir, '../../../agent/config/hz_jiache_config.json')
tencent_config_path = os.path.join(current_dir, '../../../agent/config/tencent_config.json')

def get_latest_image(image_path):
    """
    根据镜像路径获取该镜像的最新10个标签
    
    Args:
        image_path: 镜像完整路径，如 swr.cn-north-4.myhuaweicloud.com/jdocloud/appstoremanager-v2
    
    Returns:
        list: 包含镜像信息的字典列表
    """
    with open(hz_jiache_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    results = []
    with open(tencent_config_path, 'r', encoding='utf-8') as f:
        tencent_config = json.load(f)
    # 解析镜像路径
    try:
        parts = image_path.split('/')
        domain_parts = parts[0].split('.')
        target_region = domain_parts[1]  # cn-north-4
        namespace = parts[1]  # jdocloud
        repository = parts[2]  # appstoremanager-v2
    except Exception as e:
        print(f"解析镜像路径失败: {str(e)}")
        return results
    if domain_parts[0] == "swr":
        # 循环账号查找镜像
        for account_key, account_info in config.items(): 
            try:
                # 检查账号是否包含目标区域
                if target_region not in account_info["regions"]:
                    continue
                    
                ak = account_info["ak"]
                sk = account_info["sk"]
                credentials = BasicCredentials(ak, sk)
                
                try:
                    client = SwrClient.new_builder() \
                        .with_credentials(credentials) \
                        .with_region(SwrRegion.value_of(target_region)) \
                        .build()

                    request = ListReposDetailsRequest()
                    request.name = repository
                    response = client.list_repos_details(request)
                    
                    repos = response.body
                    print(repos)
                    if not repos:
                        print(f"账号 {account_key} 查询区域 {target_region} 未找到仓库")
                        continue
                    
                    # 遍历找到的仓库，修改这里进行精确匹配
                    for repo_info in repos:
                        if not isinstance(repo_info, dict):
                            repo_info = repo_info.to_dict()
                        
                        # 精确匹配仓库名称和命名空间
                        if (repo_info.get('namespace') == namespace and 
                            repo_info.get('name') == repository):  # 确保仓库名完全匹配
                            tags = repo_info.get('tags', [])
                            # 只处理符合格式的标签（包含时间戳的标签）
                            time_tags = []
                            for tag in tags:
                                if '_202' in tag:  # 确保是带时间戳的标签
                                    try:
                                        # 提取时间戳部分 (YYYYMMDD_HHMM)
                                        timestamp = tag.split('_')[-2] + '_' + tag.split('_')[-1]
                                        time_tags.append((tag, timestamp))
                                    except:
                                        continue
                            
                            # 按时间戳排序
                            sorted_tags = sorted(time_tags, 
                                              key=lambda x: x[1], 
                                              reverse=True)
                            
                            # 只获取标签名称
                            final_tags = [tag[0] for tag in sorted_tags[:10]]
                            
                            print("在",account_key,"中的",target_region,"地区找到镜像",repo_info.get('path'))
                            results.append({
                                'image_path': repo_info.get('path'),
                                'latest_tags': final_tags
                            })
                            print(results)
                            
                except Exception as e:
                    print(f"账号 {account_key} 查询区域 {target_region} 时发生错误: {str(e)}")
                    continue
                    
            except Exception as e:
                print(f"处理账号 {account_key} 时发生错误: {str(e)}")
                continue
                
        return results
    else:
        for account_key, account_info in tencent_config.items(): 
            try:
                ak = account_info["ak"]
                sk = account_info["sk"]
                region = "ap-beijing"
                cred = credential.Credential(ak, sk)
                client = tcr_client.TcrClient(cred, region)
                req = models.DescribeImagesRequest()
                params = {
                    "RegistryId": "tcr-a5syzy3a",
                    "NamespaceName": namespace,
                    "RepositoryName": repository
                }
                req.from_json_string(json.dumps(params))
                
                resp = client.DescribeImages(req)
                
                # 解析响应
                if hasattr(resp, 'ImageInfoList') and resp.ImageInfoList:
                    # 按更新时间排序
                    sorted_images = sorted(resp.ImageInfoList, 
                                        key=lambda x: x.UpdateTime,
                                        reverse=True)
                    
                    # 提取tag列表
                    tags = [img.ImageVersion for img in sorted_images]
                    print("在", account_key, "中的", target_region, "地区找到镜像", image_path)
                    results.append({
                        'image_path': image_path,
                        'latest_tags': tags[:10]  # 只取最新的10个标签
                    })
                else:
                    print(f"账号 {account_key} 查询区域 {target_region} 未找到镜像")
                    
            except Exception as e:
                print(f"账号 {account_key} 查询区域 {target_region} 时发生错误: {str(e)}")
                continue
                
        return results


image_path = "swr.cn-east-2.myhuaweicloud.com/gwm/priority"
image2_path = "hcp3-image-service.tencentcloudcr.com/hcp3-live/forward"
image3_path = "swr.cn-east-2.myhuaweicloud.com/bi-project/analysis"
results = get_latest_image(image3_path)
print(results)