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
The base module containing the main functionality of ``lmi`` metacommand.
"""

import argparse
import logging
import pkg_resources
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.help import HelpCommand
from cliff.interactive import InteractiveApp
import lmi.lmi_client_base
from lmi.scripts import common
from lmi.scripts.common import errors
from lmi.scripts.common.command import LmiCommandMultiplexer, LmiBaseCommand
from lmi.scripts.common.configuration import Configuration
from lmi.scripts.common.session import Session

PYTHON_EGG_NAME = "lmi-scripts"
#RE_COMMAND = re.compiler(r'^[a-z_]+(?:-[a-z_]+)*$')

LOG = common.get_logger(__name__)

# ignore any message before the logging is configured
logging.getLogger('').addHandler(logging.NullHandler())

class LmiHelpCommand(HelpCommand):
    """print detailed help for another command
    """

    def take_action(self, parsed_args):
        if parsed_args.cmd:
            try:
                the_cmd = self.app.command_manager.find_command(
                    parsed_args.cmd,
                )
                cmd_factory, cmd_name, search_args = the_cmd
            except ValueError:
                # Did not find an exact match
                cmd = parsed_args.cmd[0]
                fuzzy_matches = [k[0] for k in self.app.command_manager
                                 if k[0].startswith(cmd)
                                 ]
                if not fuzzy_matches:
                    raise
                self.app.stdout.write('Command "%s" matches:\n' % cmd)
                for fm in fuzzy_matches:
                    self.app.stdout.write('  %s\n' % fm)
                return
            cmd = cmd_factory(self.app, search_args)
            full_name = (cmd_name
                         if self.app.interactive_mode
                         else ' '.join([self.app.NAME, cmd_name])
                         )
            cmd_parser = cmd.get_parser(full_name)
            self.app.stdout.write(cmd.__doc__)
            return 0
        else:
            cmd_parser = self.get_parser(' '.join([self.app.NAME, 'help']))
        cmd_parser.print_help(self.app.stdout)
        return 0

def parse_hosts_file(hosts_file):
    res = []
    for line in hosts_file.readlines():
        hostname = line.strip()
        res.append(hostname)
    return res

class MetaCommand(App):

    def __init__(self):
        lmi.lmi_client_base.LmiBaseClient._set_use_exceptions(True)
        App.__init__(self,
            "OpenLMI command line interface for CIM providers."
            " It's functionality is composed of registered subcommands,"
            " operating on top of simple libraries, interfacing with"
            " particular OpenLMI profile providers. Works also in interactive"
            " mode.",
            pkg_resources.get_distribution(PYTHON_EGG_NAME).version,
            command_manager=CommandManager('lmi.scripts.cmd'))
        self.command_manager.add_command('help', LmiHelpCommand)
        self.session = None

    def build_option_parser(self, *args, **kwargs):
        parser = App.build_option_parser(self, *args, **kwargs)
        parser.add_argument('--config-file', '-c', action='store',
                default=Configuration.USER_CONFIG_FILE_PATH,
                help="Specify the user configuration file to use. Options in"
                " this file override any settings of global configuration"
                " file located in \"%s\"." % Configuration.config_file_path())
        parser.add_argument('--user', action='store', default="",
                help="Supply a username used in each connection to target"
                " host.")
        parser.add_argument('--host', action='append', dest='hosts',
                default=[],
                help="Hostname of target system, where the command will be"
                " applied.")
        parser.add_argument('--hosts-file', type=file,
                help="Supply a path to file containing target hostnames."
                " Each hostname must be listed on single line.")
        return parser

    def run(self, argv):
        """Equivalent to the main program for the application.

        :param argv: input arguments and options
        :paramtype argv: list of str
        """
        def _debug():
            if hasattr(self, 'options'):
                return self.options.debug
            else:
                return True
        try:
            self.options, remainder = self.parser.parse_known_args(argv)
            self.configure_logging()
            self.interactive_mode = not remainder
            self.initialize_app(remainder)
        except Exception as err:
            if _debug():
                LOG().exception(err)
                raise
            else:
                LOG().error(err)
            return 1

        result = 1
        if self.interactive_mode:
            # Cmd does not provide a way to override arguments in some nice way
            sys.argv = [sys.argv[0]] + remainder
            result = self.interact()
        else:
            try:
                result = self.run_subcommand(remainder)
            except errors.LmiCommandError as exc:
                getattr(LOG(), 'exception' if _debug() else 'critical')(
                        str(exc))
                result = 1
        return result

    def prepare_to_run_command(self, cmd):
        if not isinstance(cmd, LmiHelpCommand):
            if not self.options.hosts and not self.options.hosts_file:
                self.parser.error(
                        "missing one of (host | hosts-file) arguments")
            hosts = []
            if self.options.hosts_file:
                hosts.extend(parse_hosts_file(self.options.hosts_file))
            hosts.extend(self.options.hosts)
            credentials = {h: (self.options.user, '') for h in hosts}
            if self.session is None:
                self.session = Session(self, hosts, credentials)

    def run_subcommand(self, argv):
        subcommand = self.command_manager.find_command(argv)
        cmd_factory, cmd_name, sub_argv = subcommand
        cmd = cmd_factory(self, self.options)
        err = None
        result = 1
        try:
            self.prepare_to_run_command(cmd)
            full_name = (cmd_name
                         if self.interactive_mode
                         else ' '.join([self.NAME, cmd_name])
                         )
            cmd_parser = cmd.get_parser(full_name)
            if isinstance(cmd, LmiBaseCommand):
                if cmd.is_end_point():
                    parsed_args = cmd_parser.parse_args(sub_argv)
                    result = cmd.run(self.session, parsed_args)
                else:
                    parsed_args, unknown = cmd_parser.parse_known_args(sub_argv)
                    result = cmd.run(self.session, parsed_args, unknown)
            else:
                parsed_args = cmd_parser.parse_args(sub_argv)
                result = cmd.run(parsed_args)
            
        except Exception as err:
            if self.options.debug:
                LOG().exception(err)
            else:
                LOG().error(err)
            try:
                self.clean_up(cmd, result, err)
            except Exception as err2:
                if self.options.debug:
                    LOG().exception(err2)
                else:
                    LOG().error('Could not clean up: %s', err2)
            if self.options.debug:
                raise
        else:
            try:
                self.clean_up(cmd, result, None)
            except Exception as err3:
                if self.options.debug:
                    LOG().exception(err3)
                else:
                    LOG().error('Could not clean up: %s', err3)
        return result

    def configure_logging(self):
        # first instantiation of Configuration object
        config = Configuration.get_instance(self.options.config_file)
        config.verbosity = self.options.verbose_level
        root_logger = logging.getLogger('')
        # make a reference to null handlers (one should be installed)
        null_handlers = [  h for h in root_logger.handlers
                        if isinstance(h, logging.NullHandler)]
        try:
            logging_level = getattr(logging, config.logging_level.upper())
        except KeyError:
            logging_level = logging.ERROR

        # Set up logging to a file
        log_file = self.options.log_file
        if log_file is None:
            log_file = config.get_safe('Log', 'OutputFile')
        if log_file is not None:
            file_handler = logging.FileHandler(filename=log_file)
            formatter = logging.Formatter(
                    config.get_safe('Log', 'FileFormat',
                        fallback=self.LOG_FILE_MESSAGE_FORMAT,
                        raw=True))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # Always send higher-level messages to the console via stderr
        console = logging.StreamHandler(self.stderr)
        console_level_default = logging.ERROR if log_file else logging_level
        console_level = {
                Configuration.OUTPUT_SILENT  : logging.CRITICAL,
                Configuration.OUTPUT_WARNING : logging.WARNING,
                Configuration.OUTPUT_INFO    : logging.INFO,
                Configuration.OUTPUT_DEBUG   : logging.DEBUG,
            }.get(config.verbosity, console_level_default)
        console.setLevel(console_level)
        formatter = logging.Formatter(
                config.get_safe('Log', 'ConsoleFormat',
                    fallback=self.CONSOLE_MESSAGE_FORMAT))
        console.setFormatter(formatter)
        root_logger.addHandler(console)
        root_logger.setLevel(min(logging_level, console_level))

        # remove all null_handlers
        for handler in null_handlers:
            root_logger.removeHandler(handler)
        return

def main(argv=sys.argv[1:]):
    mc = MetaCommand()
    return mc.run(argv)

