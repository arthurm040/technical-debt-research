# -*- coding: utf-8 -*-

"""
    requests.core
    ~~~~~~~~~~~~~
    This module implements the main Requests system.
"""

import urllib
import urllib2
import Cookielib

__title__ = 'requests'
__version__ = '0.2.1'
__author__ = 'Kenneth Reitz'
__license__ = 'ISC'
__copyright__ = 'Copyright 2011 Kenneth Reitz'


class Request(object):
    """The :class:`Request` object."""

    _METHODS = ('GET', 'HEAD', 'PUT', 'POST', 'DELETE')

    def __init__(self):
        self.url = None
        self.headers = dict()
        self.method = None
        self.params = {}
        self.data = {}
        self.response = None
        self.auth = None
        self.sent = False

    def _get_opener(self):
        if self.auth:
            authr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            authr.add_password(None, self.url, self.auth.username, self.auth.password)
            handler = urllib2.HTTPBasicAuthHandler(authr)
            return urllib2.build_opener(handler).open
        else:
            return urllib2.urlopen

    def send(self, anyway=False):
        """Sends the request and populates the Response object."""
        if self.sent and not anyway:
            return False

        # Prepare URL/Params
        url = self.url
        if self.params:
            url = "%s?%s" % (url, urllib.urlencode(self.params))

        # Build the urllib2 Request
        req = _Request(url, method=self.method)
        if self.headers:
            req.headers = self.headers

        if self.method in ('POST', 'PUT'):
            req.data = urllib.urlencode(self.data) if isinstance(self.data, dict) else self.data

        opener = self._get_opener()

        try:
            resp = opener(req)
            # Logic to build the v1 Response object
            self.response = Response()
            self.response.status_code = resp.code
            self.response.headers = resp.info().dict
            self.response.url = resp.geturl()
            self.response.reason = resp.msg
            self.response.raw = resp  # The underlying socket-like object

            if self.method != 'HEAD':
                self.response.content = resp.read()

            self.sent = True
            return True

        except urllib2.HTTPError, why:
            self.response = Response()
            self.response.status_code = why.code
            return False


class Response(object):
    """The :class:`Response` object.
    V1: Added support for raw, encoding, url, history, cookies, and reason.
    """

    def __init__(self):
        self.content = None
        self.status_code = None
        self.headers = dict()

        # v1 Requirements
        self.raw = None
        self.encoding = None
        self.url = None
        self.history = []
        self.reason = None
        self.cookies = {}

    def __repr__(self):
        return '<Response [%s]>' % (self.status_code) if self.status_code else '<Response object>'


class _Request(urllib2.Request):
    def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None):
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)
        self.method = method

    def get_method(self):
        return self.method if self.method else urllib2.Request.get_method(self)


# --- API Methods ---

def get(url, params={}, headers={}, auth=None):
    r = Request()
    r.method = 'GET';
    r.url = url;
    r.params = params;
    r.headers = headers;
    r.auth = auth
    r.send()
    return r.response


def post(url, data={}, headers={}, auth=None):
    r = Request()
    r.method = 'POST';
    r.url = url;
    r.data = data;
    r.headers = headers;
    r.auth = auth
    r.send()
    return r.response

# (Other methods like head, put, delete follow the same pattern)