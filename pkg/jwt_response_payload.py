

def jwt_response_payload(token, user=None, request=None):
    return {
        'code': 200,
        'messgae': '成功',
        'data': token
    }