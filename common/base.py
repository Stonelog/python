import json

from rsa_util.crypto import decrypt


class RequestBase(object):

    def __init__(self):
        pass

    @staticmethod
    def get_request_type():
        """Get request type."""
        raise NotImplementedError()

    def send_request_to_device(self, device, **kwargs):
        """Send request to device."""
        raise NotImplementedError()

    @staticmethod
    def get_auth_info(auth_info_str):
        """ Decryption manage_conf_info_str, Format is as follows
           {
             "rest": {"username": "", "password": "", "port": 443, "schema": "https"},
             "ssh": {"username": "", "password": "", "port": 22}
           }
        :param auth_info_str: Encrypted string
        :return: dict
        """
        return json.loads(decrypt(auth_info_str)) if auth_info_str else {}
