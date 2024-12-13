import json
import requests

def get_token():
    url = "http://127.0.0.1:8000/get-jwt-token"
    body = {
        "username": "admin",
        "password": "admin"
    }
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=body)
        response.raise_for_status() 
        data = json.loads(response.text)
        token = data.get('data')
        if not token:
            raise ValueError("response中没有data")
        res = f'JWT {token}'
        print(res)
        return res
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except (json.JSONDecodeError, ValueError) as e:
        print(f"处理响应时出错: {e}")
        return None


def send_request():
    url = "http://127.0.0.1:8000/api/v1/cmdb/host-service"
    jwt_token = get_token()
    json = {
        "host_ip": "00534324",
        "host_name": "app-server-1222213124123",
        "service_command": [{'port': '23', 'pid': '9383', 'command': '/usr/sbin/sshd -D'},
                             {'port': '80', 'pid': '12766', 'command': '/usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 80 -container-ip 172.21.0.4 -container-port 80'}
                             ]
  }
    headers = {"Authorization": jwt_token}
    print(f"=====Sending {requests.Request('POST', url, json=json, headers=headers).prepare().method} request to {url}")
    print(f"=====Headers: {headers}")
    print(f"=====Data: {json}")
    response = requests.post(url, json=json, headers=headers)
    print(response)

get_token()
#send_request()
