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
import sys

from lmi.scripts.common import Configuration
from lmi.scripts.common import get_logger

PYTHON_EGG_NAME = "lmi-scripts"

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
    log_file = None
    if app_config.config.has_option('Log', 'OutputFile'):
        # avoid warning for missing/unconfigured option
        log_file = app_config.get_safe('Log', 'OutputFile')
        if log_file is not None:
            cfg['handlers']['file']['filename'] = log_file
            cfg['formatters']['file']['format'] = app_config.get_safe(
                    'Log', 'FileFormat', raw=True)
            try:
                cfg['handlers']['file']['level'] = \
                        getattr(logging, app_config.logging_level.upper())
            except KeyError:
                LOG().error('unsupported logging level: "%s"',
                        app_config.logging_level)
            cfg['root']['handlers'].append('file')
    if log_file is None:
        del cfg['formatters']['file']
        del cfg['handlers']['file']

    # Set up logging to console
    if stderr is not sys.stderr:
        cfg['handlers']['console']['stream'] = stderr
    cfg['handlers']['console']['level'] = {
            Configuration.OUTPUT_SILENT  : logging.ERROR,
            Configuration.OUTPUT_WARNING : logging.WARNING,
            Configuration.OUTPUT_INFO    : logging.INFO,
            Configuration.OUTPUT_DEBUG   : logging.DEBUG,
        }.get(app_config.verbosity)
    cfg['formatters']['console']['format'] = app_config.get_safe(
            'Log', 'ConsoleFormat', raw=True)

    logging.config.dictConfig(cfg)

def get_version(egg_name=PYTHON_EGG_NAME):
    """
    Gets version string of any python egg. Defaults to the egg of current
    application.
    """
    return pkg_resources.get_distribution(egg_name).version
