# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
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
Utilities for logging framework.
"""
import logging
import sys

from lmi.scripts.common import configuration
from lmi.scripts.common import errors

TERM_COLOR_NAMES = (
        'black',
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'white',
        )

# Following are terminal color codes of normal mode.
CN_BLACK   = 0
CN_RED     = 1
CN_GREEN   = 2
CN_YELLOW  = 3
CN_BLUE    = 4
CN_MAGENTA = 5
CN_CYAN    = 6
CN_WHITE   = 7
# Following are terminal color codes of bright mode.
CB_BLACK   = 8
CB_RED     = 9
CB_GREEN   = 10
CB_YELLOW  = 11
CB_BLUE    = 12
CB_MAGENTA = 13
CB_CYAN    = 14
CB_WHITE   = 15

WARNING_COLOR  = CB_YELLOW
ERROR_COLOR    = CB_RED
CRITICAL_COLOR = CB_MAGENTA

#: Dictionary assigning color code to logging level.
LOG_LEVEL_2_COLOR = {
        logging.WARNING : WARNING_COLOR,
        logging.ERROR   : ERROR_COLOR,
        logging.CRITICAL: CRITICAL_COLOR
}

class LogRecord(logging.LogRecord):
    """
    Overrides :py:class:`logging.LogRecord`. It adds new attributes:

        * `levelname_` - Name of level in lowercase.
        * `cseq`       - Escape sequence for terminal used to set color
                         assigned to particular log level.
        * `creset`     - Escape sequence for terminal used to reset foreground
                         color.

    These can be used in format strings initializing logging formatters.

    Accepts the same arguments as base class.
    """

    def __init__(self, name, level, *args, **kwargs):
        use_colors = kwargs.pop('use_colors', True)
        logging.LogRecord.__init__(self, name, level, *args, **kwargs)
        self.levelname_ = self.levelname.lower()
        if use_colors and level >= logging.WARNING:
            if level >= logging.CRITICAL:
                color = LOG_LEVEL_2_COLOR[logging.CRITICAL]
            elif level >= logging.ERROR:
                color = LOG_LEVEL_2_COLOR[logging.ERROR]
            else:
                color = LOG_LEVEL_2_COLOR[logging.WARNING]
            self.cseq = get_color_sequence(color)
            self.creset = "\x1b[39m"
        else:
            self.cseq = self.creset = ''

class ScriptsLogger(logging.getLoggerClass()):

    #: Boolean saying whether the color sequences for log messages shall be
    #: generated.
    USE_COLORS = True

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None,
            extra=None):
        """
        Overriden method that just changes the *LogRecord* class to our
        predefined and ensures that exception's traceback is printed once at
        most.
        """
        if exc_info:
            err = exc_info[1]
            if getattr(err, '_traceback_logged', False):
                # do not print traceback second time
                exc_info = None
            elif self.isEnabledFor(level):
                try:
                    err._traceback_logged = True
                except AttributeError:
                    pass
        rv = LogRecord(name, level, fn, lno, msg, args, exc_info, func,
                use_colors=self.USE_COLORS)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv

    def exception(self, msg, *args, **kwargs):
        lmi_config = configuration.Configuration.get_instance()
        exc_info = sys.exc_info()
        err = exc_info[1]
        if (   lmi_config.trace
           and (  not isinstance(err, errors.LmiError)
               or (   not getattr(err, '_traceback_logged', False)
                  and lmi_config.verbosity >= lmi_config.OUTPUT_DEBUG))):
            kwargs['exc_info'] = exc_info
        else:
            kwargs.pop('exc_info', None)
        self.error(msg, *args, **kwargs)

class LevelDispatchingFormatter(object):
    """
    Formatter class for logging module. It allows to predefine different format
    string used for some level ranges.

    :param dict formatters: Mapping of module names to *format*.
        It is a dictionary of following format: ::

            { max_level1 : format1
            , max_level2 : format2
            , ... }

        *format* in parameters description can be either ``string`` or another
        formatter object.

        For example if you want to have format3 used for *ERROR* and *CRITICAL*
        levels, *format2* for *INFO* and *format1* for anything else, your
        dictionary will look like this: ::

            { logging.INFO - 1 : format1
            , logging.INFO     : format2 }

        And the *default* value should have *format3* assigned.

    :param default: Default *format* to use. This format is used for all levels
        higher than the maximum of *formatters*' keys.
    """
    def __init__(self, formatters, default=configuration.DEFAULT_FORMAT_STRING,
            datefmt=None):
        for k, formatter in formatters.items():
            if isinstance(formatter, basestring):
                formatters[k] = logging.Formatter(formatter, datefmt=datefmt)
        #: This a a tuple of pairs sorted by the first item in descending
        #: order (highest priority ordered first).
        self._formatters = tuple(sorted(formatters.items(),
            key=lambda t: -t[0]))
        if isinstance(default, basestring):
            default = logging.Formatter(default, datefmt=datefmt)
        self._default_formatter = default

    def format(self, record):
        """
        Interface for logging module.
        """
        record.levelname_ = record.levelname.lower()
        formatter = self._default_formatter
        for level, fmt in self._formatters:
            if level < record.levelno:
                break
            formatter = fmt
        try:
            return formatter.format(record)
        except KeyError:
            # in some modules or libraries it may happen that logger is
            # initialized before our logger class is set as default
            record.cseq = record.creset = ''
            return formatter.format(record)

def get_logger(module_name):
    """
    Convenience function for getting callable returning logger for particular
    module name. It's supposed to be used at module's level to assign its
    result to global variable like this: ::

        from lmi.scripts import common

        LOG = common.get_logger(__name__)

    This can be used in module's functions and classes like this: ::

        def module_function(param):
            LOG().debug("This is debug statement logging param: %s", param)

    Thanks to ``LOG`` being a callable, it always returns valid logger object
    with current configuration, which may change overtime.

    :param string module_name: Absolute dotted module path.
    :rtype: :py:class:`logging.Logger`
    """
    def _logger():
        """ Callable used to obtain current logger object. """
        return logging.getLogger(module_name)
    return _logger

def get_color_sequence(color_code):
    """
    Computer color sequence for particular color code.

    :returns: Escape sequence for terminal used to set foreground color.
    :rtype: str
    """
    if color_code <= 7:
        return "\x1b[%dm" % (30 + color_code)
    return "\x1b[38;5;%dm" % color_code

def setup_logger(use_colors=True):
    """
    This needs to be called before any logging takes place.
    """
    ScriptsLogger.USE_COLORS = use_colors
    logging.setLoggerClass(ScriptsLogger)
