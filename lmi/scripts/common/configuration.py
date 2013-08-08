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
Module for SoftwareConfiguration class.

SoftwareConfiguration
---------------------

.. autoclass:: SoftwareConfiguration
    :members:

"""

import os
from lmi.base.BaseConfiguration import BaseConfiguration

class Configuration(BaseConfiguration):
    """
        Configuration class specific to software providers.
        OpenLMI configuration file should reside in
        /etc/openlmi/scripts/lmi.conf.
    """

    CONFIG_FILE_PATH_TEMPLATE = BaseConfiguration.CONFIG_DIRECTORY_TEMPLATE + \
            "lmi.conf"
    USER_CONFIG_FILE_PATH = "~/.lmirc"

    OUTPUT_SILENT  = -1
    OUTPUT_WARNING = 0
    OUTPUT_INFO    = 1
    OUTPUT_DEBUG   = 2

    def __init__(self, user_config_file_path=USER_CONFIG_FILE_PATH, **kwargs):
        """
        :param user_config_file_path: (``str``) Path to the user configuration
            options.
        """
        self._user_config_file_path = os.path.expanduser(user_config_file_path)
        BaseConfiguration.__init__(self, **kwargs)
        self._verbosity = self.OUTPUT_WARNING
        self._trace = False

    @classmethod
    def provider_prefix(cls):
        return "scripts"

    @classmethod
    def default_options(cls):
        """ :rtype: (``dict``) Dictionary of default values. """
        defaults = BaseConfiguration.default_options().copy()
        defaults["Verbosity"] = "0"
        defaults["CommandNamespace"] = 'lmi.scripts.cmd'
        defaults["Trace"] = "False"
        defaults['FileFormat'] = \
                "%(asctime)s:%(levelname)-8s:%(name)s:%(lineno)d - %(message)s"
        defaults['ConsoleFormat'] = "%(levelname)s: %(message)s"
        return defaults

    @classmethod
    def mandatory_sections(cls):
        sects = set(BaseConfiguration.mandatory_sections())
        sects.add('Main')
        return list(sects)

    @property
    def verbosity(self):
        """ Return integer indicating verbosity level of output to console. """
        if self._verbosity is None:
            return self.get_safe('Main', 'Verbosity', int, self.OUTPUT_WARNING)
        return self._verbosity

    @verbosity.setter
    def verbosity(self, level):
        """ Allow to set verbosity without modifying configuration values. """
        if not isinstance(level, (long, int)):
            raise TypeError("level must be integer")
        if level < self.OUTPUT_SILENT:
            level = self.OUTPUT_SILENT
        elif level > self.OUTPUT_DEBUG:
            level = self.OUTPUT_DEBUG
        self._verbosity = level

    @property
    def silent(self):
        """ Whether to suppress all output messages except for errors. """
        return self.verbosity <= self.OUTPUT_SILENT
    @property
    def verbose(self):
        """ Whether to output more details. """
        return self.verbosity >= self.OUTPUT_INFO

    @property
    def trace(self):
        """ Whether the tracebacks shall be printed upon errors. """
        if self._trace:
            return self._trace
        return self.get_safe('Main', 'Trace', bool, False)
    @trace.setter
    def trace(self, trace):
        """ Allow to override configuration option Trace. """
        self._trace = bool(trace)

    def load(self):
        """ Read additional user configuration file if it exists. """
        BaseConfiguration.load(self)
        self.config.read(self._user_config_file_path)

