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

import math
import platform
import sys

from speedtest_cli import __version__

DEBUG = False


class FakeShutdownEvent:
    """Class to fake a threading.Event.isSet so that users of this module
    are not required to register their own threading.Event()
    """

    @staticmethod
    def isSet():
        "Dummy method to always return false"
        return False

    is_set = isSet


def event_is_set(event):
    return event.is_set()


def distance(origin, destination):
    """Determine distance between 2 sets of [lat,lon] in km"""

    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) * math.sin(dlon / 2) *
         math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def build_user_agent():
    """Build a Mozilla/5.0 compatible User-Agent string"""

    ua_tuple = (
        'Mozilla/5.0',
        '(%s; U; %s; en-us)' % (platform.platform(),
                                platform.architecture()[0]),
        'Python/%s' % platform.python_version(),
        '(KHTML, like Gecko)',
        'speedtest-cli/%s' % __version__
    )
    user_agent = ' '.join(ua_tuple)
    printer('User-Agent: %s' % user_agent, debug=True)
    return user_agent


def printer(string, quiet=False, debug=False, error=False, **kwargs):
    """Helper function to print a string with various features"""

    if debug and not DEBUG:
        return

    if debug:
        if sys.stdout.isatty():
            out = '\033[1;30mDEBUG: %s\033[0m' % string
        else:
            out = 'DEBUG: %s' % string
    else:
        out = string

    if error:
        kwargs['file'] = sys.stderr

    if not quiet:
        print(out, **kwargs)


def print_dots(shutdown_event):
    """Built in callback function used by Thread classes for printing
    status
    """
    def inner(current, total, start=False, end=False):
        if event_is_set(shutdown_event):
            return

        sys.stdout.write('.')
        if current + 1 == total and end is True:
            sys.stdout.write('\n')
        sys.stdout.flush()
    return inner


def do_nothing(*args, **kwargs):
    pass
