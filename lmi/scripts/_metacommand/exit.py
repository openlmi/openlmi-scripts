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

