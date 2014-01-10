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
Module with interactive application.
"""

import cmd
import docopt
import itertools
import shlex

from lmi.scripts.common import errors
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

class Interactive(cmd.Cmd):
    """
    Launched by the main application. It enters *shell* mode allowing. Allows
    to launch set of commands interactively on all given hosts. Session object
    stays the same for the whole life of interactive mode.

    :param parent_app: Main application object. It contains ``stdin``,
        ``stdout`` and ``stderr`` attributes.
    :param prompt: (``str``) Command line prompt.
    """

    def __init__(self, parent_app, prompt):
        self._parent = parent_app
        cmd.Cmd.__init__(self,
                stdin=parent_app.stdin, stdout=parent_app.stdout)
        self.prompt = prompt
        self._last_exit_code = 0

    @property
    def command_manager(self):
        """ Return instance of ``CommandManager``. """
        return self._parent.command_manager

    def run_subcommand(self, args):
        """
        Run a subcommand given as a first item of ``args``. It must be one of
        commands registered in manager. Returns the return value of invoked
        command.

        :param args: (``list``) List of commands.
        """
        if not isinstance(args, (list, tuple)):
            raise TypeError("args must be a list")
        if len(args) < 1:
            raise ValueError("args must not be empty")
        cmd_factory = self.command_manager[args[0]]
        cmd_inst = cmd_factory(self._parent, args[0])
        return cmd_inst.run(args[1:])

    def default(self, line):
        """
        This is run, when line contains unknown command to ``cmd.Cmd``. It
        expects us to handle it if we know it, or print an error.

        :param line: (``str``) Line given to our shell.
        """
        line_parts = shlex.split(line)
        try:
            # let's try to run registered subcommand
            retval = self.run_subcommand(line_parts)
            if isinstance(retval, bool) or not isinstance(retval, (int, long)):
                retval = 0 if bool(retval) or retval is None else 1
            self._last_exit_code = retval
            return retval
        except errors.LmiCommandNotFound:
            return cmd.Cmd.default(self, line)
        except docopt.DocoptExit as err:
            # command found, but options given to it do not comply with its
            # usage string
            LOG().warn("wrong options given: %s", line.strip())
            self.stdout.write(str(err))
            self.stdout.write("\n")

    def empty_line(self):   #pylint: disable=R0201
        """ Do nothing for empty line. """
        return 0

    def completedefault(self, text, *_args, **_kwargs):
        """
        Tab-completion for commands known to the command manager.
        Does not handle options on the commands.
        """
        if not text:
            completions = sorted(n for n, v in self.command_manager)
        else:
            completions = sorted(n for n, v in self.command_manager
                              if n.startswith(text))
        return completions

    def help_help(self):
        """
        Use the command manager to get instructions for "help".
        """
        return self.run_subcommand(["help", "help"])

    def do_help(self, arg):
        """ Handle help subcommand. """
        if arg:
            # Check if the arg is a builtin command or something
            # coming from the command manager
            arg_parts = shlex.split(arg)
            method_name = '_'.join(
                itertools.chain(['do'],
                    itertools.takewhile(lambda x: not x.startswith('-'),
                                        arg_parts)))
            # Have the command manager version of the help
            # command produce the help text since cmd and
            # cmd2 do not provide help for "help"
            if hasattr(self, method_name):
                return cmd.Cmd.do_help(self, arg)
            # Dispatch to the underlying help command,
            # which knows how to provide help for extension
            # commands.
            self.run_subcommand(["help", arg])
        else:
            cmd.Cmd.do_help(self, arg)
            cmd_names = sorted(self.command_manager)
            self.print_topics(
                    "Application commands (type help <topic>):",
                    cmd_names, 15, 80)
        return

    def do_EOF(self, _arg):     #pylint: disable=C0103,R0201
        """
        Exit on End-Of-File.
        """
        raise errors.LmiTerminate(self._last_exit_code)

    def get_names(self):
        """
        Override the base class version to filter out things that look like
        they should be hidden from the user.
        """
        return [  n for n in cmd.Cmd.get_names(self)
               if not n.startswith('do__')]

    def postcmd(self, stop, _line):
        """
        This is called after the ``do_*`` command to postprocess its result and
        decide whether to stop the shell. We want to stop only when
        :py:class:`lmi.scripts.common.errors.LmiError` is raised. This
        exception is catched upwards in call chain.

        :returns: Whether to stop the shell.
        :rtype: bool
        """
        return False

