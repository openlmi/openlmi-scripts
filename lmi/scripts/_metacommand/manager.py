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
Manager module for direct subcommands of lmi metacommand. Most of them are
loaded from entry_points of installed python eggs.
"""

import pkg_resources

from lmi.scripts.common import Configuration
from lmi.scripts.common import errors
from lmi.scripts.common import get_logger
from lmi.scripts.common.command import base
from lmi.scripts.common.command import util

LOG = get_logger(__name__)

class _CustomCommandWrapper(object):
    """
    Provide an interface mocking an entry_point object for custom commands
    added by lmi metacommand application.

    :param name: (``str``) Name of command.
    :param cmd_class: (``LmiBaseCommand``) Factory for custom commands.
    """

    def __init__(self, name, cmd_class):
        if not isinstance(name, basestring):
            raise TypeError("name must be a string")
        if not issubclass(cmd_class, base.LmiBaseCommand):
            raise TypeError("cmd_class must be a LmiBaseCommand")
        self._name = name
        self._cmd_class = cmd_class

    @property
    def name(self):
        """ Return command name. """
        return self._name

    def load(self):
        """ Return command class. """
        return self._cmd_class

class CommandManager(object):
    """
    Manager of direct subcommands of lmi metacommand. It manages commands
    registered with entry_points under particular namespace installed by
    python eggs. Custom commands may also be added.

    :param namespace: (``str``) Namespace, where commands are registered.
        For example ``lmi.scripts.cmd``.
    """

    def __init__(self, namespace=None):
        if namespace is not None and not isinstance(namespace, basestring):
            raise TypeError("namespace must be a string")
        if namespace is None:
            namespace = Configuration.get_instance().get_safe(
                    "Main", "CommandNamespace")
        self._namespace = namespace
        self._commands = {}
        self._load_commands()

    @property
    def command_names(self):
        """ Returns list of command names. """
        return self._commands.keys()

    def __len__(self):
        return len(self._commands)

    def __iter__(self):
        """ Yields command names. """
        return iter(self._commands)

    def __getitem__(self, cmd_name):
        """ Gets command factory for name. """
        return self.find_command(cmd_name)

    def _load_commands(self):
        """ Loads commands from entry points under provided namespace. """
        def _add_entry_point(epoint):
            """
            Convenience function taking an entry point, making some name
            checks and adding it to registered commands.
            """
            if not util.RE_COMMAND_NAME.match(epoint.name):
                LOG().error('invalid command name: %s, ignoring', epoint.name)
                return
            if epoint.name in self._commands:
                LOG().warn('command "%s" already registered, ignoring',
                        epoint.name)
            else:
                LOG().debug('found command "%s"', epoint.name)
                self._commands[epoint.name] = epoint

        for entry_point in pkg_resources.iter_entry_points(self._namespace):
            if isinstance(entry_point, dict):
                for epoint in entry_point.values():
                    _add_entry_point(epoint)
            else:
                _add_entry_point(entry_point)


    def add_command(self, name, cmd_class):
        """
        Registers custom command. May be used for example for *help* command.

        :param name: (``str``) Name of command.
        :param cmd_class: (``LmiBaseCommand``) Factory for commands.
        """
        if not isinstance(name, basestring):
            raise TypeError("name must be a string")
        if not issubclass(cmd_class, base.LmiBaseCommand):
            raise TypeError("cmd_class must be a LmiBaseCommand")
        if not util.RE_COMMAND_NAME.match(name):
            raise errors.LmiCommandInvalidName(
                    cmd_class.__module__, cmd_class.__class__.__name__, name)
        if name in self._commands:
            LOG().warn('command "%s" already managed, overwriting with "%s:%s"',
                    name, cmd_class.__module__, cmd_class.__name__)
        self._commands[name] = _CustomCommandWrapper(name, cmd_class)

    def find_command(self, cmd_name):
        """
        Loads a command associated with given name and returns it.

        :param cmd_name: (``str``) Name of command to load.
        :rtype: (``LmiBaseCommand``) Factory for commands.
        """
        try:
            return self._commands[cmd_name].load()
        except KeyError:
            raise errors.LmiCommandNotFound(cmd_name)

    def reload_commands(self, keep_custom=True):
        """
        Flushes all commands and reloads entry points.

        :param keep_custom: (``bool``) Custom commands -- not loaded from
            entry points -- are preserved.
        """
        if keep_custom:
            keep = {  n: c for n, c in self._commands.items()
                   if isinstance(c, _CustomCommandWrapper)}
        else:
            keep = {}
        self._commands = {}
        self._load_commands()
        self._commands.update(keep)

