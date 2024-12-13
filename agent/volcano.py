from __future__ import print_function
import volcenginesdkcore
import volcenginesdkecs
from volcenginesdkcore.rest import ApiException
import volcenginesdkvpc
import json
import os
import sys
from typing import List
import requests
import datetime

with open('/Users/babyyy/工作/JD/CMDB平台/ops_api/agent/config/volcano_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_token():
    url = "http://127.0.0.1:8000/get-jwt-token"
    body = {
        "username": "admin",
        "password": "admin"
    }
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=body)
    res = 'JWT ' + eval(response.content.decode())['data']
    return res

def get_vecs_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            configuration = volcenginesdkcore.Configuration()
            configuration.ak = ak
            configuration.sk = sk
            configuration.region = region_key
            volcenginesdkcore.Configuration.set_default(configuration)
            api_instance = volcenginesdkecs.ECSApi()
            describe_instances_request = volcenginesdkecs.DescribeInstancesRequest(
                max_results=100,
            )
            try:
                response = api_instance.describe_instances(describe_instances_request)
                account_summary[account_key] += len(response.instances)
                for server in response.instances: 
                    data = {
                        "vecs_id": server.instance_id,
                        "instance_name": server.instance_name,
                        "status": server.status,
                        "hostname": server.hostname,
                        "cpu": server.cpus,
                        "memory": server.memory_size,
                        "os_name": server.os_name,
                        "instance_type_id":server.instance_type_id,
                        "subnet_id":server.network_interfaces[0].subnet_id,
                        "vpc_id":server.network_interfaces[0].vpc_id,
                        "primary_ip_address":server.network_interfaces[0].primary_ip_address,
                        "ip_address": server.eip_address.ip_address if server.eip_address else None,
                        "region": region_key,
                        "account": account_key
                    }
                    results.append(data)
            except ApiException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 ECS")

    return {
        'model': 25,
        'data': results
    }

def get_vvpc_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            configuration = volcenginesdkcore.Configuration()
            configuration.ak = ak
            configuration.sk = sk
            configuration.region = region_key
            volcenginesdkcore.Configuration.set_default(configuration)
            api_instance = volcenginesdkvpc.VPCApi()
            describe_vpcs_request = volcenginesdkvpc.DescribeVpcsRequest()
            try:
                response = api_instance.describe_vpcs(describe_vpcs_request)
                account_summary[account_key] += len(response.vpcs)
                for server in response.vpcs: 
                    data = {
                        "vvpc_id": server.vpc_id,
                        "vpc_name": server.vpc_name,
                        "cidr_block": server.cidr_block,
                        "status": server.status,
                        "nat_gateway_ids": ', '.join(server.nat_gateway_ids) if server.nat_gateway_ids else None,
                        "route_table_ids": ', '.join(server.route_table_ids) if server.route_table_ids else None,
                        "security_group_ids": ', '.join(server.security_group_ids) if server.security_group_ids else None,
                        "subnet_ids": ', '.join(server.subnet_ids) if server.subnet_ids else None,
                        "region": region_key,
                        "account": account_key
                    }
                    results.append(data)
            except ApiException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 台 VPC")

    return {
        'model': 26,
        'data': results
    }

def get_vsubnet_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            configuration = volcenginesdkcore.Configuration()
            configuration.ak = ak
            configuration.sk = sk
            configuration.region = region_key
            volcenginesdkcore.Configuration.set_default(configuration)
            api_instance = volcenginesdkvpc.VPCApi()
            describe_subnets_request = volcenginesdkvpc.DescribeSubnetsRequest()
            try:
                response = api_instance.describe_subnets(describe_subnets_request)
                account_summary[account_key] += len(response.subnets)
                for server in response.subnets: 
                    data = {
                        "vsubnet_id": server.subnet_id,
                        "subnet_name": server.subnet_name,
                        "cidr_block": server.cidr_block,
                        "status": server.status,
                        "available_ip_address_count": server.available_ip_address_count,
                        "total_ipv4_count": server.total_ipv4_count,
                        "route_table_id": server.route_table.route_table_id,
                        "vpc_id": server.vpc_id,
                        "region": region_key,
                        "account": account_key
                    }
                    results.append(data)
            except ApiException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个子网")

    return {
        'model': 27,
        'data': results
    }

def get_vroute_table_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            configuration = volcenginesdkcore.Configuration()
            configuration.ak = ak
            configuration.sk = sk
            configuration.region = region_key
            volcenginesdkcore.Configuration.set_default(configuration)
            api_instance = volcenginesdkvpc.VPCApi()
            describe_route_table_list_request = volcenginesdkvpc.DescribeRouteTableListRequest()
            try:
                response = api_instance.describe_route_table_list(describe_route_table_list_request)
                account_summary[account_key] += len(response.router_table_list)
                for server in response.router_table_list: 
                    data = {
                        "vroute_table_id": server.route_table_id,
                        "route_table_name": server.route_table_name,
                        "route_table_type": server.route_table_type,
                        "subnet_ids": ', '.join(server.subnet_ids) if server.subnet_ids else None,
                        "vpc_id": server.vpc_id,
                        "vpc_name": server.vpc_name,
                        "region": region_key,
                        "account": account_key
                    }
                    results.append(data)
            except ApiException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个路由表")

    return {
        'model': 28,
        'data': results
    }

def get_vnetwork_interface_detail():
    results = []  
    account_summary = {} 

    for account_key, account_info in config.items(): 
        ak = account_info["ak"]
        sk = account_info["sk"]
        regions = account_info["regions"]
        
        account_summary[account_key] = 0 
        
        for region_key in regions.keys(): 
            configuration = volcenginesdkcore.Configuration()
            configuration.ak = ak
            configuration.sk = sk
            configuration.region = region_key
            volcenginesdkcore.Configuration.set_default(configuration)
            api_instance = volcenginesdkvpc.VPCApi()
            describe_network_interfaces_request = volcenginesdkvpc.DescribeNetworkInterfacesRequest()
            try:
                response = api_instance.describe_network_interfaces(describe_network_interfaces_request)
                account_summary[account_key] += response.total_count
                for server in response.network_interface_sets: 
                    data = {
                        "vnetwork_interface_id": server.network_interface_id,
                        "network_interface_name": server.network_interface_name,
                        "status": server.status,
                        "primary_ip_address": server.primary_ip_address,#网卡的主私网IP地址
                        "eip_address": server.associated_elastic_ip.eip_address if server.associated_elastic_ip else None,#公网IP的IP地址
                        "allocation_id": server.associated_elastic_ip.allocation_id if server.associated_elastic_ip else None,#公网IP的ID
                        "device_id": server.device_id,#网卡绑定的实例ID
                        "security_group_ids": ', '.join(server.security_group_ids) if server.security_group_ids else None,#网卡绑定的安全组ID列表
                        "subnet_id": server.subnet_id,#网卡所属子网ID
                        "vpc_id": server.vpc_id,#网卡所属VPC的ID
                        "vpc_name": server.vpc_name,#网卡所属VPC的名称
                        "tags": server.tags[0].key + ':' + server.tags[0].value if server.tags else None,#网卡绑定的资源ID
                        "region": region_key,
                        "account": account_key
                    }
                    results.append(data)
            except ApiException as e: 
                print(f"发生未知错误: {str(e)} 在区域: {regions[region_key]} 账号: {account_key}")

    for account, count in account_summary.items():
        print(f"账号 {account} 下一共查询到 {count} 个网卡")

    return {
        'model': 29,
        'data': results
    }


def _send_cmdb_request():
    url = "http://127.0.0.1:8000/api/v1/cmdb/resource"
    jwt_token = get_token()
    vecsdata = get_vecs_detail()
    vvpcdata = get_vvpc_detail()
    vsubnetdata = get_vsubnet_detail()
    vroutedata = get_vroute_table_detail()
    vnetwork_interface_data = get_vnetwork_interface_detail()
    response = requests.post(url, json=vecsdata, headers={"Authorization": jwt_token})
    response = requests.post(url, json=vvpcdata, headers={"Authorization": jwt_token})
    response = requests.post(url, json=vsubnetdata, headers={"Authorization": jwt_token})
    response = requests.post(url, json=vroutedata, headers={"Authorization": jwt_token})
    response = requests.post(url, json=vnetwork_interface_data, headers={"Authorization": jwt_token})
    return response.content


if __name__ == '__main__':
    #get_vecs_detail()
    #get_vvpc_detail()
    #get_vsubnet_detail()
    #get_vroute_table_detail()
    #get_vnetwork_interface_detail()
    _send_cmdb_request()
