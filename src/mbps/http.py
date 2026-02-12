# Copyright 2012 Matt Martz
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import gzip
import socket
import timeit
from io import BytesIO

from http.client import HTTPConnection, HTTPSConnection
from urllib.request import (
    Request, urlopen, AbstractHTTPHandler, ProxyHandler,
    HTTPDefaultErrorHandler, HTTPRedirectHandler,
    HTTPErrorProcessor, OpenerDirector,
)

from mbps.compat import GZIP_BASE, HTTP_ERRORS, ssl
from mbps.exceptions import SpeedtestHTTPError
from mbps.utils import build_user_agent, printer

_GLOBAL_DEFAULT_TIMEOUT = object()


def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
    """Connect to *address* and return the socket object.

    Convenience function. Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object. Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect. If no *timeout* is supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    is used. If *source_address* is set it must be a tuple of (host, port)
    for the socket to bind as a source address before making the connection.
    A host of '' or port 0 tells the OS to use the default.
    """

    host, port = address
    err = None
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)
            if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(float(timeout))
            if source_address:
                sock.bind(source_address)
            sock.connect(sa)
            return sock

        except socket.error as e:
            err = e
            if sock is not None:
                sock.close()

    if err is not None:
        raise err
    else:
        raise socket.error("getaddrinfo returns an empty list")


class SpeedtestHTTPConnection(HTTPConnection):
    """Custom HTTPConnection to support source_address"""
    def __init__(self, *args, **kwargs):
        source_address = kwargs.pop('source_address', None)
        timeout = kwargs.pop('timeout', 10)

        self._tunnel_host = None

        HTTPConnection.__init__(self, *args, **kwargs)

        self.source_address = source_address
        self.timeout = timeout

    def connect(self):
        """Connect to the host and port specified in __init__."""
        try:
            self.sock = socket.create_connection(
                (self.host, self.port),
                self.timeout,
                self.source_address
            )
        except (AttributeError, TypeError):
            self.sock = create_connection(
                (self.host, self.port),
                self.timeout,
                self.source_address
            )

        if self._tunnel_host:
            self._tunnel()


class SpeedtestHTTPSConnection(HTTPSConnection):
    """Custom HTTPSConnection to support source_address"""
    default_port = 443

    def __init__(self, *args, **kwargs):
        source_address = kwargs.pop('source_address', None)
        timeout = kwargs.pop('timeout', 10)

        self._tunnel_host = None

        HTTPSConnection.__init__(self, *args, **kwargs)

        self.timeout = timeout
        self.source_address = source_address

    def connect(self):
        """Connect to a host on a given (SSL) port."""
        try:
            self.sock = socket.create_connection(
                (self.host, self.port),
                self.timeout,
                self.source_address
            )
        except (AttributeError, TypeError):
            self.sock = create_connection(
                (self.host, self.port),
                self.timeout,
                self.source_address
            )

        if self._tunnel_host:
            self._tunnel()

        if ssl:
            kwargs = {}
            if self._tunnel_host:
                kwargs['server_hostname'] = self._tunnel_host
            else:
                kwargs['server_hostname'] = self.host
            self.sock = self._context.wrap_socket(self.sock, **kwargs)
        else:
            raise SpeedtestHTTPError(
                'This version of Python does not support HTTPS/SSL '
                'functionality'
            )


def _build_connection(connection, source_address, timeout, context=None):
    """Build an ``HTTPConnection`` or ``HTTPSConnection`` with the args
    we need.

    Called from ``http(s)_open`` methods of ``SpeedtestHTTPHandler`` or
    ``SpeedtestHTTPSHandler``
    """
    def inner(host, **kwargs):
        kwargs.update({
            'source_address': source_address,
            'timeout': timeout
        })
        if context:
            kwargs['context'] = context
        return connection(host, **kwargs)
    return inner


class SpeedtestHTTPHandler(AbstractHTTPHandler):
    """Custom ``HTTPHandler`` that can build a ``HTTPConnection`` with the
    args we need for ``source_address`` and ``timeout``
    """
    def __init__(self, debuglevel=0, source_address=None, timeout=10):
        AbstractHTTPHandler.__init__(self, debuglevel)
        self.source_address = source_address
        self.timeout = timeout

    def http_open(self, req):
        return self.do_open(
            _build_connection(
                SpeedtestHTTPConnection,
                self.source_address,
                self.timeout
            ),
            req
        )

    http_request = AbstractHTTPHandler.do_request_


class SpeedtestHTTPSHandler(AbstractHTTPHandler):
    """Custom ``HTTPSHandler`` that can build a ``HTTPSConnection`` with the
    args we need for ``source_address`` and ``timeout``
    """
    def __init__(self, debuglevel=0, context=None, source_address=None,
                 timeout=10):
        AbstractHTTPHandler.__init__(self, debuglevel)
        self._context = context
        self.source_address = source_address
        self.timeout = timeout

    def https_open(self, req):
        return self.do_open(
            _build_connection(
                SpeedtestHTTPSConnection,
                self.source_address,
                self.timeout,
                context=self._context,
            ),
            req
        )

    https_request = AbstractHTTPHandler.do_request_


def build_opener(source_address=None, timeout=10):
    """Build an ``OpenerDirector`` with the explicit handlers we want,
    ``source_address`` for binding, ``timeout`` and our custom `User-Agent`
    """

    printer('Timeout set to %d' % timeout, debug=True)

    if source_address:
        source_address_tuple = (source_address, 0)
        printer('Binding to source address: %r' % (source_address_tuple,),
                debug=True)
    else:
        source_address_tuple = None

    handlers = [
        ProxyHandler(),
        SpeedtestHTTPHandler(source_address=source_address_tuple,
                             timeout=timeout),
        SpeedtestHTTPSHandler(source_address=source_address_tuple,
                              timeout=timeout),
        HTTPDefaultErrorHandler(),
        HTTPRedirectHandler(),
        HTTPErrorProcessor()
    ]

    opener = OpenerDirector()
    opener.addheaders = [('User-agent', build_user_agent())]

    for handler in handlers:
        opener.add_handler(handler)

    return opener


def build_request(url, data=None, headers=None, bump='0', secure=False):
    """Build a urllib request object

    This function automatically adds a User-Agent header to all requests
    """

    if not headers:
        headers = {}

    if url[0] == ':':
        scheme = ('http', 'https')[bool(secure)]
        schemed_url = '%s%s' % (scheme, url)
    else:
        schemed_url = url

    if '?' in url:
        delim = '&'
    else:
        delim = '?'

    # Cache busting
    final_url = '%s%sx=%s.%s' % (schemed_url, delim,
                                 int(timeit.time.time() * 1000),
                                 bump)

    headers.update({
        'Cache-Control': 'no-cache',
    })

    printer('%s %s' % (('GET', 'POST')[bool(data)], final_url),
            debug=True)

    return Request(final_url, data=data, headers=headers)


def catch_request(request, opener=None):
    """Helper function to catch common exceptions encountered when
    establishing a connection with a HTTP/HTTPS request
    """

    if opener:
        _open = opener.open
    else:
        _open = urlopen

    try:
        uh = _open(request)
        if request.get_full_url() != uh.geturl():
            printer('Redirected to %s' % uh.geturl(), debug=True)
        return uh, False
    except HTTP_ERRORS as e:
        return None, e


def get_response_stream(response):
    """Helper function to return either a Gzip reader if
    ``Content-Encoding`` is ``gzip`` otherwise the response itself
    """

    if response.getheader('content-encoding') == 'gzip':
        return GzipDecodedResponse(response)

    return response


class GzipDecodedResponse(GZIP_BASE):
    """A file-like object to decode a response encoded with the gzip
    method, as described in RFC 1952.

    Largely copied from ``xmlrpclib``/``xmlrpc.client`` and modified
    to work for py3
    """
    def __init__(self, response):
        if not gzip:
            raise SpeedtestHTTPError('HTTP response body is gzip encoded, '
                                     'but gzip support is not available')
        self.io = BytesIO()
        while True:
            chunk = response.read(1024)
            if len(chunk) == 0:
                break
            self.io.write(chunk)
        self.io.seek(0)
        gzip.GzipFile.__init__(self, mode='rb', fileobj=self.io)

    def close(self):
        try:
            gzip.GzipFile.close(self)
        finally:
            self.io.close()
