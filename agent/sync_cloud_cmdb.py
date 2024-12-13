import json
import os
import sys
from typing import List
import requests
import datetime
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cvm.v20170312 import cvm_client, models
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from alibabacloud_slb20140515.client import Client as Slb20140515Client
from alibabacloud_slb20140515 import models as slb_20140515_models
from alibabacloud_rds20140815.client import Client as Rds20140815Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_rds20140815 import models as rds_20140815_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_alikafka20190916.client import Client as alikafka20190916Client
from alibabacloud_alikafka20190916 import models as alikafka_20190916_models
from alibabacloud_r_kvstore20150101.client import Client as R_kvstore20150101Client
from alibabacloud_r_kvstore20150101 import models as r_kvstore_20150101_models
from alibabacloud_dds20151201.client import Client as Dds20151201Client
from alibabacloud_dds20151201 import models as dds_20151201_models
from alibabacloud_elasticsearch20170613.client import Client as elasticsearch20170613Client
from alibabacloud_elasticsearch20170613 import models as elasticsearch_20170613_models
from alibabacloud_amqp_open20191212.client import Client as amqp_open20191212Client
from alibabacloud_amqp_open20191212 import models as amqp_open_20191212_models
from alibabacloud_waf_openapi20190910.client import Client as waf_openapi20190910Client
from alibabacloud_waf_openapi20190910 import models as waf_openapi_20190910_models
from alibabacloud_polardb20170801.client import Client as polardb20170801Client
from alibabacloud_polardb20170801 import models as polardb_20170801_models


def get_token():
    url = "http://127.0.0.1:8000/get-jwt-token"
    body = {
        "username": "admin",
        "password": "admin"
    }
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=body)
    res = 'JWT ' + eval(response.content.decode())['data']
    return res


def get_cvm_instance():
    try:
        data_list = []
        params = {}
        cred = credential.Credential("你的腾讯云AK", "你的腾讯云SK")
        httpProfile = HttpProfile()
        httpProfile.endpoint = "cvm.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = cvm_client.CvmClient(cred, "ap-shanghai", clientProfile)
        req = models.DescribeInstancesRequest()
        req.from_json_string(json.dumps(params))
        resp = client.DescribeInstances(req)
        for data in resp.InstanceSet:
            priva_ip = data.PrivateIpAddresses,
            publi_ip = data.PublicIpAddresses,
            item = {
                "instance_id": data.InstanceId,
                "instance_name": data.InstanceName,
                "cpu": data.CPU,
                "memory": data.Memory,
                "status": data.InstanceState,
                "private_ip": priva_ip[0][0],
                "public_ip": publi_ip[0][0],
                "business": "业务系统",
                "idc": "腾讯云",
                "type": "CVM",
                "cluster": "业务集群",
                "disk": data.SystemDisk.DiskSize,
                "create_time": data.CreatedTime,
                "charge": "",
                "description": ""
            }
            data_list.append(item)
        return {
            "model": 5,
            "data": data_list
        }
    except TencentCloudSDKException as err:
        print(err)


def get_ecs_data():
    all_ecs = []
    cli = client.AcsClient('你的阿里云AK', '你的阿里云SK', 'cn-hangzhou')
    res = DescribeInstancesRequest.DescribeInstancesRequest()
    res.set_accept_format('json')
    res.set_PageSize(100)
    for i in range(1, 10):
        res.set_PageNumber(i)
        result = json.loads(cli.do_action_with_exception(res))
        ecs_info_list = result.get('Instances', {}).get('Instance', [])
        for info in ecs_info_list:
            Description = info.get('Description', '')
            network_interfaces = info.get('NetworkInterfaces', {}).get('NetworkInterface', [])
            PrimaryIp = network_interfaces[0].get('PrimaryIpAddress') if network_interfaces else ''
            public_ip_addresses = info.get('PublicIpAddress', {}).get('IpAddress', [])
            pub_ip = public_ip_addresses[0] if public_ip_addresses else ''
            ecs_data = {
                "instance_id": info.get('InstanceId'),
                "instance_name": info.get('InstanceName'),
                "cpu": str(info.get('Cpu')),
                "memory": str(int(info.get('Memory')) / 1024),
                "status": info.get('Status'),
                "private_ip": PrimaryIp,
                "public_ip": pub_ip,
                "business": "业务系统",
                "idc": "阿里云",
                "type": "ECS",
                "cluster": "业务集群",
                "disk": "",
                "create_time": info.get('CreationTime'),
                "charge": "",
                "description": Description
            }
            all_ecs.append(ecs_data)
    return {
        "model": 6,
        "data": all_ecs
    }


class getSlb:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Slb20140515Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'slb.aliyuncs.com'
        return Slb20140515Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getSlb.create_client()
        all_slb = []
        try:
            for i in range(1,10):
                describe_load_balancers_request = slb_20140515_models.DescribeLoadBalancersRequest(
                    region_id='cn-hangzhou',
                    page_number=int(i),
                    page_size=100
                )
                runtime = util_models.RuntimeOptions()
                response = client.describe_load_balancers_with_options(describe_load_balancers_request, runtime)
                data = response.body.to_map()['LoadBalancers']['LoadBalancer']
                all_slb.extend(data)
            return all_slb
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_slb_data():
    slb_list = []
    all_slb = getSlb.main(sys.argv[1:])
    for item in all_slb:
        slb_data = {
            "loadbalancer_id": item.get('LoadBalancerId'),
            "loadbalancer_name": item.get('LoadBalancerName'),
            "status":item.get('LoadBalancerStatus'),
            "ip": item.get('Address'),
            "band_width": item.get('Bandwidth'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": "SLB",
            "cluster": "业务集群",
            "create_time": item.get('CreateTime'),
            "charge": "",
            "description": ""
        }
        slb_list.append(slb_data)
    return {
        "model": 7,
        "data": slb_list
    }


class getRds:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Rds20140815Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'rds.aliyuncs.com'
        return Rds20140815Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        all_rds = []
        client = getRds.create_client()
        try:
            for i in range(1,5):
                describe_dbinstances_request = rds_20140815_models.DescribeDBInstancesRequest(
                    region_id='cn-hangzhou',
                    page_number=int(i),
                    page_size=100
                )
                runtime = util_models.RuntimeOptions()
                res = client.describe_dbinstances_with_options(describe_dbinstances_request, runtime)
                data = res.body.to_map()['Items']['DBInstance']
                all_rds.extend(data)
            return all_rds
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_rds_data():
    rds_list = []
    all_rds = getRds.main(sys.argv[1:])
    for item in all_rds:
        rds_data = {
            "db_id": item.get('DBInstanceId'),
            "db_name": item.get('DBInstanceDescription'),
            "status":item.get('DBInstanceStatus'),
            "db_type": item.get('Engine'),
            "edition": item.get('EngineVersion'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": "RDS",
            "cluster": "业务集群",
            "create_time": item.get('CreateTime'),
            "charge": "",
            "description": "",
        }
        rds_list.append(rds_data)
    return {
        "model": 9,
        "data": rds_list
    }


class getKafka:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> alikafka20190916Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'alikafka.cn-hangzhou.aliyuncs.com'
        return alikafka20190916Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getKafka.create_client()
        get_instance_list_request = alikafka_20190916_models.GetInstanceListRequest(region_id='cn-hangzhou')
        runtime = util_models.RuntimeOptions()
        try:
            res = client.get_instance_list_with_options(get_instance_list_request, runtime)
            items = res.body.to_map()['InstanceList']['InstanceVO']
            return items
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_kafka_data():
    kafka_list = []
    kafka_data = getKafka.main(sys.argv[1:])
    for item in kafka_data:
        kafka_item = {
            "instance_id": item.get('InstanceId'),
            "instance_name": item.get('Name'),
            "status": "running",
            "private_ip": item.get('EndPoint'),
            "disk_size": item.get('DiskSize'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": "kafka",
            "cluster": "业务集群",
            "create_time": datetime.datetime.fromtimestamp(item.get('CreateTime')/1000.0).strftime('%Y-%m-%d %H:%M:%S'),
            "charge": "",
            "charge_center": "",
            "description": "",
        }
        kafka_list.append(kafka_item)
    return {
        "model": 15,
        "data": kafka_list
    }


class getRedis:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> R_kvstore20150101Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'r-kvstore.aliyuncs.com'
        return R_kvstore20150101Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getRedis.create_client()
        describe_instances_request = r_kvstore_20150101_models.DescribeInstancesRequest(
            region_id='cn-hangzhou',
            page_number=1,
            page_size=1000)
        runtime = util_models.RuntimeOptions()
        try:
            res = client.describe_instances_with_options(describe_instances_request, runtime)
            items = res.body.to_map()['Instances']['KVStoreInstance']
            return items
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_redis_data():
    redis_list = []
    redis_data = getRedis.main(sys.argv[1:])
    for item in redis_data:
        redis_item = {
            "instance_id": item.get('InstanceId'),
            "instance_name": item.get('InstanceName'),
            "status": item.get('InstanceStatus'),
            "private_ip": item.get('PrivateIp'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": item.get('InstanceType'),
            "cluster": "业务集群",
            "create_time": item.get('CreateTime'),
            "charge": "",
            "charge_center": "",
            "description": "",
        }
        redis_list.append(redis_item)
    return {
        "model": 16,
        "data": redis_list
    }


class getMogodb:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Dds20151201Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'mongodb.aliyuncs.com'
        return Dds20151201Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getMogodb.create_client()
        describe_dbinstances_request = dds_20151201_models.DescribeDBInstancesRequest(
            region_id='cn-hangzhou'
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.describe_dbinstances_with_options(describe_dbinstances_request, runtime)
            items = res.body.to_map()['DBInstances']['DBInstance']
            return items
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_mogodb_data():
    mogo_list = []
    mogo_data = getMogodb.main(sys.argv[1:])
    for item in mogo_data:
        mogo_item = {
            "instance_id": item.get('DBInstanceId'),
            "instance_name": item.get('DBInstanceDescription'),
            "status": item.get('DBInstanceStatus'),
            "disk_size": item.get('DBInstanceStorage'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": item.get('Engine'),
            "cluster": "业务集群",
            "create_time": item.get('CreationTime'),
            "charge": "",
            "charge_center": "",
            "description": "",
        }
        mogo_list.append(mogo_item)
    return {
        "model": 17,
        "data": mogo_list
    }


class getEs:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> elasticsearch20170613Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'elasticsearch.cn-hangzhou.aliyuncs.com'
        return elasticsearch20170613Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getEs.create_client()
        list_instance_request = elasticsearch_20170613_models.ListInstanceRequest()
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            res = client.list_instance_with_options(list_instance_request, headers, runtime)
            items = res.body.to_map()['Result']
            return items
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_es_data():
    es_list = []
    es_data = getEs.main(sys.argv[1:])
    for item in es_data:
        es_item = {
            "instance_id": item.get('instanceId'),
            "instance_name": item.get('description'),
            "status": item.get('status'),
            "disk_size": item.get('nodeSpec')['disk'],
            "business": "业务系统",
            "idc": "阿里云",
            "type": "Elasticsearch",
            "cluster": "业务集群",
            "create_time": item.get('createdAt'),
            "charge": "",
            "charge_center": "",
            "description": "",
        }
        es_list.append(es_item)
    return {
        "model": 20,
        "data": es_list
    }


class getMq:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> amqp_open20191212Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'amqp-open.cn-hangzhou.aliyuncs.com'
        return amqp_open20191212Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getMq.create_client()
        list_instances_request = amqp_open_20191212_models.ListInstancesRequest(max_results=200)
        runtime = util_models.RuntimeOptions()
        try:
            res = client.list_instances_with_options(list_instances_request, runtime)
            items = res.body.to_map()['Data']['Instances']
            return items
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_mq_data():
    mq_list = []
    mq_data = getMq.main(sys.argv[1:])
    for item in mq_data:
        mq_item = {
            "instance_id": item.get('InstanceId'),
            "instance_name": item.get('InstanceName'),
            "status": item.get('Status'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": "RabbitMQ",
            "cluster": "业务集群",
            "create_time": datetime.datetime.fromtimestamp(item.get('OrderCreateTime')/1000.0).strftime('%Y-%m-%d %H:%M:%S'),
            "charge": "",
            "charge_center": "",
            "description": "",
        }
        mq_list.append(mq_item)
    return {
        "model": 21,
        "data": mq_list
    }


class getWaf:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> waf_openapi20190910Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'wafopenapi.cn-hangzhou.aliyuncs.com'
        return waf_openapi20190910Client(config)

    @staticmethod
    def main(args: List[str],) -> None:
        client = getWaf.create_client()
        describe_instance_info_request = waf_openapi_20190910_models.DescribeInstanceInfoRequest(region_id='cn-hangzhou')
        runtime = util_models.RuntimeOptions()
        try:
            res = client.describe_instance_info_with_options(describe_instance_info_request, runtime)
            items = res.body.to_map()['InstanceInfo']
            return items
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_waf_data():
    waf_list = []
    waf_data = getWaf.main(sys.argv[1:])
    a = {
            "instance_id": waf_data.get('InstanceId'),
            "instance_name": "阿里云WAF",
            "status": waf_data.get('Status'),
            "business": "业务系统",
            "idc": "阿里云",
            "type": "WAF",
            "cluster": "业务集群",
            "create_time": "2024-06-18 14:45:00",
            "charge": "",
            "charge_center": "",
            "description": "",
        }
    waf_list.append(a)
    return {
        "model": 22,
        "data": waf_list
    }


class getPolardb:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> polardb20170801Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'polardb.aliyuncs.com'
        return polardb20170801Client(config)

    @staticmethod
    def main(
            args: List[str],
    ) -> None:
        client = getPolardb.create_client()
        describe_dbclusters_request = polardb_20170801_models.DescribeDBClustersRequest()
        runtime = util_models.RuntimeOptions()
        try:
            res = client.describe_dbclusters_with_options(describe_dbclusters_request, runtime)
            print(res)
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


def get_polardb_data():
    po_list = []
    po_data = getPolardb.main(sys.argv[1:])
    print(po_data)


# 发送本地CMDB请求
def _send_cmdb_request():
    url = "http://127.0.0.1:8000/api/v1/cmdb/resource"
    # cvm_datas = get_cvm_instance()
    # ecs_datas = get_ecs_data()
    # slb_datas = get_slb_data()
    jwt_token = get_token()
    print(jwt_token)
    # response = requests.post(url, json=ecs_datas, headers={"Authorization": jwt_token})
    # return response.content


if __name__ == '__main__':
    _send_cmdb_request()