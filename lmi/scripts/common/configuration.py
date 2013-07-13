# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
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
# -*- coding: utf-8 -*-
"""
Module for SoftwareConfiguration class.

SoftwareConfiguration
---------------------

.. autoclass:: SoftwareConfiguration
    :members:

"""

import os
from lmi.common.BaseConfiguration import BaseConfiguration

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

    @classmethod
    def provider_prefix(cls):
        return "scripts"

    @classmethod
    def default_options(cls):
        """ :rtype: (``dict``) Dictionary of default values. """
        defaults = BaseConfiguration.default_options().copy()
        defaults["Verbose"] = False
        return defaults

    @property
    def verbosity(self):
        """ Return integer indicating verbosity level of output to console. """
        if self._verbosity is None:
            return self.get_safe('Main', 'Verbose', bool, self.OUTPUT_WARNING)
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

    def load(self):
        """ Read additional user configuration file if it exists. """
        BaseConfiguration.load(self)
        self.config.read(self._user_config_file_path)

