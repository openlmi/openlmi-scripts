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
Module defining base command class for all possible commands of lmi
meta-command.
"""

import abc
import re

# regular expression matching leading whitespaces not until the first line
# containing non-white-spaces
RE_LSPACES = re.compile(r'\A(\s*$.)*', re.DOTALL | re.MULTILINE)
RE_COMMAND_NAME = re.compile(r'^[a-z]+(-[a-z]+)*$')

class LmiBaseCommand(object):
    """
    Abstract base class for all commands handling command line arguemtns.
    Instances of this class are organized in a tree with root element being
    the lmi metacommand (if not running in interactive mode). Each such
    instance can have more child commands if it's ``is_end_point()`` method
    return False. Each has one parent command except for the top level one,
    whose ``parent`` property returns ``None``.

    Set of commands is organized in a tree, where each command
    (except for the root) has its own parent. ``is_end_point()`` method
    distinguish leaves from nodes. The path from root command to the
    leaf is a sequence of commands passed to command line.

    If the ``has_own_usage()`` returns True, the parent command won't process
    the whole command line and the remainder will be passed as a second
    argument to the ``run()`` method.

    :param app: Main application object.
    :param cmd_name: (``str``) Name of command.
    :param parent: (``LmiBaseCommand``) Instance of parent command.
    """

    __metaclass__ = abc.ABCMeta

    @classmethod
    def get_description(cls):
        """
        Return description for this command. This is usually a first line
        of documentation string of a class.
        """
        if cls.__doc__ is None:
            return ""
        return cls.__doc__.strip().split("\n", 1)[0]

    @classmethod
    def is_end_point(cls):
        """
        Return True, if this command parses the rest of command line and can
        not have any child subcommands.

        :rtype: (``bool``)
        """
        return True

    @classmethod
    def has_own_usage(cls):
        """
        Return True, if this command has its own usage string, which is
        returned by get_description(). Otherwise the parent command must be
        queried.
        """
        return False

    @classmethod
    def child_commands(cls):
        """
        Abstract class method returning dictionary of child commands with
        structure:

            { "command-name" : cmd_factory, ... }

        Dictionary contains just a direct children (commands, which
        may immediately follow this particular command on command line).
        """
        raise NotImplementedError("child_commands() method must be overriden"
                " in a subclass")


    def __init__(self, app, cmd_name, parent=None):
        if not isinstance(cmd_name, basestring):
            raise TypeError('cmd_name must be a string')
        if parent is not None and not isinstance(parent, LmiBaseCommand):
            raise TypeError('parent must be an LmiBaseCommand instance')
        self._app = app
        self._cmd_name = cmd_name.strip()
        self._parent = parent

    @property
    def app(self):
        """ Return application object. """
        return self._app

    @property
    def parent(self):
        """ Return parent command. """
        return self._parent

    @property
    def cmd_name(self):
        """ Name of this subcommand as a single word. """
        return self._cmd_name

    @property
    def cmd_full_name(self):
        """
        Name of this subcommand with all prior commands included.
        It's the sequence of commands as given on command line up to this
        subcommand without any options present. In interactive mode
        this won't contain the name of binary (``sys.argv[0]``).

        :rtype: (``str``) Concatenation of all preceding commands with
            ``cmd_name``.
        """
        return ' '.join(self.cmd_name_args)

    @property
    def cmd_name_args(self):
        """
        The same as ``cmd_full_name``, except the result is a list of
        subcommands.

        :rtype: (``list``) List of command strings as given on command line
            up to this command.
        """
        if self.parent is not None:
            return self.parent.cmd_name_args + [self.cmd_name]
        return [self._cmd_name]

    @property
    def docopt_cmd_name_args(self):
        """
        Arguments array for docopt parser. Similar to ``cmd_name_args`` except
        for the leading binary name, which is omitted here.

        :rtype: (``list``)
        """
        if self.app.interactive_mode:
            return self.cmd_name_args
        return self.cmd_name_args[1:]

    def get_usage(self, proper=False):
        """
        Get command usage. Return value of this function is used by docopt
        parser as usage string. Command tree is traversed upwards until command
        with defined usage string is found. End point commands (leaves) require
        manually written usage, so the first command in the sequence of parents
        with own usage string is obtained and its usage returned. For nodes
        missing own usage string this can be generated based on its
        subcommands.

        :param proper: (``bool``) Says, whether the usage string written
            manually is required or not. It applies only to node (not a leaf)
            commands without its own usage string.
        """
        if self.is_end_point() or self.has_own_usage() or proper:
            # get proper (manually written) usage, also referred as *own*
            cmd = self
            while not cmd.has_own_usage() and cmd.parent is not None:
                cmd = cmd.parent
            if cmd.__doc__ is None:
                docstr = "Usage: %s\n" % self.cmd_full_name
            else:
                docstr = ( ( cmd.__doc__.rstrip()
                           % {'cmd' : cmd.cmd_full_name }
                           ) + "\n")
                match = RE_LSPACES.match(docstr)
                if match:   # strip leading spaces
                    docstr = docstr[match.end(0):]
        else:
            # generate usage string from what is known, applies to nodes
            # without own usage
            hlp = []
            if self.get_description():
                hlp.append(self.get_description())
                hlp.append("")
            hlp.append("Usage:")
            hlp.append("    %s (--help | <command> [<args> ...])"
                    % self.cmd_full_name)
            hlp.append("")
            hlp.append("Commands:")
            cmd_max_len = max(len(c) for c in self.child_commands())
            for name, cmd in sorted(self.child_commands().items()):
                hlp.append(("  %%-%ds %%s" % cmd_max_len)
                        % (name, cmd.get_description()))
            docstr = "\n".join(hlp) + "\n"
        return docstr

    @abc.abstractmethod
    def run(self, args):
        """
        Handle the command line arguments. If this is not an end point
        command, it will pass the unhandled arguments to one of it's child
        commands. So the arguments are processed recursively by the instances
        of this class.

        :param args: (``list``) Arguments passed to the command line that were
            not yet parsed. It's the contents of sys.argv (if in
            non-interactive mode) from the current command on.
        :rtype: (``int``) Exit code of application.
        """
        raise NotImplementedError("run method must be overriden in subclass")

