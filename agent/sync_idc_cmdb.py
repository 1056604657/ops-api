import os
try:
  import psutil
except ModuleNotFoundError:
  os.system('pip3 install psutil')

import subprocess
import psutil
import socket
import datetime
import requests


def exec_cmd(cmd):
    result = subprocess.Popen(args=cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = result.communicate()
    stdout = stdout.decode().replace('\n', '').strip()
    if result.returncode == 0:
        return stdout
    else:
        return stderr


def bytes_to_Gb(bytes):
    gb = bytes / (1024 * 1024 * 1024)
    return gb


def getSn():
    server_sn = exec_cmd("dmidecode -t system | grep -i 'Serial Number'|awk -F ':' '{print $2}'")
    if server_sn == None:
        server_sn = exec_cmd("dmidecode -t system | grep -i 'UUID'|awk -F ':' '{print $2}'")
    return server_sn


def SystemInfo():
    name = socket.gethostname()
    cpu = psutil.cpu_count()
    memory = str(bytes_to_Gb(psutil.virtual_memory().total)).split('.')[0]
    disk = str(bytes_to_Gb(psutil.disk_usage('/')[0])).split('.')[0]
    ip = exec_cmd("ip a show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")
    data = {
        "serverId": getSn(),
        "serverName": name,
        "softSystem": name,
        "softEnvironment": "生产环境",
        "idc": '本地机房',
        "region": '杭州',
        "serverType": '服务器',
        "affiliatedCluster": '业务集群',
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "private_ip": ip,
        "public_ip": '暂未使用',
        "status": 'running',
        "create_time": str(datetime.datetime.now()).split('.')[-2:][0],
    }
    return data


def idc_cmdb_info():
    name = socket.gethostname()
    cpu = psutil.cpu_count()
    memory = str(bytes_to_Gb(psutil.virtual_memory().total)).split('.')[0]
    disk = str(bytes_to_Gb(psutil.disk_usage('/')[0])).split('.')[0]
    ip = exec_cmd("ip a show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")
    data = {
        "server_id": getSn(),
        "server_name": name,
        "idc": '本地机房',
        "type": '本地机房',
        "cluster": '业务集群',
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "private_ip": ip,
        "public_ip": '',
        "status": 'running',
        "create_time": str(datetime.datetime.now()).split('.')[-2:][0],
        "charge": '',
        "charge_email": '',
        "description": ''
    }
    return {
        "model": 12,
        "data": data
    }


def get_pro_token():
    url = "http://127.0.0.1:8000/get-jwt-token"
    body = {
        "username": "admin",
        "password": "admin"
    }
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=body)
    res = 'JWT ' + eval(response.content.decode())['data']
    return res


def _send_procmdb_request():
    url = "http://127.0.0.1:8000/api/v1/cmdb/resource?model=12"
    jwt_token = get_pro_token()
    result = idc_cmdb_info()
    print(result)
    response = requests.post(url, json=result, headers={"Authorization": jwt_token})
    print(response.content)
    return response.content


if __name__ == '__main__':
    _send_procmdb_request()