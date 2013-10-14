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
Module defining the root command (``lmi`` binary).
"""

USAGE_STRING = \
"""
OpenLMI command line interface for CIM providers. It's functionality is
composed of registered subcommands, operating on top of simple libraries,
interfacing with particular OpenLMI profile providers.
Works also in interactive mode which is entered, when <command> argument is
omitted.

Usage:
    %(cmd)s [options] [(--trace | --notrace)] [-v]... [-h <host>]...
        <command> [<args> ...]
    %(cmd)s [options] [(--trace | --notrace)] [-v]... [-h <host>]...
    %(cmd)s (--help | --version)

Options:
    -c --config-file <config>  Path to a user configuration file. Options
                               specified here override any settings of global
                               configuration file.
    -h --host <host>           Hostname of target system.
    --hosts-file <hosts>       Path to a file containing target hostnames.
                               Each hostname must be listed on a single line.
    --user <user>              Username used in connection to any target host.
    --same-credentials         Use the first credentials given for all hosts.
    -n --noverify              Do not verify cimom's ssl certificate.
    -v                         Increase verbosity of output.
    --trace                    Show tracebacks on errors.
    --notrace                  Suppress tracebacks for exceptions.
    -q --quiet                 Supress output except for errors.
    --log-file <log_file>      Output file for logging messages.
    --namespace <namespace>    Default CIM namespace to use.
    -N --no-headings           Don't print table headings.
    -H --human-friendly        Print large values in human friendly units (i.e.
                               MB, GB, TB etc.)
    -L --lister-format (table | csv)
                               Print output of lister commands in CSV or table
                               format. CSV format is more suitable for machine
                               processing. Defaults to table.
    --help                     Show this text and quit.
    --version                  Print version of '%(cmd)s' in use and quit.

Handling hosts:
    If no --host or --hosts-file given the "localhost" is tried. When running
    under root with Pegasus CIMOM, this results in a connection over unix
    socket (without the need for credentials).

    Hosts may contain embedded credentials e.g.:
        http://user:passwd@hostname:5988
    Avoid supplying them on command line though since arguments are visible in
    process table. Use --hosts-file option instead.
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
        return USAGE_STRING % { 'cmd' : self.cmd_full_name }

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

