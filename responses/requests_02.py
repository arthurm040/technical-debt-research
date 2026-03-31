# -*- coding: utf-8 -*-

import urllib
import urllib2


# ... (Previous imports and _Request class remain the same) ...

class Request(object):
    """The :class:`Request` object. It carries out all functionality of
    Requests. Recommended interface is with the Requests functions.
    """

    _METHODS = ('GET', 'HEAD', 'PUT', 'POST', 'DELETE')

    def __init__(self):
        self.url = None
        self.headers = dict()
        self.method = None
        self.params = {}
        self.data = {}
        self.response = Response()
        self.auth = None
        self.sent = False
        self.redirects = 0

    # ... (__repr__, __setattr__, _checks, _get_opener remain the same) ...

    def _prepare(self):
        """Internal method to prepare the urllib2.Request object based on
        the current Request state.
        """
        self._checks()

        url = self.url
        data = None

        # Handle Query Parameters for GET/HEAD/DELETE
        if self.method in ('GET', 'HEAD', 'DELETE'):
            if self.params:
                params = urllib.urlencode(self.params) if isinstance(self.params, dict) else self.params
                url = "%s?%s" % (self.url, params)

        # Handle Body Data for POST/PUT
        elif self.method in ('POST', 'PUT'):
            if isinstance(self.data, dict):
                data = urllib.urlencode(self.data)
            else:
                data = self.data

        req = _Request(url, data=data, method=self.method)

        if self.headers:
            req.headers = self.headers

        return req

    def _handle_redirect(self, resp):
        """Internal method to handle HTTP redirects (e.g. 301, 302)."""
        # Note: Basic implementation logic for future expansion
        # Currently, urllib2 handles basic redirects, but this hook allows
        # for custom cookie/auth persistence during jumps.
        pass

    def send(self, anyway=False):
        """Sends the request using the modularized session methods."""

        if self.sent and not anyway:
            return False

        # 1. Preparation
        req = self._prepare()
        opener = self._get_opener()

        # 2. Execution
        try:
            resp = opener(req)

            # 3. Response Handling
            self.response.status_code = resp.code
            self.response.headers = resp.info().dict

            # Only read content if it's not a HEAD request
            if self.method != 'HEAD':
                self.response.content = resp.read()

            self.sent = True
            return True

        except urllib2.HTTPError, why:
            self.response.status_code = why.code
            self.sent = False
            return False
        except Exception:
            raise RequestException