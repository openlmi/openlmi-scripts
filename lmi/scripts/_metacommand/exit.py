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
"""
Module containing help command.
"""

from lmi.scripts.common import get_logger
from lmi.scripts.common.command import LmiEndPointCommand
from lmi.scripts.common import errors

LOG = get_logger(__name__)

def _execute_exit(exit_code):
    """ Associated function with ``Exit`` command. """
    raise errors.LmiTerminate(exit_code)

class Exit(LmiEndPointCommand):
    """
    Terminate the shell.

    Usage: %(cmd)s [<exit_code>]
    """
    CALLABLE = _execute_exit
    OWN_USAGE = True

    def verify_options(self, options):
        code = options['<exit_code>']
        if code is not None:
            try:
                int(code)
            except ValueError:
                raise errors.LmiInvalidOptions(
                        "<exit_code> must be an integer not \"%s\"" % code)

    def transform_options(self, options):
        code = options.get('<exit_code>', None)
        if code is None:
            code = 0
        options['<exit_code>'] = int(code)

