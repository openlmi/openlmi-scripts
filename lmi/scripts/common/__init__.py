# Software Management Providers
#
# Copyright (C) 2012-2013 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Package with client-side python modules and command line utilities.
"""

import logging
from lmi.scripts.common.configuration import Configuration

DEFAULT_LOGGING_CONFIG = {
    "version" : 1,
    'disable_existing_loggers' : True,
    "formatters": {
        # this is a message format for logging function/method calls
        # it's manually set up in YumWorker's init method
        "default": {
            "default" : "%(levelname)s:%(module)s:"
                        "%(funcName)s:%(lineno)d - %(message)s"
            },
        },
    "handlers": {
        "stderr" : {
            "class" : "logging.StreamHandler",
            "level" : "ERROR",
            "formatter": "default",
            },
        },
    "root": {
        "level": "ERROR",
        "handlers" : ["cmpi"],
        },
    }

def setup_logging(config):
    """
    Set up the logging with options given by Configuration instance.
    This should be called at process's startup before any message is sent to
    log.

    :param config: (``BaseConfiguration``) Configuration with Log section
        containing settings for logging.
    """
    cp = config.config
    logging_setup = False
    try:
        path = config.file_path('Log', 'FileConfig')
        if not os.path.exists(path):
            logging.getLogger(__name__).error('given FileConfig "%s" does'
                    ' not exist', path)
        else:
            logging.config.fileConfig(path)
            logging_setup = True
    except Exception:
        if cp.has_option('Log', 'FileConfig'):
            logging.getLogger(__name__).exception(
                    'failed to setup logging from FileConfig')
    if logging_setup is False:
        defaults = DEFAULT_LOGGING_CONFIG.copy()
        defaults["handlers"]["cmpi"]["cmpi_logger"] = env.get_logger()
        if config.stderr:
            defaults["root"]["handlers"] = ["stderr"]
        level = config.logging_level
        if not level in LOGGING_LEVELS:
            logging.getLogger(__name__).error(
                    'level name "%s" not supported', level)
        else:
            level = LOGGING_LEVELS[level]
            for handler in defaults["handlers"].values():
                handler["level"] = level
            defaults["root"]["level"] = level
        logging.config.dictConfig(defaults)

def get_logger(module_name):
    """
    Convenience function for getting callable returning logger for particular
    module name. It's supposed to be used at module's level to assign its
    result to global variable like this:

        LOG = common.get_logger(__name__)

    This can be used in module's functions and classes like this:

        def module_function(param):
            LOG().debug("this is debug statement logging param: %s", param)

    Thanks to ``LOG`` being a callable, it always returns valid logger object
    with current configuration, which may change overtime.
    """
    def _logger():
        """ Callable used to obtain current logger object. """
        return logging.getLogger(module_name)
    return _logger
