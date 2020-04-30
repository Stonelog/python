import copy

from requests import codes
from oslo_log import log as logging

from rest import RestRequest
from exceptions import exceptions
from ssh import Client as SSHClient
from common import base
from common.cache_util import cookies_mapping

LOGIN_REQUEST_LIST = [{
    "url": "/login",
    "method": "POST",
    "headers": {
        "content-type": "application/json"
    },
    "result": [201]
}, {
    "url": "/v1/login",
    "method": "POST",
    "headers": {
        "content-type": "application/x-www-form-urlencoded"
    },
    "result": [200]

}]


LOG = logging.getLogger(__name__)


class CustomRestRequest(base.RequestBase):

    def __init__(self):
        super(CustomRestRequest, self).__init__()
        self.rest_request = RestRequest()

    @staticmethod
    def get_request_type():
        return "rest"

    def get_login_cookies(self, device):
        """ Get rest request cookies
        :param device:
        :return: response or None
        """
        base_info = self.get_auth_info(device.get("auth_info")).get("rest")
        ip = device.get("ip_address")
        port = base_info.get("port", 443)
        schema = base_info.get("schema", "https")
        username = base_info.get("username")
        password = base_info.get("password")
        if not username or not password:
            return

        # Add send request cookies
        body = {
            "username": username,
            "password": password
        }

        login_requests = LOGIN_REQUEST_LIST
        for login_req in login_requests:
            method = login_req.get("method")
            uri = login_req.get("url")
            kwargs = {
                "verify": False,
                "headers": login_req.get("headers")
            }
            if kwargs["headers"].get("content-type") == "application/json":
                kwargs.update({"json": body})
            else:
                kwargs.update({"data": body})
            login_resp = self.rest_request.send_request(
                method,
                ip, port,
                uri,
                schema=schema,
                **kwargs
            )
            status_code = getattr(login_resp, "status_code", None)
            if status_code in login_req["result"]:
                return login_resp

    def send_request_to_device(self, device, authorized_retries=3, **kwargs):
        """  The parameters to send the request are ready and the request will be sent
        :param device:
        :param authorized_retries:
        :param kwargs:
        :return: (status_code, response) or (-1, None)
        """
        LOG.debug("Send rest request, authorized_retries is %s, kwargs is >>> %s", authorized_retries, kwargs)
        # kwargs = {
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
        #     "params": None,
        #     "timeout": 5
        # }
        base_info = self.get_auth_info(device.get("auth_info")).get("rest")
        ip = device.get("ip_address")
        port = base_info.get("port", 443)
        schema = base_info.get("schema", "https")

        print cookies_mapping.get_cookies()

        # Cache cookies during login
        if ip not in cookies_mapping.get_cookies().keys():
            login_resp = self.get_login_cookies(device)
            if login_resp is not None:
                cookies_mapping.add_cookie(ip, login_resp.cookies)
        _kwargs = copy.deepcopy(kwargs)

        # Send the rest request
        response = self.rest_request.send_request(
            kwargs.pop("method", ""),
            ip, port,
            kwargs.pop("uri", "/"),
            schema=schema,
            verify=False,
            cookies=cookies_mapping.get_cookie(ip),
            **kwargs
        )
        if response is None:
            return -1, None

        status_code = getattr(response, "status_code", None)
        if status_code in [codes.unauthorized]:
            if authorized_retries <= 0:
                return -1, None
            # Cache cookies during login
            login_resp = self.get_login_cookies(device)
            if login_resp is not None:
                cookies_mapping.add_cookie(ip, login_resp.cookies)
            return self.send_request_to_device(device, authorized_retries=authorized_retries - 1, **_kwargs)
        return status_code, response


class SSHRequest(base.RequestBase):

    def __init__(self):
        super(SSHRequest, self).__init__()

    @staticmethod
    def get_request_type():
        return "ssh"

    def send_request_to_device(self, device, **kwargs):
        """ The parameters to send the ssh request are ready and the request will be sent
        :param device:
        :param kwargs:
        :return: (status_code, ret) or (-1, None)
        """
        LOG.debug("Send ssh request, kwargs is >>> %s", kwargs)
        # kwargs = {
        #     "cmd": "ls -l /opt/"
        # }
        base_info = self.get_auth_info(device.get("auth_info")).get("ssh")
        ip = device.get("ip_address")
        ssh_username = base_info.get("username")
        ssh_pwd = base_info.get("password")
        ssh_port = base_info.get("port", 22)
        timeout = kwargs.pop("timeout", 5)

        ssh_client = SSHClient(
            ip,
            ssh_username,
            password=ssh_pwd,
            timeout=timeout,
            port=ssh_port
        )
        try:
            ssh_cmd = kwargs.get("cmd")
            LOG.info("Send ssh request, cmd is >>> %s", ssh_cmd)
            ret = ssh_client.exec_command(ssh_cmd)
            return 200, ret
        except (exceptions.SSHExecCommandFailed, exceptions.SSHTimeout) as e:
            LOG.error("Send ssh request failed, reason >>> %s", e)
        return -1, None
