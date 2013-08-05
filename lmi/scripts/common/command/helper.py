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

