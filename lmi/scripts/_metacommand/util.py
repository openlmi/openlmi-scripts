# Copyright (c) 2013, Red Hat, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of the FreeBSD Project.
#
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Meta-command utility module.
"""

import logging
import logging.config
import pkg_resources
import re
import sys
import urlparse

from lmi.scripts.common import Configuration
from lmi.scripts.common import get_logger

PYTHON_EGG_NAME = "openlmi-scripts"

RE_NETLOC = re.compile(r'^((?P<username>[^:@]+)(:(?P<password>[^@]+))?@)?'
        r'(?P<hostname>[^:]+)(:(?P<port>\d+))?$')

DEFAULT_LOGGING_CONFIG = {
    'version' : 1,
    'disable_existing_loggers': True,
    'formatters' : {
        'console' : {
            'format': Configuration.default_options()['ConsoleFormat'],
            'datefmt' : '%Y-%m-%d %H:%M:%S'
        },
        'file' : {
            'format' : Configuration.default_options()['FileFormat'],
            'datefmt' : '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers' : {
        'console': {
            'class' : "logging.StreamHandler",
            'level' : logging.ERROR,
            'formatter': 'console',
        },
        'file' : {
            'class' : "logging.FileHandler",
            'level' : Configuration.default_options()['Level'].upper(),
            'formatter': 'file',
        }
    },
    'root' : {
        'level' : logging.DEBUG,
        'handlers' : ['console']
    }
}

LOG = get_logger(__name__)

def setup_logging(app_config, stderr=sys.stderr):
    """
    Setup logging to console and optionally to the file.

    :param app_config: (``lmi.scripts.common.Configuration``)
        Configuration object.
    :param stderr: (``file``) Output stream, where console handler should
        dispatch logging messages.
    """
    cfg = DEFAULT_LOGGING_CONFIG.copy()

    # Set up logging to a file
    if app_config.log_file:
        cfg['handlers']['file']['filename'] = app_config.log_file
        cfg['formatters']['file']['format'] = app_config.get_safe(
                'Log', 'FileFormat', raw=True)
        try:
            cfg['handlers']['file']['level'] = \
                    getattr(logging, app_config.logging_level.upper())
        except KeyError:
            LOG().error('unsupported logging level: "%s"',
                    app_config.logging_level)
        cfg['root']['handlers'].append('file')
    else:
        del cfg['formatters']['file']
        del cfg['handlers']['file']

    if app_config.get_safe('Log', "LogToConsole", bool):
        # Set up logging to console
        if stderr is not sys.stderr:
            cfg['handlers']['console']['stream'] = stderr
        cfg['handlers']['console']['level'] = {
                Configuration.OUTPUT_SILENT  : logging.CRITICAL,
                Configuration.OUTPUT_WARNING : logging.WARNING,
                Configuration.OUTPUT_INFO    : logging.INFO,
                Configuration.OUTPUT_DEBUG   : logging.DEBUG,
            }.get(app_config.verbosity)
        cfg['formatters']['console']['format'] = app_config.get_safe(
                'Log', 'ConsoleFormat', raw=True)
    else:
        del cfg['handlers']['console']
        cfg['root']['handlers'].remove('console')

    logging.config.dictConfig(cfg)

def get_version(egg_name=PYTHON_EGG_NAME):
    """
    Gets version string of any python egg. Defaults to the egg of current
    application.
    """
    return pkg_resources.get_distribution(egg_name).version

def get_hosts_credentials(hostnames):
    """
    Parse list of hostnames, get credentials out of them and return
    ``(hostnames, creds)``, where ``hostnames`` is a list of ``hostnames``
    with credentials removed and ``creds`` is a dictionary with a pair
    ``(username, password)`` for every hostname, that supplied it.

    :param hostnames: (``list``) List of hostnames with optional credentials.
        For example: ``http://root:password@hostname:5988``.
    """
    if not hasattr(hostnames, '__iter__'):
        raise TypeError("hostnames must be a list of hosts")
    new_hostnames = []
    credentials = {}
    for hostname in hostnames:
        parsed = urlparse.urlparse(hostname)
        if not parsed.netloc and parsed.path:
            # got something like [user[:pass]@]hostname[:port] (no scheme)
            match = RE_NETLOC.match(hostname)
            if match:
                hostname = match.group('hostname')
                if match.group('port'):
                    hostname += ':' + match.group('port')
                if match.group('username') or match.group('password'):
                    credentials[hostname] = (
                        match.group('username'), match.group('password'))
        elif parsed.username or parsed.password:
            hostname = parsed.scheme
            if parsed.scheme:
                hostname += "://"
            hostname += parsed.hostname
            if parsed.port:
                hostname += ":" + str(parsed.port)
            hostname += parsed.path
            credentials[hostname] = (parsed.username, parsed.password)
        new_hostnames.append(hostname)
    return (new_hostnames, credentials)

def parse_hosts_file(hosts_file):
    """
    Parse file with hostnames to connect to. Return list of parsed hostnames.

    :param hosts_file: (``file``) File object openned for read.
        It containes hostnames. Each hostname occupies single line.
    :rtype: (``tuple``) A pair of ``(hosts, creds)``, where ``hosts`` is a list
        of string with hostnames and ``creds`` is a dictionary mapping
        ``(username, password)`` to each hostname if supplied.
    """
    hostnames = []
    for line in hosts_file.readlines():
        hostnames.append(line.strip())
    return get_hosts_credentials(hostnames)

