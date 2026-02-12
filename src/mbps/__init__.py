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

__version__ = '2.1.4b1'

# Lazy imports to avoid circular dependency issues at module load time.
# The public API is available via __all__ and will be resolved on attribute access.


def __getattr__(name):
    if name == 'Speedtest':
        from mbps.core import Speedtest
        return Speedtest
    if name == 'SpeedtestResults':
        from mbps.results import SpeedtestResults
        return SpeedtestResults

    _exceptions = {
        'SpeedtestException',
        'SpeedtestCLIError',
        'SpeedtestHTTPError',
        'SpeedtestConfigError',
        'SpeedtestServersError',
        'ConfigRetrievalError',
        'ServersRetrievalError',
        'InvalidServerIDType',
        'NoMatchedServers',
        'SpeedtestMiniConnectFailure',
        'InvalidSpeedtestMiniServer',
        'ShareResultsConnectFailure',
        'ShareResultsSubmitFailure',
        'SpeedtestUploadTimeout',
        'SpeedtestBestServerFailure',
        'SpeedtestMissingBestServer',
    }
    if name in _exceptions:
        from mbps import exceptions
        return getattr(exceptions, name)

    raise AttributeError(f"module 'mbps' has no attribute {name!r}")


__all__ = [
    '__version__',
    'Speedtest',
    'SpeedtestResults',
    'SpeedtestException',
    'SpeedtestCLIError',
    'SpeedtestHTTPError',
    'SpeedtestConfigError',
    'SpeedtestServersError',
    'ConfigRetrievalError',
    'ServersRetrievalError',
    'InvalidServerIDType',
    'NoMatchedServers',
    'SpeedtestMiniConnectFailure',
    'InvalidSpeedtestMiniServer',
    'ShareResultsConnectFailure',
    'ShareResultsSubmitFailure',
    'SpeedtestUploadTimeout',
    'SpeedtestBestServerFailure',
    'SpeedtestMissingBestServer',
]
