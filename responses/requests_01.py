# -*- coding: utf-8 -*-

"""requests.core
~~~~~~~~~~~~~

This module implements the main Requests system.

:copyright: (c) 2011 by Kenneth Reitz.
:license: ISC, see LICENSE for more details.
"""

import urllib

import urllib2

__title__ = 'requests'
__version__ = '0.2.1'
__build__ = 0x000201
__author__ = 'Kenneth Reitz'
__license__ = 'ISC'
__copyright__ = 'Copyright 2011 Kenneth Reitz'


# --- Exception Hierarchy ---

class RequestException(Exception):
    """There was an ambiguous exception that occurred while handling your request."""

class HTTPError(RequestException):
    """An HTTP error occurred."""

class ConnectionError(RequestException):
    """A Connection error occurred."""

class Timeout(RequestException):
    """The request timed out."""

class URLRequired(RequestException):
    """A valid URL is required to make a request."""

class InvalidMethod(RequestException):
    """An inappropriate method was attempted."""

class AuthenticationError(RequestException):
    """The authentication credentials provided were invalid."""


# --- Core Logic ---

AUTOAUTHS = []


class _Request(urllib2.Request):
    """Hidden wrapper around the urllib2.Request object. Allows for manual
    setting of HTTP methods.
    """

    def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None):
       urllib2.Request.__init__( self, url, data, headers, origin_req_host, unverifiable)
       self.method = method

    def get_method(self):
       if self.method:
          return self.method

       return urllib2.Request.get_method(self)


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

    def __repr__(self):
       try:
          repr = '<Request [%s]>' % (self.method)
       except:
          repr = '<Request object>'
       return repr

    def __setattr__(self, name, value):
       if (name == 'method') and (value):
          if value not in self._METHODS:
             raise InvalidMethod("Method %s not supported." % value)

       object.__setattr__(self, name, value)

    def _checks(self):
       """Deterministic checks for consistency."""
       if not self.url:
          raise URLRequired("A URL is required to send a request.")

    def _get_opener(self):
       """Creates appropriate opener object for urllib2."""
       if self.auth:
          authr = urllib2.HTTPPasswordMgrWithDefaultRealm()
          authr.add_password(None, self.url, self.auth.username, self.auth.password)
          handler = urllib2.HTTPBasicAuthHandler(authr)
          opener = urllib2.build_opener(handler)
          return opener.open
       else:
          return urllib2.urlopen

    def send(self, anyway=False):
       """Sends the request. Returns True if successful, False if not."""
       self._checks()
       success = False

       if (not self.sent) or anyway:

           # Prepare URL and Data
           if self.method in ('GET', 'HEAD', 'DELETE'):
               params = urllib.urlencode(self.params) if isinstance(self.params, dict) else self.params
               url = ("%s?%s" % (self.url, params)) if params else self.url
               req = _Request(url, method=self.method)
           else:
               req = _Request(self.url, method=self.method)
               req.data = urllib.urlencode(self.data) if isinstance(self.data, dict) else self.data

           if self.headers:
               req.headers = self.headers

           opener = self._get_opener()

           try:
               resp = opener(req)
               self.response.status_code = resp.code
               self.response.headers = resp.info().dict

               if self.method.lower() not in ('head'):
                   self.response.content = resp.read()

               success = True

           except urllib2.HTTPError, why:
               self.response.status_code = why.code
               # In v1, we might want to raise this, but for now we maintain
               # the v0 behavior of storing the code, while defining the types.
               success = False
           except urllib2.URLError, why:
               raise ConnectionError(why)
           except Exception, why:
               raise RequestException(why)

       self.sent = True if success else False
       return success


class Response(object):
    def __init__(self):
       self.content = None
       self.status_code = None
       self.headers = dict()

    def __repr__(self):
       try:
          repr = '<Response [%s]>' % (self.status_code)
       except:
          repr = '<Response object>'
       return repr


class AuthObject(object):
    def __init__(self, username, password):
       self.username = username
       self.password = password

# --- API Methods ---

def get(url, params={}, headers={}, auth=None):
    r = Request()
    r.method = 'GET'; r.url = url; r.params = params; r.headers = headers
    r.auth = _detect_auth(url, auth)
    r.send()
    return r.response

def head(url, params={}, headers={}, auth=None):
    r = Request()
    r.method = 'HEAD'; r.url = url; r.params = params; r.headers = headers
    r.auth = _detect_auth(url, auth)
    r.send()
    return r.response

def post(url, data={}, headers={}, auth=None):
    r = Request()
    r.method = 'POST'; r.url = url; r.data = data; r.headers = headers
    r.auth = _detect_auth(url, auth)
    r.send()
    return r.response

def put(url, data='', headers={}, auth=None):
    r = Request()
    r.method = 'PUT'; r.url = url; r.data = data; r.headers = headers
    r.auth = _detect_auth(url, auth)
    r.send()
    return r.response

def delete(url, params={}, headers={}, auth=None):
    r = Request()
    r.method = 'DELETE'; r.url = url; r.headers = headers
    r.auth = _detect_auth(url, auth)
    r.send()
    return r.response

# --- Internal Helpers ---

def add_autoauth(url, authobject):
    global AUTOAUTHS
    AUTOAUTHS.append((url, authobject))

def _detect_auth(url, auth):
    return _get_autoauth(url) if not auth else auth

def _get_autoauth(url):
    for (autoauth_url, auth) in AUTOAUTHS:
       if autoauth_url in url:
          return auth
    return None