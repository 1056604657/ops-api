import json
import os
import sys
from typing import List
import requests
import datetime
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkecs.v2 import EcsClient, ListServersDetailsRequest
from huaweicloudsdkrds.v3.region.rds_region import RdsRegion
from huaweicloudsdkrds.v3 import *
#from huaweicloudsdkobs.v1 import *
from huaweicloudsdkeip.v3 import *
#from huaweicloudsdkobs.v1.region.obs_region import ObsRegion
from huaweicloudsdkeip.v3.region.eip_region import EipRegion
from huaweicloudsdkelb.v3.region.elb_region import ElbRegion
from huaweicloudsdkelb.v3 import *
from huaweicloudsdkcbr.v1.region.cbr_region import CbrRegion
from huaweicloudsdkcbr.v1 import *
from huaweicloudsdkdcs.v2.region.dcs_region import DcsRegion
from huaweicloudsdkdcs.v2 import *
from huaweicloudsdkrabbitmq.v2.region.rabbitmq_region import RabbitMQRegion
from huaweicloudsdkrabbitmq.v2 import *
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion as VpcRegion_v2
from huaweicloudsdkvpc.v2 import *
from huaweicloudsdkvpc.v2 import VpcClient as VpcClient_v2
from huaweicloudsdknat.v2.region.nat_region import NatRegion
from huaweicloudsdknat.v2 import *
from huaweicloudsdkvpc.v3.region.vpc_region import VpcRegion as VpcRegion_v3
from huaweicloudsdkvpc.v3 import *
from huaweicloudsdkvpc.v3 import VpcClient as VpcClient_v3
from huaweicloudsdkdds.v3.region.dds_region import DdsRegion
from huaweicloudsdkdds.v3 import *
import xml.etree.ElementTree as ET

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config', 'hz_jiache_config.json')

# 使用相对于脚本的路径读取配置文件
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_token():
    print("开始获取token...")
    url = "http://127.0.0.1:8000/get-jwt-token"
    body = {
        "username": "admin",
        "password": "admin"
    }
    print(f"请求URL: {url}")
    print(f"请求体: {body}")
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=body)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.content}")
    res = 'JWT ' + eval(response.content.decode())['data']
    print(f"生成的token: {res}")
    return res

def get_ecs_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = EcsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(EcsRegion.value_of(region_key)) \
                .build()
            try:
                request = ListServersDetailsRequest()
                request.limit = 500
                response = client.list_servers_details(request)
                account_summary[account_key] += response.count 
                
                for server in response.servers: 
                    server_dict = server.to_dict()
                    private_ip = None
                    floating_ip = None
                    if 'addresses' in server_dict:
                        addresses = server_dict['addresses']
                        if isinstance(addresses, dict):
                            for network_interface, ip_list in addresses.items(): 
                                for ip_info in ip_list:
                                    ip_type = ip_info.__dict__.get('_os_ext_ip_stype', None)
                                    addr = ip_info.addr 
                                    if ip_type is not None:
                                        ip_info_dict = {
                                            "addr": addr,
                                            "type": ip_type
                                        }
                                        if ip_type == 'fixed':
                                            private_ip = ip_info_dict["addr"] 
                                        elif ip_type == 'floating':
                                            floating_ip = ip_info_dict["addr"] 
                        else:
                            print(f"addresses 不是字典类型: {addresses}") 

                    #获取系统名称
                    if 'metadata' in server_dict:
                        metadata = server_dict['metadata']
                        system_name = metadata.get('image_name', None)
                        
                    else:
                        system_name = None
                    
                    configuration = []
                    configuration.append("cpu:")
                    configuration.append(server_dict['flavor']['vcpus'])
                    configuration.append("/")
                    configuration.append("memory:")
                    configuration.append(server_dict['flavor']['ram'])
                    configuration.append("/")
                    configuration.append("disk:")
                    configuration.append(server_dict['flavor']['name'])
                    data = {
                        "ecs_id": server_dict['id'], 
                        "name": server_dict['name'],
                        "region": regions[region_key],
                        "account": account_key,
                        "configuration": configuration,
                        "private_ip": private_ip, 
                        "floating_ip": floating_ip,
                        "status": server_dict['status'],
                        "system_name": system_name
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 ECS")

    return {
        'model': 3,
        'data': results
    }

def get_rds_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = RdsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(RdsRegion.value_of(region_key)) \
                .build()
            try:
                request = ListInstancesRequest()
                response = client.list_instances(request)
                account_summary[account_key] += len(response.instances) 
                

                for instance in response.instances: 
                    instance_dict = instance.to_dict()
                    data = {
                        "rds_id": instance_dict['id'],
                        "name": instance_dict['name'],
                        "region": regions[region_key],
                        "status": instance_dict['status'],
                        "private_ip": ','.join(instance_dict['private_ips']),
                        "type": instance_dict['type'],
                        "flavor_ref": instance_dict['flavor_ref'],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 RDS")

    return {
        'model': 4,
        'data': results
    }

def get_obs_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = ObsCredentials(ak, sk) 
            client = ObsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(ObsRegion.value_of(region_key)) \
                .build()
            try:    
                request = ListBucketsRequest()
                response = client.list_buckets(request)
                root = ET.fromstring(response.content)
                buckets = root.findall('.//{http://obs.myhwclouds.com/doc/2015-06-30/}Bucket')
                for bucket in buckets:
                    bucket_dict = {
                        'name': bucket.find('{http://obs.myhwclouds.com/doc/2015-06-30/}Name').text,
                        'location': bucket.find('{http://obs.myhwclouds.com/doc/2015-06-30/}Location').text
                    }
                    results.append(bucket_dict)
                    print(results)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")


    return {
        'model': 6,
        'data': results
    }

def get_eip_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = EipClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(EipRegion.value_of(region_key)) \
                .build()
            try:
                request = ListPublicipsRequest()
                request.limit = 200
                response = client.list_publicips(request)
                account_summary[account_key] += response.total_count

                for publicip in response.publicips: 
                    publicip_dict = publicip.to_dict()
                    if publicip_dict.get('vnic'):
                        vpc_id = publicip_dict['vnic']['vpc_id']
                        instance_id = publicip_dict['vnic']['instance_id']
                        instance_type = publicip_dict['vnic']['instance_type']
                    else:
                        vpc_id = None
                        instance_id = None
                        instance_type = None
                    data = {
                        "eip_id": publicip_dict['id'],
                        "public_ip_address": publicip_dict['public_ip_address'],
                        "vpc_id": vpc_id,
                        "instance_id": instance_id,
                        "instance_type": instance_type,
                        "associate_instance_type": publicip_dict['associate_instance_type'],
                        "associate_instance_id": publicip_dict['associate_instance_id'],
                        "status": publicip_dict['status'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 EIP")

    return {
        'model': 5,
        'data': results
    }

def get_elb_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = ElbClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(ElbRegion.value_of(region_key)) \
                .build()
            try:
                request = ListLoadBalancersRequest()
                request.limit = 500
                response = client.list_load_balancers(request)
                account_summary[account_key] += response.page_info.current_count

                for loadbalancer in response.loadbalancers: 
                    loadbalancer_dict = loadbalancer.to_dict()
                    listeners = loadbalancer_dict['listeners']
                    listener_list = []
                    for listener in listeners:
                        listener_list.append(listener['id']) 
                    listener_ids = '******'.join(listener_list)
                    publicip_address = []
                    for publicip in loadbalancer_dict['publicips']:
                        publicip_address.append(publicip.get('publicip_address'))
                        publicip_address = '******'.join(publicip_address)

                    data = {
                        "elb_id": loadbalancer_dict['id'],
                        "name": loadbalancer_dict['name'],
                        "description": loadbalancer_dict['description'],
                        "listeners": listener_ids, 
                        "vip_address": loadbalancer_dict['vip_address'],   # IPv4私有地址
                        "vip_subnet_cidr_id": loadbalancer_dict['vip_subnet_cidr_id'],  #IPv4子网id
                        "publicip_address": publicip_address,    #IPv4公网地址
                        "vpc_id": loadbalancer_dict['vpc_id'],   #所属虚拟私有云id
                        "operating_status": loadbalancer_dict['operating_status'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 ELB")

    return {
        'model': 6,
        'data': results
    }


def get_cbr_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = CbrClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(CbrRegion.value_of(region_key)) \
                .build()
            try:
                request = ListVaultRequest()
                response = client.list_vault(request)
                account_summary[account_key] += len(response.vaults)

                for vault in response.vaults: 
                    vault_dict = vault.to_dict()
                    
                    data = {
                        "cbr_id": vault_dict['id'],
                        "name": vault_dict['name'],
                        "account": account_key,
                        "region": regions[region_key],
                        "type": vault_dict['billing']['protect_type'], 
                        "resource_name": vault_dict['resources'][0]['name'],
                        "resource_id": vault_dict['resources'][0]['id'],
                        "backup_count": vault_dict['resources'][0]['backup_count'],
                        "status": vault_dict['billing']['status'],
                        "size": vault_dict['billing']['size'],
                        "used": vault_dict['billing']['used'],
                        "allocated": vault_dict['billing']['allocated'],
                        "auto_expand": vault_dict['auto_expand'],
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 CBR")

    return {
        'model': 7,
        'data': results
    }

def get_redis_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = DcsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(DcsRegion.value_of(region_key)) \
                .build()
            try:
                request = ListInstancesRequest()
                response = client.list_instances(request)
                account_summary[account_key] += response.instance_num

                for instance in response.instances: 
                    instance_dict = instance.to_dict()
                    data = {
                        "redis_id": instance_dict['instance_id'],
                        "name": instance_dict['name'],
                        "status": instance_dict['status'],
                        "max_memory": instance_dict['max_memory'],
                        "used_memory": instance_dict['used_memory'],
                        "domain_name": instance_dict['domain_name'],
                        "engine_version": instance_dict['engine_version'],
                        "ip": instance_dict['ip'],
                        "port": instance_dict['port'],
                        "capacity": instance_dict['capacity'],
                        "capacity_minor": instance_dict['capacity_minor'],
                        "cpu_type": instance_dict['cpu_type'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 Redis")

    return {
        'model': 8,
        'data': results
    }

def get_rabbitmq_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = RabbitMQClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(RabbitMQRegion.value_of(region_key)) \
                .build()
            try:
                request = ListInstancesDetailsRequest()
                request.engine = "rabbitmq"
                response = client.list_instances_details(request)
                account_summary[account_key] += response.instance_num

                for instance in response.instances: 
                    instance_dict = instance.to_dict()
                    data = {
                        "rabbitmq_id": instance_dict['instance_id'],
                        "name": instance_dict['name'],
                        "status": instance_dict['status'],
                        "connect_address": instance_dict['connect_address'],
                        "port": instance_dict['port'],
                        "management_connect_address": instance_dict['management_connect_address'],
                        "specification": instance_dict['specification'],
                        "engine_version": instance_dict['engine_version'],
                        "storage_resource_id": instance_dict['storage_resource_id'],
                        "storage_space": instance_dict['storage_space'],
                        "total_storage_space": instance_dict['total_storage_space'],
                        "used_storage_space": instance_dict['used_storage_space'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 RabbitMQ")

    return {
        'model': 10,
        'data': results
    }

def get_vpc_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = VpcClient_v3.new_builder() \
                .with_credentials(credentials) \
                .with_region(VpcRegion_v3.value_of(region_key)) \
                .build()
            try:
                request = ListVpcsRequest()
                response = client.list_vpcs(request)
                account_summary[account_key] += len(response.vpcs)

                for vpc in response.vpcs: 
                    vpc_dict = vpc.to_dict()
                    data = {
                        "vpc_id": vpc_dict['id'],
                        "name": vpc_dict['name'],
                        "description": vpc_dict['description'],
                        "status": vpc_dict['status'],
                        "cidr": vpc_dict['cidr'],
                        "routetable_count": vpc_dict['cloud_resources'][0]['resource_count'],
                        "virsubnet_count": vpc_dict['cloud_resources'][1]['resource_count'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 VPC")

    return {
        'model': 11,
        'data': results
    }

def get_nat_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = NatClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(NatRegion.value_of(region_key)) \
                .build()
            try:
                request = ListNatGatewaysRequest()
                response = client.list_nat_gateways(request)
                print("response!!!!!!!!",response)
                account_summary[account_key] += len(response.nat_gateways)

                for nat_gateway in response.nat_gateways: 
                    nat_gateway_dict = nat_gateway.to_dict()
                    data = {
                        "nat_id": nat_gateway_dict['id'],
                        "name": nat_gateway_dict['name'],
                        "vpc_id": nat_gateway_dict['router_id'],
                        "status": nat_gateway_dict['status'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 NAT")

    return {
        'model': 13,
        'data': results
    }

def get_snat_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = NatClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(NatRegion.value_of(region_key)) \
                .build()
            try:
                request = ListNatGatewaySnatRulesRequest()
                response = client.list_nat_gateway_snat_rules(request)
                account_summary[account_key] += len(response.snat_rules)

                for snat_rule in response.snat_rules: 
                    snat_rule_dict = snat_rule.to_dict()
                    data = {
                        "snat_id": snat_rule_dict['nat_gateway_id'],
                        "nat_gateway_id": snat_rule_dict['nat_gateway_id'], #表示NAT网关
                        "floating_ip_address": snat_rule_dict['floating_ip_address'], #表示浮动IP
                        "status": snat_rule_dict['status'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个SNAT规则")

    return {
        'model': 22,
        'data': results
    }



def get_dnat_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = NatClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(NatRegion.value_of(region_key)) \
                .build()
            try:
                request = ListNatGatewayDnatRulesRequest()
                response = client.list_nat_gateway_dnat_rules(request)
                account_summary[account_key] += len(response.dnat_rules)

                for dnat_rule in response.dnat_rules: 
                    dnat_rule_dict = dnat_rule.to_dict()
                    data = {
                        "dnat_id": dnat_rule_dict['id'],
                        "nat_gateway_id": dnat_rule_dict['nat_gateway_id'],
                        "floating_ip_address": dnat_rule_dict['floating_ip_address'],
                        "external_service_port": dnat_rule_dict['external_service_port'],
                        "private_ip": dnat_rule_dict['private_ip'],
                        "internal_service_port": dnat_rule_dict['internal_service_port'],
                        "status": dnat_rule_dict['status'],
                        "protocol": dnat_rule_dict['protocol'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个DNAT规则")

    return {
        'model': 14,
        'data': results
    }

def get_secgrouprule_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        account_rule = 0
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = VpcClient_v2.new_builder() \
                .with_credentials(credentials) \
                .with_region(VpcRegion_v2.value_of(region_key)) \
                .build()
            try:
                request = ListSecurityGroupsRequest()
                response = client.list_security_groups(request)
                account_summary[account_key] += len(response.security_groups)
                account_rule = 0
                for secgroup in response.security_groups:
                    for security_group_rule in secgroup.security_group_rules:
                        data = {
                            "secgrouprule_id": secgroup.id,
                            "name": secgroup.name,
                            "description": secgroup.description,
                            "rule_description": security_group_rule.description,
                            "direction": security_group_rule.direction,
                            "protocol": security_group_rule.protocol,
                            "ethertype": security_group_rule.ethertype,
                            "port_range_max": security_group_rule.port_range_max,
                            "port_range_min": security_group_rule.port_range_min,
                            "remote_ip_prefix": security_group_rule.remote_ip_prefix, 
                            "remote_address_group_id": security_group_rule.remote_address_group_id, 
                            "region": regions[region_key],
                            "account": account_key,
                        }
                        account_rule += 1
                        results.append(data)
                account_summary[account_key] += account_rule
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")
    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个安全组规则")
    return {
        'model': 15,
        'data': results
    }

def get_ipgroup_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = VpcClient_v3.new_builder() \
                .with_credentials(credentials) \
                .with_region(VpcRegion_v3.value_of(region_key)) \
                .build()
            try:
                request = ListAddressGroupRequest()
                response = client.list_address_group(request)
                account_summary[account_key] += len(response.address_groups)

                for address_group in response.address_groups: 
                    address_group_dict = address_group.to_dict()
                    data = {
                        "ipgroup_id": address_group_dict['id'],
                        "name": address_group_dict['name'],
                        "description": address_group_dict['description'],
                        "status": address_group_dict['status'],
                        "ip_set": "******".join(address_group_dict['ip_set']), 
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个IP组")

    return {
        'model': 16,
        'data': results
    }

def get_routetable_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = VpcClient_v2.new_builder() \
                .with_credentials(credentials) \
                .with_region(VpcRegion_v2.value_of(region_key)) \
                .build()
            try:
                request = ListRouteTablesRequest()
                response = client.list_route_tables(request)
                account_summary[account_key] += len(response.routetables)

                for routetable in response.routetables: 
                    routetable_dict = routetable.to_dict()
                    subnet_ids = [subnet['id'] for subnet in routetable_dict['subnets']]
                    data = {
                        "routetable_id": routetable_dict['id'],
                        "name": routetable_dict['name'],
                        "vpc_id": routetable_dict['vpc_id'],
                        "subnets": "******".join(subnet_ids), 
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询��� {count} 个路由表")

    return {
        'model': 20,
        'data': results
    }

def get_subnet_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = VpcClient_v2.new_builder() \
                .with_credentials(credentials) \
                .with_region(VpcRegion_v2.value_of(region_key)) \
                .build()
            try:
                request = ListSubnetsRequest()
                response = client.list_subnets(request)
                account_summary[account_key] += len(response.subnets)

                for subnet in response.subnets: 
                    subnet_dict = subnet.to_dict()
                    data = {
                        "subnet_id": subnet_dict['id'],
                        "name": subnet_dict['name'],
                        "description": subnet_dict['description'],
                        "status": subnet_dict['status'],
                        "cidr": subnet_dict['cidr'],
                        "dns_list": "******".join(subnet_dict['dns_list']),
                        "vpc_id": subnet_dict['vpc_id'],
                        "gateway_ip": subnet_dict['gateway_ip'],
                        "neutron_network_id": subnet_dict['neutron_network_id'],#代表
                        "neutron_subnet_id": subnet_dict['neutron_subnet_id'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个子网")

    return {
        'model': 21,
        'data': results
    }

def get_mongodb_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk) 
            client = DdsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(DdsRegion.value_of(region_key)) \
                .build()
            try:
                request = ListInstancesRequest()
                response = client.list_instances(request)
                account_summary[account_key] += response.total_count

                for instance in response.instances: 
                    instance_dict = instance.to_dict()


                    nodes_info = []
                    
                    # 遍历所有组
                    groups = instance_dict.get('groups', [])
                    for group in groups:
                        nodes = group.get('nodes', [])
                        for node in nodes:
                            node_data = {
                                "node_name": node.get('name'),
                                "private_ip": node.get('private_ip'),
                                "role": node.get('role')
                            }
                            nodes_info.append(node_data)
                            nodes_info_str = json.dumps(nodes_info)
                    data = {
                        "mongodb_id": instance_dict['id'],
                        "name": instance_dict['name'],
                        "status": instance_dict['status'],
                        "port": instance_dict['port'],
                        "mode": instance_dict['mode'],
                        "version": instance_dict['datastore']['version'],
                        "type": instance_dict['datastore']['type'],
                        "db_user_name": instance_dict['db_user_name'],
                        "vpc_id": instance_dict['vpc_id'],
                        "subnet_id": instance_dict['subnet_id'],
                        "security_group_id": instance_dict['security_group_id'],
                        "maintenance_window": instance_dict['maintenance_window'],
                        "size": instance_dict['groups'][0]['volume']['size'],
                        "used": instance_dict['groups'][0]['volume']['used'],
                        "nodes": nodes_info_str,
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 MongoDB")

    return {
        'model': 23,
        'data': results
    }

def get_port_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            credentials = BasicCredentials(ak, sk)
            client = VpcClient_v2.new_builder() \
                .with_credentials(credentials) \
                .with_region(VpcRegion_v2.value_of(region_key)) \
                .build()
            try:
                request = ListPortsRequest()
                response = client.list_ports(request)
                account_summary[account_key] += len(response.ports)

                for port in response.ports: 
                    port_dict = port.to_dict()
                    data = {
                        "port_id": port_dict['id'],
                        "name": port_dict['name'],
                        "status": port_dict['status'],
                        "admin_state_up": str(port_dict['admin_state_up']),
                        "mac_address": port_dict['mac_address'],
                        "network_id": port_dict['network_id'],
                        "tenant_id": port_dict['tenant_id'],
                        "device_id": port_dict['device_id'],
                        "device_owner": port_dict['device_owner'],
                        "security_groups": "******".join(port_dict['security_groups']),
                        "port_security_enabled": str(port_dict['port_security_enabled']),
                        "instance_type": port_dict['instance_type'],
                        "instance_id": port_dict['instance_id'],
                        "region": regions[region_key],
                        "account": account_key,
                    }
                    
                    # 处理 fixed_ips
                    if 'fixed_ips' in port_dict and port_dict['fixed_ips']:
                        data['subnet_id'] = port_dict['fixed_ips'][0]['subnet_id']
                        data['ip_address'] = port_dict['fixed_ips'][0]['ip_address']
                    results.append(data)
            except exceptions.ClientRequestException as e:
                print(f"！！！！！！发生错误: {e.error_msg} 在区域: {regions[region_key]} 账号: {account_key}")
            except Exception as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个端口")

    return {
        'model': 24, 
        'data': results
    }

def _send_cmdb_request():
    url = "http://127.0.0.1:8000/api/v1/cmdb/resource"
    print("开始获取JWT token...")
    jwt_token = get_token()
    print("JWT token获取成功")

    print("\n开始获取ECS数据...")
    ecsdata = get_ecs_detail()
    print("ECS数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=ecsdata, headers={"Authorization": jwt_token})
    print(f"ECS数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取RDS数据...")
    rdsdata = get_rds_detail()
    print("RDS数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=rdsdata, headers={"Authorization": jwt_token})
    print(f"RDS数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取EIP数据...")
    eipdata = get_eip_detail()
    print("EIP数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=eipdata, headers={"Authorization": jwt_token})
    print(f"EIP数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取ELB数据...")
    elbdata = get_elb_detail()
    print("ELB数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=elbdata, headers={"Authorization": jwt_token})
    print(f"ELB数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取CBR数据...")
    cbrdata = get_cbr_detail()
    print("CBR数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=cbrdata, headers={"Authorization": jwt_token})
    print(f"CBR数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取Redis数据...")
    redisdata = get_redis_detail()
    print("Redis数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=redisdata, headers={"Authorization": jwt_token})
    print(f"Redis数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取RabbitMQ数据...")
    rabbitmqdata = get_rabbitmq_detail()
    print("RabbitMQ数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=rabbitmqdata, headers={"Authorization": jwt_token})
    print(f"RabbitMQ数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取VPC数据...")
    vpcdata = get_vpc_detail()
    print("VPC数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=vpcdata, headers={"Authorization": jwt_token})
    print(f"VPC数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取NAT数据...")
    natdata = get_nat_detail()
    print("NAT数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=natdata, headers={"Authorization": jwt_token})
    print(f"NAT数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取DNAT数据...")
    dnatdata = get_dnat_detail()
    print("DNAT数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=dnatdata, headers={"Authorization": jwt_token})
    print(f"DNAT数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取安全组规则数据...")
    secgrouprule_data = get_secgrouprule_detail()
    print("安全组规则数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=secgrouprule_data, headers={"Authorization": jwt_token})
    print(f"安全组规��数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取IP组数据...")
    ipgroupdata = get_ipgroup_detail()
    print("IP组数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=ipgroupdata, headers={"Authorization": jwt_token})
    print(f"IP组数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取路由表数据...")
    routetabledata = get_routetable_detail()
    print("路由表数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=routetabledata, headers={"Authorization": jwt_token})
    print(f"路由表数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取子网数据...")
    subnetdata = get_subnet_detail()
    print("子网数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=subnetdata, headers={"Authorization": jwt_token})
    print(f"子网数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取SNAT数据...")
    snatdata = get_snat_detail()
    print("SNAT数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=snatdata, headers={"Authorization": jwt_token})
    print(f"SNAT数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取MongoDB数据...")
    mongodbdata = get_mongodb_detail()
    print("MongoDB数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=mongodbdata, headers={"Authorization": jwt_token})
    print(f"MongoDB数据发送完成,响应状态: {response.status_code}\n")

    print("开始获取端口数据...")
    portdata = get_port_detail()
    print("端口数据获取完成,准备发送到CMDB")
    response = requests.post(url, json=portdata, headers={"Authorization": jwt_token})
    print(f"端口数据发送完成,响应状态: {response.status_code}\n")

    print("所有数据同步完成!")
    return response.content


if __name__ == '__main__':
    #get_ecs_detail()
    #get_rds_detail()
    #get_obs_detail()
    #get_eip_detail()
    #get_vpc_detail()
    #get_elb_detail()
    #get_cbr_detail()
    #get_nat_detail()
    #get_dnat_detail()
    #get_secgrouprule_detail()
    #get_ipgroup_detail()
    #get_routetable_detail()
    #get_subnet_detail()
    #get_snat_detail()
    #get_mongodb_detail()
    #get_port_detail()
    _send_cmdb_request()
