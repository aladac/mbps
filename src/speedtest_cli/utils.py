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

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn

from speedtest_cli import __version__

DEBUG = False

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)


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

    if not quiet:
        if debug:
            err_console.print(f"[dim]DEBUG: {string}[/dim]", **kwargs)
        elif error:
            err_console.print(string, **kwargs)
        else:
            print(string, **kwargs)


def make_rich_callback(shutdown_event, label=""):
    """Create a rich Progress bar and callback for download/upload progress.

    Returns (progress, callback) tuple. Caller must use progress as a
    context manager.
    """
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
        console=console,
    )
    task_id = progress.add_task(label, total=None)

    def callback(current, total, start=False, end=False):
        if event_is_set(shutdown_event):
            return
        if start and progress.tasks[task_id].total is None:
            progress.update(task_id, total=total)
        if end:
            progress.advance(task_id)

    return progress, callback


def print_dots(shutdown_event):
    """Built in callback function used by Thread classes for printing
    status — kept for backwards compatibility.
    """
    import sys

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
