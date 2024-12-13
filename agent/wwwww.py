import requests
import json

def get_token():
    url = "https://172.16.15.147:55000/security/user/authenticate"
    auth = ('wazuh-wui', 'MyS3cr37P450r.*-')
    res=requests.post(url, auth = auth,verify=False)
    token=res.json()["data"]["token"]
    return token
def get_package_info():
    #url = "https://172.16.15.147:55000/experimental/syscollector/packages?limit=1000&wait_for_complete=true"
    #url = "https://172.16.15.147:55000/experimental/syscollector/packages?search=jenkins"
    #url = "https://172.16.15.147:55000/experimental/syscollector/netaddr"
    url = "https://172.16.15.147:55000/experimental/syscollector/ports?limit=1000&wait_for_complete=true"
    #url = "https://172.16.15.147:55000/experimental/syscollector/processes?limit=1000&wait_for_complete=true"
    # url = "https://172.16.15.147:55000/experimental/syscollector/processes?search=wazuh"
    #url = "https://172.16.15.147:55000/agents"
    #url = "https://172.16.15.147:55000/syscollector/001/hardware?wait_for_complete=true"
    token=get_token()
    headers = {'Authorization': 'Bearer ' + token}
    res=requests.get(url,headers=headers,verify=False)
    #res.json保存到wwwwww.json
    with open("wwwwww222.json", "w", encoding="utf-8") as f:
        json.dump(res.json(), f, ensure_ascii=False, indent=4)
    # with open("res.json", "w", encoding="utf-8") as f:
    #     json.dump(res.json(), f, ensure_ascii=False, indent=4)
    print("=================",json.dumps(res.json(),indent=4))


get_package_info()