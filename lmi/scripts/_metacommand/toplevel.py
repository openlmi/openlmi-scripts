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
OpenLMI command line interface for CIM providers. It's functionality is
composed of registered subcommands, operating on top of simple libraries,
interfacing with particular OpenLMI profile providers. Works also in
interactive mode. It's entered, when <command> argument is ommited.

Usage:
    %(cmd)s [options] [-v]... [-h <host>]... <command> [<args> ...]
    %(cmd)s [options] [-v]... [-h <host>]...
    %(cmd)s (--help | --version)

Options:
    -c --config-file <config> Path to a user configuration file. Options
                              specified here override any settings of global
                              configuration file.
    -h --host <host>          Hostname of target system.
    --hosts-file <hosts>      Path to a file containing target hostnames.
                              Each hostname must be listed on a single line.
    --user <user>             Username used in connection to any target host.
    -v                        Increase verbosity of output.
    --trace                   Show tracebacks on errors.
    -q --quiet                Supress output except for errors.
"""

import docopt

from lmi.scripts._metacommand import util
from lmi.scripts._metacommand import Interactive
from lmi.scripts._metacommand.exit import Exit
from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common.command import base

LOG = get_logger(__name__)

class TopLevelCommand(base.LmiBaseCommand):
    """
    Top level (instance, without any parent) command handling application
    parameters and passing work to registered subcommands.
    """

    @classmethod
    def has_own_usage(cls):
        return True

    @classmethod
    def child_commands(cls):
        return []

    def __init__(self, app, cmd_name='lmi'):
        base.LmiBaseCommand.__init__(self, app, cmd_name)

    def get_usage(self, _proper=False):
        return __doc__ % { 'cmd' : self.cmd_full_name }

    def run_subcommand(self, cmd_name, args):
        """
        Finds a command factory, instantiates it and passes the control.
        """
        cmd_factory = self.app.command_manager[cmd_name]
        cmd = cmd_factory(self.app, cmd_name, parent=self)
        return cmd.run(args)

    def start_interactive_mode(self):
        """ Run the command line loop of interactive application. """
        self.app.command_manager.add_command("exit", Exit)
        iapp = Interactive(self.app, self.cmd_name + "> ")
        try:
            return iapp.cmdloop()
        except errors.LmiTerminate as err:
            return err.args[0]

    def run(self, args):
        """
        Handle program arguments, set up the application and call
        a subcommand or enter interactive mode. Return exit code.

        :param args: (``list``) Arguments without the binary name.
        """
        if not isinstance(args, (tuple, list)):
            raise TypeError("args must be a list")
        try:
            options = docopt.docopt(self.get_usage(), args,
                    version=util.get_version(), help=False, options_first=True)
        except docopt.DocoptLanguageError as exc:
            self.app.stderr.write("%s\n" % str(exc))
            return 1
        if options.pop('--help', False):
            self.app.stdout.write(self.get_usage())
            self.app.stdout.write("\nCommands:\n")
            self.app.stdout.write("    %s\n" % " ".join(
                n for n in sorted(self.app.command_manager)))
            return 0
        if options.pop('--version', False):
            self.app.print_version()
            return 0
        self.app.setup(options)
        if options['<command>'] is None:
            return self.start_interactive_mode()
        else:
            LOG().debug('running command "%s"', options['<command>'])
            return self.run_subcommand(
                    options['<command>'], options['<args>'])

