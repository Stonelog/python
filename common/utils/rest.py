import time
import socket
import requests
import urllib3

from oslo_log import log as logging

urllib3.disable_warnings()
LOG = logging.getLogger(__name__)

REQUESTS_VERSION = tuple(int(v) for v in requests.__version__.split('.'))


class TCPKeepAliveAdapter(requests.adapters.HTTPAdapter):
    """The custom adapter used to set TCP Keep-Alive on all connections.

    This Adapter also preserves the default behaviour of Requests which
    disables Nagle's Algorithm. See also:
    https://blogs.msdn.com/b/windowsazurestorage/archive/2010/06/25/nagle-s-algorithm-is-not-friendly-towards-small-requests.aspx
    """

    def init_poolmanager(self, *args, **kwargs):

        try:
            with open('/proc/version', 'r') as f:
                is_windows_linux_subsystem = 'microsoft' in f.read().lower()
        except IOError:
            is_windows_linux_subsystem = False

        if 'socket_options' not in kwargs and REQUESTS_VERSION >= (2, 4, 1):
            socket_options = [
                # Keep Nagle's algorithm off
                (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
                # Turn on TCP Keep-Alive
                (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            ]

            # Some operating systems (e.g., OSX) do not support setting
            # keepidle
            if hasattr(socket, 'TCP_KEEPIDLE'):
                socket_options += [
                    # Wait 60 seconds before sending keep-alive probes
                    (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                ]

            # Windows subsystem for Linux does not support this feature
            if (hasattr(socket, 'TCP_KEEPCNT') and
                    not is_windows_linux_subsystem):
                socket_options += [
                    # Set the maximum number of keep-alive probes
                    (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4),
                ]

            if hasattr(socket, 'TCP_KEEPINTVL'):
                socket_options += [
                    # Send keep-alive probes every 15 seconds
                    (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15),
                ]

            # After waiting 60 seconds, and then sending a probe once every 15
            # seconds 4 times, these options should ensure that a connection
            # hands for no longer than 2 minutes before a ConnectionError is
            # raised.
            kwargs['socket_options'] = socket_options
        super(TCPKeepAliveAdapter, self).init_poolmanager(*args, **kwargs)


def _construct_session(session_obj=None):
    # NOTE(morganfainberg): if the logic in this function changes be sure to
    # update the betamax fixture's '_construct_session_with_betamax" function
    # as well.
    if not session_obj:
        session_obj = requests.Session()
        # Use TCPKeepAliveAdapter to fix bug 1323862
        for scheme in list(session_obj.adapters):
            session_obj.mount(scheme, TCPKeepAliveAdapter())
    return session_obj


class RestRequest(object):

    def __init__(self):
        self.session = _construct_session()
        self.detect_port_is_open_timeout = 3

    def _send_request(self, method, url, connect_retries=3, connect_retry_delay=0.5, **kwargs):
        # NOTE(jamie len nox): We handle redirection manually because the
        # requests lib follows some browser patterns where it will redirect
        # POSTs as GETs for certain statuses which is not want we want for an
        # API. See: https://en.wikipedia.org/wiki/Post/Redirect/Get

        # NOTE(jamie len nox): The interaction between retries and redirects are
        # handled naively. We will attempt only a maximum number of retries and
        # redirects rather than per request limits. Otherwise the extreme case
        # could be redirects * retries requests. This will be sufficient in
        # most cases and can be fixed properly if there's ever a need.
        try:
            try:
                with self.session.request(method, url, **kwargs) as resp:
                    # Clean up the last request cookie
                    self.session.cookies.clear()
                    return resp
            except requests.exceptions.SSLError as e:
                msg = 'SSL exception connecting to %(url)s: %(error)s' % {
                    'url': url, 'error': e}
                LOG.info(msg)
            except requests.exceptions.Timeout as e:
                raise e
            except requests.exceptions.ConnectionError as e:
                # NOTE(sda gue): urllib3/requests connection error is a
                # translation of SocketError. However, SocketError
                # happens for many different reasons, and that low
                # level message is often really important in figuring
                # out the difference between network mis configurations
                # and firewall blocking.
                raise e
            except requests.exceptions.RequestException as e:
                raise e
        except requests.exceptions.Timeout as e:
            if connect_retries <= 0:
                return
            LOG.info('Failure: %(e)s. Retrying in %(delay).1fs.', {
                'e': e, 'delay': connect_retry_delay})
            time.sleep(connect_retry_delay)
            kwargs.update({
                "timeout": kwargs.get("timeout", 5) + 5
            })
            return self._send_request(
                method, url,
                connect_retries=connect_retries - 1,
                connect_retry_delay=connect_retry_delay * 2,
                **kwargs)

    def send_request(self, method, ip, port, uri, schema="https", **kwargs):
        """
        :param method:
        :param ip:
        :param port:
        :param uri:
        :param schema:
        :param kwargs:
        :return: None or resp
        """
        # Detect if the IP and port are open
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.settimeout(self.detect_port_is_open_timeout)
            sk.connect((ip, int(port)))
            sk.close()
        except BaseException as e:
            LOG.info("Aster Request, Port not open. [{}:{}] error: {}".format(ip, port, e))
            return
        start = time.time()
        if uri and not uri.startswith("/"):
            uri = "/{}".format(uri)
        url = "{}://{}:{}{}".format(schema, ip, port, uri)
        msg = "Aster request [ {} {} kwargs: {} ]".format(method, url, kwargs)

        try:
            # Send HTTP or HTTPS request
            resp = self._send_request(
                method, url,
                **kwargs
            )
            finish = time.time()
            if resp is None:
                msg = "{} reason: Response is None time: {:.6f} sec".format(msg, finish - start)
                LOG.error(msg)
                return
            status_code = getattr(resp, "status_code", None)
            msg = "{} status: {}  time: {:.6f} sec".format(msg, status_code, finish - start)
            if status_code and requests.codes.ok <= status_code < requests.codes.bad:
                LOG.info(msg)
            else:
                msg = "{} reason: {}".format(msg, resp.text)
                LOG.info(msg)
            return resp
        except BaseException as e:
            msg = "Request failure. {} reason: {}".format(msg, e)
            LOG.error(msg)
