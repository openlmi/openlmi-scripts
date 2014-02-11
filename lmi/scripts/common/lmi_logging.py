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
import logging

#: Default format string to use in stderr handlers.
DEFAULT_FORMAT_STRING = "%(levelname_)-8s: %(message)s"

class LogRecord(logging.LogRecord):

    def __init__(self, name, *args, **kwargs):
        logging.LogRecord.__init__(self, name, *args, **kwargs)
        self.levelname_ = self.levelname

class ScriptsLogger(logging.getLoggerClass()):

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None,
            extra=None):
        """
        Overriden method that just changes the *LogRecord* class to our
        predefined.
        """
        rv = LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv

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
    def __init__(self, formatters, default=DEFAULT_FORMAT_STRING,
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
            LOG().debug("this is debug statement logging param: %s", param)

    Thanks to ``LOG`` being a callable, it always returns valid logger object
    with current configuration, which may change overtime.

    :param string module_name: Absolute dotted module path.
    :rtype: :py:class:`logging.Logger`
    """
    def _logger():
        """ Callable used to obtain current logger object. """
        return logging.getLogger(module_name)
    return _logger

def setup_logger():
    logging.setLoggerClass(ScriptsLogger)
