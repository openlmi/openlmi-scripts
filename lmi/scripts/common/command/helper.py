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
Module with convenient function for defining user commands.
"""

from lmi.scripts.common.command import LmiLister
from lmi.scripts.common.command import LmiCommandMultiplexer

def make_list_command(func,
        name=None,
        columns=None,
        verify_func=None,
        transform_func=None):
    """
    Create a command subclassed from ``LmiLister``.
    Please refer to this class for detailed usage.

    :param func: (``str`` or callable) Contents of ``CALLABLE`` property.
    :param name: (``str``) Optional name of resulting class. If not given,
        it will be made from the name of associated function.
    :param columns: (``tuple``) Contents of ``COLUMNS`` property.
    :param verify_func: Callable overriding ``verify_options()`` method.
    :param transform_func: Callable overriding ``transform_options()`` method.
    :rtype: (``type``) Subclass of ``LmiLister`` (command factory).
    """
    if name is None:
        if isinstance(func, basestring):
            name = func.split('.')[-1]
        else:
            name = func.__name__
        if not name.startswith('_'):
            name = '_' + name.capitalize()
    props = { 'COLUMNS' : columns, 'CALLABLE' : func }
    if verify_func:
        props['verify_options'] = verify_func
    if transform_func:
        props['transform_options'] = transform_func
    return LmiLister.__metaclass__(name, (LmiLister, ), props)

def register_subcommands(command_name, usage, command_map):
    """
    Create a multiplexer command (a node in a tree of commands).

    :param command_name: (``str``) Name of created command. The same as will
        be given on a command line.
    :param usage: (``str``) Usage string parseable by ``docopt``.
    :param command_map: (``dict``) Dictionary of subcommands. Associates
        command names to their factories.
    :rtype: (``type``) Subclass of ``LmiCommandMultiplexer`` (command factory).
    """
    props = { 'COMMANDS'   : command_map
            , 'OWN_USAGE'  : True
            , '__doc__'    : usage }
    return LmiCommandMultiplexer.__metaclass__(command_name,
            (LmiCommandMultiplexer, ), props)

