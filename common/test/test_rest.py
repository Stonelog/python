#!/usr/bin/python
# coding:utf-8
import os
import json

from common.rsa_util.crypto import encrypt
from common import request_manager

os.environ['OSLO_LOCK_PATH'] = "/root/lock"

auth_info = {
    "rest": {
        "username": "",
        "password": "",
        "port": 443,
        "schema": "https"
    },
    "ssh": {
        "username": "root",
        "password": "1",
        "port": 22
    }
}
auth_info_str = encrypt(json.dumps(auth_info))

request_manager = request_manager.RequestManager()
device = {
    "ip_address": "www.baidu.com",
    # "ip_address": "192.168.0.150",
    "auth_info": auth_info_str,
}

# kwargs = {
#     "request_type": "ssh",
#     "cmd": "ls -l /home/"
# }

# kwargs = {
#     "request_type": "rest",
#     "method": "GET",
#     "uri": "/rest/v1/system/subsystems",
#     "headers": {
#         "content-type": "application/json"
#     },
#     "data": None,
#     "json": None,
#     "params": {
#         'depth': 1, 'selector': 'status'
#     },
#     "timeout": 10,
#     # "authorized_retries": 3,
#     # "connect_retries": 3,
#     # "connect_retry_delay": 0.5
# }
# kwargs = {
#     "request_type": "rest",
#     "method": "POST",
#     "uri": "/rest/v1/login",
#     "headers": {
#         "content-type": "application/x-www-form-urlencoded"
#     },
#     "data": {
#         "username": "admin",
#         "password": "passok"
#     },
#     "json": None,
#     "params": None
# }
# kwargs = {
#     "request_type": "rest",
#     "method": "POST",
#     "uri": "/login",
#     "headers": {
#         "content-type": "application/json"
#     },
#     "data": None,
#     "json": {
#         "username": "admin",
#         "password": "passok"
#     },
#     "params": None
# }

kwargs = {
    "request_type": "rest",
    "method": "GET",
    "uri": "/",
    "headers": {
        "content-type": "application/json"
    }
}

code, ret = request_manager.send_request_to_device(device, **kwargs)
print code, ret
