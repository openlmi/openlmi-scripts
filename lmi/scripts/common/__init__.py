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
