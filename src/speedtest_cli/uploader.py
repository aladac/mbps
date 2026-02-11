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

import threading
import timeit
from io import BytesIO

from urllib.request import urlopen

from speedtest_cli.compat import HTTP_ERRORS
from speedtest_cli.exceptions import SpeedtestCLIError, SpeedtestUploadTimeout
from speedtest_cli.http import build_request
from speedtest_cli.utils import FakeShutdownEvent, event_is_set


class HTTPUploaderData:
    """File-like object to improve cutting off the upload once the timeout
    has been reached
    """

    def __init__(self, length, start, timeout, shutdown_event=None):
        self.length = length
        self.start = start
        self.timeout = timeout

        if shutdown_event:
            self._shutdown_event = shutdown_event
        else:
            self._shutdown_event = FakeShutdownEvent()

        self._data = None

        self.total = [0]

    def pre_allocate(self):
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        multiplier = int(round(int(self.length) / 36.0))
        try:
            self._data = BytesIO(
                ('content1=%s' %
                 (chars * multiplier)[0:int(self.length) - 9]
                 ).encode()
            )
        except MemoryError:
            raise SpeedtestCLIError(
                'Insufficient memory to pre-allocate upload data. Please '
                'use --no-pre-allocate'
            )

    @property
    def data(self):
        if not self._data:
            self.pre_allocate()
        return self._data

    def read(self, n=10240):
        if ((timeit.default_timer() - self.start) <= self.timeout and
                not event_is_set(self._shutdown_event)):
            chunk = self.data.read(n)
            self.total.append(len(chunk))
            return chunk
        else:
            raise SpeedtestUploadTimeout()

    def __len__(self):
        return self.length


class HTTPUploader(threading.Thread):
    """Thread class for putting a URL"""

    def __init__(self, i, request, start, size, timeout, opener=None,
                 shutdown_event=None):
        threading.Thread.__init__(self)
        self.request = request
        self.request.data.start = self.starttime = start
        self.size = size
        self.result = 0
        self.timeout = timeout
        self.i = i

        if opener:
            self._opener = opener.open
        else:
            self._opener = urlopen

        if shutdown_event:
            self._shutdown_event = shutdown_event
        else:
            self._shutdown_event = FakeShutdownEvent()

    def run(self):
        request = self.request
        try:
            if ((timeit.default_timer() - self.starttime) <= self.timeout and
                    not event_is_set(self._shutdown_event)):
                try:
                    f = self._opener(request)
                except TypeError:
                    request = build_request(self.request.get_full_url(),
                                            data=request.data.read(self.size))
                    f = self._opener(request)
                f.read(11)
                f.close()
                self.result = sum(self.request.data.total)
            else:
                self.result = 0
        except (IOError, SpeedtestUploadTimeout):
            self.result = sum(self.request.data.total)
        except HTTP_ERRORS:
            self.result = 0
