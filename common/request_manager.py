
from oslo_utils import importutils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

request_maps = {
    'rest': 'common.utils.request_tools.CustomRestRequest',
    'ssh': 'common.utils.request_tools.SSHRequest',
}


class RequestManager(object):

    def __init__(self):
        self.request_tools = {}
        self.init_manager()

    def init_manager(self):
        for key, value in request_maps.items():
            if key not in self.request_tools.keys():
                request_obj = importutils.import_class(request_maps.get(key))
                self.request_tools.update({
                    request_obj.get_request_type(): request_obj()
                })
        print self.request_tools
        LOG.info("Request tools mappings is >>> %s", self.request_tools)

    def send_request_to_device(self, device, **kwargs):
        request_type = kwargs.pop("request_type", "rest")
        aster_req = self.request_tools.get(request_type)
        return aster_req.send_request_to_device(device, **kwargs) if aster_req else (-1, None)
