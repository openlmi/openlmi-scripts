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
Module with convenient function for defining user commands.
"""

from lmi.scripts.common.command import LmiLister
from lmi.scripts.common.command import LmiCommandMultiplexer
from lmi.scripts.common.command import LmiSelectCommand
from lmi.scripts.common.command import util

def make_list_command(func,
        name=None,
        columns=None,
        verify_func=None,
        transform_func=None):
    """
    Create a command subclassed from :py:class:`~.lister.LmiLister`. Please
    refer to this class for detailed usage.

    :param func: Contents of ``CALLABLE`` property.
    :type func: string or callable
    :param string name: Optional name of resulting class. If not given,
        it will be made from the name of associated function.
    :param tuple columns: Contents of ``COLUMNS`` property.
    :param callable verify_func: Callable overriding
        py:meth:`~.endpoint.LmiEndPointCommand.verify_options` method.
    :param callable transform_func: Callable overriding
        :py:meth:`~.endpoint.LmiEndPointCommand.transform_options` method.
    :returns:  Subclass of :py:class:`~.lister.LmiLister`.
    :rtype: type
    """
    if name is None:
        if isinstance(func, basestring):
            name = func.split('.')[-1]
        else:
            name = func.__name__
        if not name.startswith('_'):
            name = '_' + name.capitalize()
    props = { 'COLUMNS' : columns
            , 'CALLABLE' : func
            , '__module__' : util.get_module_name() }
    if verify_func:
        props['verify_options'] = verify_func
    if transform_func:
        props['transform_options'] = transform_func
    return LmiLister.__metaclass__(name, (LmiLister, ), props)

def register_subcommands(command_name, usage, command_map,
        fallback_command=None):
    """
    Create a multiplexer command (a node in a tree of commands).

    :param string command_name: Name of created command. The same as will
        be given on a command line.
    :param string usage: Usage string parseable by ``docopt``.
    :param dictionary command_map: Dictionary of subcommands. Associates
        command names to their factories. It's assigned to ``COMMANDS``
        property.
    :param fallback_command: Command factory used when no command is given
        on command line.
    :type fallback_command: :py:class:`~.endpoint.LmiEndPointCommand`
    :returns: Subclass of :py:class:`~.multiplexer.LmiCommandMultiplexer`.
    :rtype: type
    """
    props = { 'COMMANDS'         : command_map
            , 'OWN_USAGE'        : True
            , '__doc__'          : usage
            , '__module__'       : util.get_module_name()
            , 'FALLBACK_COMMAND' : fallback_command }
    return LmiCommandMultiplexer.__metaclass__(command_name,
            (LmiCommandMultiplexer, ), props)

def select_command(command_name, *args, **kwargs):
    """
    Create command selector that loads command whose requirements are met.

    Example of invocation: ::

        Hardware = select_command('Hardware',
            ("Openlmi-Hardware >= 0.4.2", "lmi.scripts.hardware.current.Cmd"),
            ("Openlmi-Hardware < 0.4.2" , "lmi.scripts.hardware.pre042.Cmd"),
            default=HwMissing
        )

    Above example checks remote broker for OpenLMI-Hardware provider. If it is
    installed and its version is equal or higher than 0.4.2, command from
    ``current`` module will be used. For older registered versions command
    contained in ``pre042`` module will be loaded. If hardware provider is not
    available, HwMissing command will be loaded instead.

    .. seealso::
        Check out the grammer describing language used in these conditions at
        :py:mod:`lmi.scripts.common.versioncheck.parser`.

    :param args: List of pairs ``(condition, command)`` that are inspected in
        given order until single condition is satisfied. Associated command is
        then loaded. Command is either a reference to command class or path to
        it given as string. In latter case last dot divides module's import
        path and command name.
    :param default: This command will be loaded when no condition from *args*
        is satisfied.
    """
    props = { 'SELECT'         : args
            , 'DEFAULT'        : kwargs.get('default', None)
            , '__module__'     : util.get_module_name()
            }
    return LmiSelectCommand.__metaclass__(command_name,
            (LmiSelectCommand, ), props)

