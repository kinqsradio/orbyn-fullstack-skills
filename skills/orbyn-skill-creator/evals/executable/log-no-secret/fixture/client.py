"""A tiny API client."""
import logging

log = logging.getLogger('client')


class Client:
    def __init__(self, host, token, timeout=5):
        self.host = host
        self.token = token
        self.timeout = timeout

    def headers(self):
        return {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/json'}

    def connect(self):
        return {'host': self.host, 'timeout': self.timeout, 'connected': True}
