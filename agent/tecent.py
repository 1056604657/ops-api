import json
import types
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cvm.v20170312 import cvm_client, models as cvm_models
import os
import requests
from tencentcloud.vpc.v20170312 import vpc_client, models as vpc_models





current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建配置文件的相对路径
tencent_config_path = os.path.join(current_dir, 'config/tencent_config.json')
config = json.load(open(tencent_config_path, 'r', encoding='utf-8'))

def get_token():
    url = "http://127.0.0.1:8000/get-jwt-token"
    body = {
        "username": "admin",
        "password": "admin"
    }
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=body)
    res = 'JWT ' + eval(response.content.decode())['data']
    return res

def get_tecent_ecs_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            try:
                cred = credential.Credential(ak, sk)
                clientProfile = ClientProfile()
                client = cvm_client.CvmClient(cred, region_key, clientProfile)
                req = cvm_models.DescribeInstancesRequest()
                params = {
                    "Limit": 100
                }
                req.from_json_string(json.dumps(params))

                # 获取响应并解析JSON
                response = client.DescribeInstances(req)
                response_json = json.loads(response.to_json_string())
                
                # 更新账号实例总数
                account_summary[account_key] += response_json['TotalCount']
                #print(account_summary[account_key])
                # 处理每个实例
                for instance in response_json['InstanceSet']:
                    data = {
                        "tecs_id": instance['InstanceId'],
                        "instance_name": instance['InstanceName'],
                        "status": instance['InstanceState'],
                        "cpu": instance['CPU'],
                        "memory": instance['Memory'],
                        "disk": instance['SystemDisk']['DiskSize'],
                        "os_name": instance['OsName'],
                        "instance_type_id": instance['InstanceType'],
                        "subnet_id": instance['VirtualPrivateCloud']['SubnetId'],
                        "vpc_id": instance['VirtualPrivateCloud']['VpcId'],
                        "security_groups": instance['SecurityGroupIds'][0] if instance['SecurityGroupIds'] else None,
                        "primary_ip_address": instance['PrivateIpAddresses'][0] if instance['PrivateIpAddresses'] else None,
                        "ip_address": instance['PublicIpAddresses'][0] if instance.get('PublicIpAddresses') else None,
                        "region": region_key,
                        "account": account_key
                    }
                    #print(data)
                    results.append(data)
                    
            except TencentCloudSDKException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 ECS")

    return {
        'model': 30,
        'data': results
    }

def get_tecent_vpc_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            try:
                cred = credential.Credential(ak, sk)
                clientProfile = ClientProfile()
                client = vpc_client.VpcClient(cred, region_key, clientProfile)
                req = vpc_models.DescribeVpcsRequest()
                params = {
                    "Limit": "100"
                }
                req.from_json_string(json.dumps(params))

                # 获取响应并解析JSON
                response = client.DescribeVpcs(req)
                response_json = json.loads(response.to_json_string())
                
                # 更新账号VPC总数
                account_summary[account_key] += response_json['TotalCount']
                
                # 处理每个VPC
                for vpc in response_json['VpcSet']:
                    # 将辅助CIDR列表转换为逗号分隔的字符串
                    assistant_cidrs = ','.join([assistant['CidrBlock'] for assistant in vpc.get('AssistantCidrSet', [])])
                    
                    data = {
                        "tvpc_id": vpc['VpcId'],
                        "vpc_name": vpc['VpcName'],
                        "cidr": vpc['CidrBlock'],
                        "created_time": vpc['CreatedTime'],
                        "dns_servers": vpc.get('DnsServerSet', []),
                        "domain_name": vpc.get('DomainName', ''),
                        "dhcp_options_id": vpc.get('DhcpOptionsId', ''),
                        "ipv6_cidr": vpc.get('Ipv6CidrBlock', ''),
                        "tags": vpc.get('TagSet', []),
                        "assistant_cidrs": assistant_cidrs,  
                        "region": region_key,
                        "account": account_key
                    }
                    #print(data)
                    results.append(data)
                    
            except TencentCloudSDKException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个 VPC")

    return {
        'model': 31,
        'data': results
    }

def get_tecent_subnet_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            try:
                cred = credential.Credential(ak, sk)
                clientProfile = ClientProfile()
                client = vpc_client.VpcClient(cred, region_key, clientProfile)
                req = vpc_models.DescribeSubnetsRequest()
                params = {
                    "Limit": "100"
                }
                req.from_json_string(json.dumps(params))

                # 获取响应并解析JSON
                response = client.DescribeSubnets(req)
                response_json = json.loads(response.to_json_string())
                
                # 更新账号VPC总数
                account_summary[account_key] += len(response_json['SubnetSet'])
                
                for subnet in response_json['SubnetSet']:
                    data = {
                        "tsubnet_id": subnet['SubnetId'],
                        "subnet_name": subnet['SubnetName'],
                        "cidr": subnet['CidrBlock'],
                        "created_time": subnet['CreatedTime'],
                        "route_table_id": subnet['RouteTableId'],
                        "vpc_id": subnet['VpcId'],
                        "available_ip_count": subnet['AvailableIpAddressCount'],
                        "total_ip_count": subnet['TotalIpAddressCount'],
                        "region": region_key,
                        "account": account_key
                    }
                    #print(data)
                    results.append(data)
                    
            except TencentCloudSDKException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个 子网")

    return {
        'model': 32,
        'data': results
    }







def _send_cmdb_request():
    url = "http://127.0.0.1:8000/api/v1/cmdb/resource"
    jwt_token = get_token()
    tencent_ecs_data = get_tecent_ecs_detail()
    tencent_vpc_data = get_tecent_vpc_detail()
    tencent_subnet_data = get_tecent_subnet_detail()    
    response = requests.post(url, json=tencent_ecs_data, headers={"Authorization": jwt_token})
    response = requests.post(url, json=tencent_vpc_data, headers={"Authorization": jwt_token})
    response = requests.post(url, json=tencent_subnet_data, headers={"Authorization": jwt_token})
    return response.content


if __name__ == '__main__':
    #get_tecent_ecs_detail()
    #get_tecent_vpc_detail()
    #get_tecent_subnet_detail()
    _send_cmdb_request()
