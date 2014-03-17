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
Module with interactive application.
"""

import cmd
import docopt
import itertools
import os
import shlex

from lmi.scripts.common import errors
from lmi.scripts.common import get_logger
from lmi.scripts.common.command import LmiBaseCommand, LmiCommandMultiplexer
from lmi.scripts._metacommand import cmdutil
from lmi.scripts._metacommand import exit

LOG = get_logger(__name__)

BUILT_INS_USAGE = """
Built-ins.

Usage:
    : cd [<path>]
    : ..
    : pwd
    : (help | -h | --help)

Description:
    cd    Nest to a subcommand. Accepts a sequence of subcommands separated
          with "/". If "/" is given, top-level command becomes the active one.
          Other supported special symbols are ".." and ".".
    ..    Make parent command the active one. Same as issuing ":cd ..".
    pwd   Print current command path.
    help  Show this help.
"""

BUILT_INS = ('..', 'cd', 'pwd', 'help')

class LmiBuiltInError(errors.LmiError):
    """ General exception concerning the use of built-in commands. """
    pass

class LmiCanNotNest(LmiBuiltInError):
    """ Raised upon invalid use of *cd* built-in command. """
    pass

class Interactive(cmd.Cmd):
    """
    Launched by the main application. It enters *shell* mode. Allows to launch
    set of commands interactively on all given hosts. Session object stays the
    same for the whole life of interactive mode.

    :param top_level_cmd: Top-level command.
    :type top_level_cmd: :py:class:`.toplevel.TopLevelCommand`
    """

    def __init__(self, top_level_cmd):
        self._top_level_cmd = top_level_cmd
        cmd.Cmd.__init__(self,
                stdin=top_level_cmd.app.stdin, stdout=top_level_cmd.app.stdout)
        self._last_exit_code = exit.EXIT_CODE_SUCCESS
        self.doc_header = 'Static commands'
        self.app.active_command = top_level_cmd

    # *************************************************************************
    # Properties
    # *************************************************************************
    @property
    def app(self):
        """ :returns: Application object. """
        return self._top_level_cmd.app

    @property
    def command_manager(self):
        """ :returns: An instance of :py:class:`~.manager.CommandManager`. """
        return self.app.command_manager

    @property
    def on_top_level_node(self):
        """
        :returns: Whether the current node is a top-level one. In other words
            we're not nested in any subcommand namespace.
        :rtype: boolean
        """
        return self._top_level_cmd is self.app.active_command

    @property
    def prompt(self):
        """
        :returns: Dynamically computed shell prompt.
        :rtype: string
        """
        if self.app.stdin.isatty():
            parents_num = 0
            node = self.app.active_command
            while node.parent is not None:
                parents_num += 1
                node = node.parent
            return '>'*parents_num + self.app.active_command.cmd_name + '> '
        return ''

    # *************************************************************************
    # Private methods
    # *************************************************************************
    def _change_to_node(self, path):
        """
        Handles any command path. It constructs an object of command
        corresponding to given path. Path can be absolute or relative.

        :param str path: Path to command. Looks similar to unix file path.
            Command names are separated with ``'/'``.
        :returns: Multiplexer command corresponding to path.
        :rtype: :py:class:`~lmi.scripts.common.command.multiplexer.LmiCommandMultiplexer`
        """
        cur_node = self.app.active_command
        if path.startswith('/'):
            if path.startswith('/lmi'):
                path = path[4:]
            else:
                path = path[1:]
            cur_node = self._top_level_cmd

        cmd_chain = os.path.normpath(path).split('/')
        for subcmd in cmd_chain:
            if subcmd == '..':
                cur_node = (  cur_node.parent
                           if cur_node.parent is not None else cur_node)
            elif subcmd and subcmd != '.':
                if not subcmd in cmdutil.get_subcommand_names(cur_node):
                    raise LmiCanNotNest('No such subcommand "%s".' %
                            "/".join(cmd_chain))
                cmd_cls = cmdutil.get_subcommand_factory(cur_node, subcmd)
                if not issubclass(cmd_cls, LmiCommandMultiplexer):
                    raise LmiCanNotNest('Can not nest to subcommand "%s" which'
                            " is not a multiplexer." % "/".join(cmd_chain))
                if not cmd_cls.has_own_usage():
                    raise LmiCanNotNest('Can not nest to subcommand "%s" which'
                            ' lacks any help message.' % "/".join(cmd_chain))
                cur_node = cmd_cls(self.app, subcmd, cur_node)
        self.app.active_command = cur_node
        return exit.EXIT_CODE_SUCCESS

    def _do_built_in_cmd(self, args):
        """
        Execute built-in command.

        :param list args: Command arguments including command name.
        """
        options = docopt.docopt(BUILT_INS_USAGE, args, help=False)
        if options['cd']:
            path = '.' if not options.get('<path>', None) else options['<path>']
            return self._change_to_node(path)
        elif options['..']:
            return self._change_to_node('..')
        elif options['pwd']:
            self.app.stdout.write("/"
                    + "/".join(self.app.active_command.get_cmd_name_parts(
                        all_parts=True)) + "\n")
        elif options['help'] or options['-h'] or options['--help']:
            self.app.stdout.write(BUILT_INS_USAGE[1:])
        return exit.EXIT_CODE_SUCCESS

    def _execute_line_parts(self, line_parts):
        """
        Try to execute given line. This method can throw various exceptions
        that needs to be handled by a caller, otherwise interactive mode will
        be terminated.

        :param list line_parts: Parsed command line arguments.
        :returns: Command's exit code.
        """
        if line_parts[0][0] == ':':
            if len(line_parts[0]) > 1:
                line_parts[0]  = line_parts[0][1:]
            else:
                line_parts = line_parts[1:]
            return self._do_built_in_cmd(line_parts)

        else:
            # let's try to run registered subcommand
            retval = self.run_subcommand(line_parts)
            if isinstance(retval, bool) or not isinstance(retval, (int, long)):
                retval = (    exit.EXIT_CODE_SUCCESS
                         if   bool(retval) or retval is None
                         else exit.EXIT_CODE_FAILURE)
            return retval

    # *************************************************************************
    # Public methods
    # *************************************************************************
    def complete(self, text, state):
        """
        Overrides parent's method so that registered commands can be also
        completed.
        """
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            command, _, _ = self.parseline(line)
            compfunc = self.completedefault
            if command and hasattr(self, 'complete_' + command):
                compfunc = getattr(self, 'complete_' + command)
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def completedefault(self, text, line, *_args, **_kwargs):
        """
        Tab-completion for commands known to the command manager and subcommands
        in current command namespace. Does not handle command options.
        """
        if line.startswith(':'):
            commands = BUILT_INS
        else:
            commands = set(self.completenames(text))
            commands.update(set(cmdutil.get_subcommand_names(self.app.active_command)))
        completions = sorted(n for n in commands
                if not text or n.startswith(text))
        return completions

    def default(self, line):
        """
        This is run, when line contains unknown command to ``cmd.Cmd``. It
        expects us to handle it if we know it, or print an error.

        :param str line: Line given to our shell.
        """
        try:
            line_parts = shlex.split(line)
        except ValueError as err:
            LOG().error(str(err))
            return exit.EXIT_CODE_INVALID_SYNTAX

        try:
            self._execute_line_parts(line_parts)

        except docopt.DocoptExit as err:
            # command found, but options given to it do not comply with its
            # usage string
            if '--help' in line_parts:
                return self.do_help(" ".join(
                    line_parts[:line_parts.index('--help')]))
            LOG().warn("Wrong options given: %s", line.strip())
            self.stdout.write(str(err))
            if (   line_parts[0] in cmdutil.get_subcommand_names(
                    self.app.active_command)
               and cmdutil.get_subcommand_factory(self.app.active_command,
                    line_parts[0]).is_end_point()):
                self.stdout.write("\n\nTo see a full usage string, type:\n"
                        "    help %s\n" % line_parts[0])
            else:
                self.stdout.write("\n\nTo see a list of available commands,"
                        " type:\n    help\n")
            self._last_exit_code = exit.EXIT_CODE_FAILURE

        except errors.LmiCommandNotFound as err:
            LOG().error(str(err))
            self._last_exit_code = exit.EXIT_CODE_COMMAND_NOT_FOUND

        except errors.LmiUnsatisfiedDependencies as err:
            LOG().error(str(err))
            self._last_exit_code = exit.EXIT_CODE_UNSATISFIED_DEPENDENCIES

        except errors.LmiError as err:
            LOG().error(str(err))
            self._last_exit_code = exit.EXIT_CODE_FAILURE

        except KeyboardInterrupt as err:
            LOG().debug('%s: %s', err.__class__.__name__, str(err))
            self._last_exit_code = exit.EXIT_CODE_KEYBOARD_INTERRUPT

        return self._last_exit_code

    def do_EOF(self, _arg):     #pylint: disable=C0103,R0201
        """
        Exit on End-Of-File if we are on top-level command. Otherwise change
        to parent command.
        """
        if self.app.stdin.isatty():
            self.app.stdout.write('\n')
        if self.app.stdin.isatty() and not self.on_top_level_node:
            self._change_to_node('..')
        else:
            raise errors.LmiTerminate(self._last_exit_code)

    def do_exit(self, arg):
        """
        This makes the exit command work in both (non-)interactive modes.
        """
        command = ["exit"]
        if arg:
            command.append(arg)
        return self.run_subcommand(command)

    def do_help(self, arg):
        """ Handle help subcommand. """
        if arg:
            try:
                arg_parts = shlex.split(arg)
            except ValueError as err:
                LOG().error(str(err))
                return exit.EXIT_CODE_INVALID_SYNTAX

            method_name = '_'.join(
                itertools.chain(['do'],
                    itertools.takewhile(lambda x: not x.startswith('-'),
                                        arg_parts)))
            if hasattr(self, method_name):
                return cmd.Cmd.do_help(self, arg)
        else:
            arg_parts = []

        if (   self.on_top_level_node
           and (  not arg
               or (   len(arg_parts) == 1
                  and arg not in self.app.command_manager.command_names))):
            if not self.completenames(arg):
                LOG().error(str(errors.LmiCommandNotFound(arg)))
                cmd.Cmd.do_help(self, '')
            else:
                cmd.Cmd.do_help(self, arg)
            cmd_names = set(self.command_manager)
            cmd_names.difference_update(set(self.completenames('')))
            self.print_topics(
                    "Application commands (type help <topic>):",
                    sorted(cmd_names), 15, 80)
            self.print_topics(
                    "Built-in commands (type :help):",
                    [':'+bi for bi in BUILT_INS], 15, 80)
            return exit.EXIT_CODE_SUCCESS

        return self.run_subcommand(['help'] + arg_parts)

    def emptyline(self):   #pylint: disable=R0201
        """ Do nothing for empty line. """
        pass

    def help_exit(self):
        """ Provide help for exit command. """
        cur_node = self.app.active_command
        # temporarily change to top level command where help cmd is registered
        self.app.active_command = self._top_level_cmd
        try:
            return self.run_subcommand(["help", "exit"])
        finally:
            self.app.active_command = cur_node

    def help_help(self):
        """
        Use the command manager to get instructions for "help".
        """
        cur_node = self.app.active_command
        # temporarily change to top level command where help cmd is registered
        self.app.active_command = self._top_level_cmd
        try:
            return self.run_subcommand(["help", "help"])
        finally:
            self.app.active_command = cur_node

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

    def run_subcommand(self, args):
        """
        Run a subcommand given as a first item of ``args``. It must be one of
        commands registered in manager. Returns the return value of invoked
        command.

        :param list args: List of commands.
        """
        if not isinstance(args, (list, tuple)):
            raise TypeError("args must be a list")
        if len(args) < 1:
            raise ValueError("args must not be empty")
        try:
            cmd_factory = cmdutil.get_subcommand_factory(
                    self.app.active_command, args[0])
            parent = self.app.active_command
        except errors.LmiCommandNotFound:
            # When nested into a subcommand, let it handle the args if known.
            # If not known, try one of static commands.
            if not self.on_top_level_node and hasattr(self, 'do_' + args[0]):
                cmd_factory = self.app.command_manager.find_command(args[0])
                parent = self._top_level_cmd
            else:
                raise
        cmd_inst = cmd_factory(self.app, args[0], parent)
        return cmd_inst.run(args[1:])
