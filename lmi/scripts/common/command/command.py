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
Module with abstractions for representing subcommand of lmi meta-command.
"""

import abc
import argparse
import inspect
import re
from cliff.command import Command
from cliff.lister import Lister
from cliff.show import ShowOne
from docopt import docopt

import lmi.lmi_client_base
from lmi.scripts.common import Configuration
from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common.command import meta
from lmi.scripts.common.command.base import LmiBaseCommand

RE_OPT_BRACKET_ARGUMENT = re.compile('^<(?P<name>[^>]+)>$')
RE_OPT_UPPER_ARGUMENT = re.compile('^(?P<name>[A-Z]+(?:[_-][A-Z]+)*)$')
RE_OPT_SHORT_OPTION = re.compile('^-(?P<name>[a-z])$', re.IGNORECASE)
RE_OPT_LONG_OPTION = re.compile('^--(?P<name>[a-z_-]+)$', re.IGNORECASE)

LOG = get_logger(__name__)

def _row_to_string(tup):
    return tuple(str(a) for a in tup)

def opt_name_sanitize(opt_name):
    return re.sub(r'[^a-zA-Z]', '_', opt_name).lower()

def options_dict2kwargs(options):
    """
    Convert option name from resulting docopt dictionary to a valid python
    identificator token used as function argument name.

    :param options: (``dict``) Dictionary return by docopt call.
    :rtype: (``dict``) New dictionary with keys passeable to function
        as argument names.
    """
    # (new_name, value) for each pair in options dictionary
    kwargs = {}
    # (name 
    orig_names = {}
    for name, value in options.items():
        for (reg, func) in (
                (RE_OPT_BRACKET_ARGUMENT, lambda m: m.group('name')),
                (RE_OPT_UPPER_ARGUMENT,   lambda m: m.group('name')),
                (RE_OPT_SHORT_OPTION,     lambda m: m.group(0)),
                (RE_OPT_LONG_OPTION,      lambda m: m.group(0))):
            match = reg.match(name)
            if match:
                new_name = func(match)
                break
        else:
            if meta.RE_COMMAND_NAME:
                LOG().warn('command "%s" is missing implementation' % name)
                continue
            raise errors.LmiError(
                    'failed to convert argument "%s" to function option'
                    % name)
        new_name = opt_name_sanitize(new_name)
        if new_name in kwargs:
            raise errors.LmiError('option clash for "%s" and "%s", which both'
                ' translate to "%s"' % (name, orig_names[new_name], new_name))
        kwargs[new_name] = value
        orig_names[new_name] = name
    return kwargs

class LmiCommandMultiplexer(LmiBaseCommand, Command):
    __metaclass__ = meta.MultiplexerMetaClass

    @classmethod
    def is_end_point(cls):
        return False

    @classmethod
    def get_commands(cls):
        raise NotImplementedError("get_commands method must be overriden in"
                " a subclass")

    def __init__(self, *args, **kwargs):
        LmiBaseCommand.__init__(self, args, kwargs)
        Command.__init__(self, *args, **kwargs)

    def get_parser(self, cmd_name_args):
        self.cmd_name_args = cmd_name_args
        parser = argparse.ArgumentParser(
                description=self.get_description(),
                prog=self.cmd_full_name,
                add_help=False)
        subparser = parser.add_subparsers(dest='command')
        for cmd in self.get_commands():
            subparser.add_parser(cmd)
        return parser

    def make_options(self, subcmd_name, unknown_args):
        full_args = self.docopt_cmd_name_args
        full_args.append(subcmd_name)
        full_args.extend(unknown_args)
        options = docopt(self.__doc__, full_args)
        for scn in self.get_commands():
            try:
                del options[scn]
            except KeyError:
                LOG().warn('doc string of "%s" command does not contain'
                        ' registered command "%s" command',
                        subcmd_name, scn)
        # remove also this command from options
        if self.cmd_name in options:
            del options[self.cmd_name]
        return options

    def take_action(self, session, args, unknown_args):
        for cmd_name, cmd_cls in self.get_commands().items():
            if cmd_name == args.command:
                cmd = cmd_cls(self.app, self.app_args, parent=self)
                subcmd_args = self.cmd_name_args + [cmd_name]
                cmd_parser = cmd.get_parser(subcmd_args)
                parsed_args, remainder = cmd_parser.parse_known_args(
                        unknown_args)
                if cmd.is_end_point():
                    options = self.make_options(cmd_name, remainder)
                    return cmd.run(session, parsed_args, options)
                else:
                    return cmd.run(session, parsed_args, remainder)
        # this won't happen if checks are done correctly
        LOG().critical('unexpected command "%s"', args.command)
        raise errors.LmiCommandNotFound(args.command)

    def run(self, session, parsed_args, unknown_args):
        self.take_action(session, parsed_args, unknown_args)
        return 0

class LmiEndPointCommand(LmiBaseCommand):

    @abc.abstractmethod
    def process_session(self, session, cmd_args, options):
        raise NotImplementedError("process_session must be overriden"
                " in subclass")

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError("execute method must be overriden"
                " in subclass")

    def _make_end_point_args(self, options):
        argspec = inspect.getargspec(self.execute.dest)
        kwargs = options_dict2kwargs(options)
        to_remove = []
        if argspec.keywords is None:
            for opt_name in kwargs:
                if opt_name not in argspec.args[1:]:
                    LOG().debug('option "%s" not handled in function "%s",'
                        ' ignoring', opt_name, self.cmd_name)
                    to_remove.append(opt_name)
        for opt_name in to_remove:
            del kwargs[opt_name]
        args = []
        for arg_name in argspec.args[1:]:
            if arg_name not in kwargs:
                raise errors.LmiCommandError(
                    self.__module__, self.__class__.__name__,
                    'registered command "%s" expects option "%s", which'
                    ' is not covered in usage string'
                    % (self.cmd_name, arg_name))
            args.append(kwargs.pop(arg_name))
        return args, kwargs

    def verify_options(self, _options):
        pass

    def transform_options(self, options):
        return options

    def get_parser(self, cmd_name_args):
        cls = self.__class__
        parser = None
        self.cmd_name_args = cmd_name_args
        while cls:
            cmd_bases = tuple(c for c in cls.__bases__
                    if issubclass(c, Command))
            not_end_point_bases = tuple(c for c in cmd_bases
                    if not issubclass(c, LmiEndPointCommand))
            if len(not_end_point_bases) > 0:
                parser = not_end_point_bases[0].get_parser(self,
                        self.cmd_full_name)
                break
            cls = cmd_bases[0]
        return parser

    def run(self, session, cmd_args, options):
        self.verify_options(options)
        options = self.transform_options(options)
        args, kwargs = self._make_end_point_args(options)
        return self.process_session(session, cmd_args, args, kwargs)

class LmiLister(LmiEndPointCommand, Lister):
    __metaclass__ = meta.ListerMetaClass

    def __init__(self, *args, **kwargs):
        LmiEndPointCommand.__init__(self, args, kwargs)
        Lister.__init__(self, *args, **kwargs)

    @classmethod
    def get_columns(cls):
        return None

    def take_action(self, connection, function_args, function_kwargs):
        res = self.execute(connection, *function_args, **function_kwargs)
        columns = self.get_columns()
        if columns is None:
            # let's get columns from the first row
            columns = next(res)
        return (_row_to_string(columns), res)

    def process_session(self, session, cmd_args, function_args,
            function_kwargs):
        self.formatter = self.formatters[cmd_args.formatter]
        for connection in session:
            if len(session) > 1:
                self.app.stdout.write("="*79 + "\n")
                self.app.stdout.write("Host: %s\n" % connection.hostname)
                self.app.stdout.write("="*79 + "\n")
            column_names, data = self.take_action(
                    connection, function_args, function_kwargs)
            self.produce_output(cmd_args, column_names, data)
            if len(session) > 1:
                self.app.stdout.write("\n")
        return 0

class LmiShowInstance(LmiEndPointCommand, ShowOne):
    __metaclass__ = meta.ShowInstanceMetaClass

    def __init__(self, *args, **kwargs):
        LmiEndPointCommand.__init__(self, args, kwargs)
        ShowOne.__init__(self, *args, **kwargs)

    @abc.abstractmethod
    def render(self, result):
        raise NotImplementedError(
                "render method must be overriden in subclass")

    def take_action(self, connection, function_args, function_kwargs):
        res = self.execute(connection, *function_args, **function_kwargs)
        return self.render(res)

    def process_session(self, session, cmd_args, function_args,
            function_kwargs):
        self.formatter = self.formatters[cmd_args.formatter]
        failures = []
        for connection in session:
            if len(session) > 1:
                self.app.stdout.write("="*79 + "\n")
                self.app.stdout.write("Host: %s\n" % connection.hostname)
                self.app.stdout.write("="*79 + "\n")
            try:
                column_names, data = self.take_action(
                        connection, function_args, function_kwargs)
                self.produce_output(cmd_args, column_names, data)
            except Exception as exc:
                if self.app.options.debug:
                    LOG().exception('show instance failed for host "%s"',
                            connection.hostname)
                else:
                    LOG().error('show instance failed for host "%s": %s',
                            connection.hostname, exc)
                failures.append((connection.hostname, exc))
            if len(session) > 1:
                self.app.stdout.write("\n")
        if len(failures) > 0:
            self.app.stdout.write('There were %d unsuccessful runs on hosts:\n'
                    % len(failures))
            lister = LmiLister(self.app, self.app_args)
            lister.formatter = self.formatters['table']
            lister.produce_output(
                    cmd_args, ('Host', 'Error'), failures)
        return 0

class LmiCheckResult(LmiEndPointCommand, Lister):
    __metaclass__ = meta.CheckResultMetaClass

    def __init__(self, *args, **kwargs):
        LmiEndPointCommand.__init__(self, args, kwargs)
        Lister.__init__(self, *args, **kwargs)
        self.result = None

    @abc.abstractmethod
    def check_result(self, options, result):
        raise NotImplementedError("check_result must be overriden in subclass")

    def take_action(self, connection, function_args, function_kwargs):
        try:
            res = self.execute(connection, *function_args, **function_kwargs)
            return (self.check_result(function_args, res), None)
        except Exception as exc:
            if self.app.options.debug:
                LOG().exception("failed to execute wrapped function")
            else:
                LOG().warn("failed to execute wrapped function: %s", exc)
            return (False, exc)

    def process_session(self, session, cmd_args, function_args,
            function_kwargs):
        self.formatter = self.formatters[cmd_args.formatter]
        # first list contain passed hosts, the second one failed ones
        results = ([], [])
        for connection in session:
            passed, error = self.take_action(
                    connection, function_args, function_kwargs)
            results[0 if passed else 1].append((connection.hostname, error))
            if not passed and error:
                LOG().warn('invocation failed on host "%s": %s',
                        connection.hostname, error)
                if Configuration.get_instance().verbosity >= \
                        Configuration.OUTPUT_DEBUG:
                    self.app.stdout.write('invocation failed on host "%s":'
                            ' %s\n"' % (connection.hostname, str(error)))
        if Configuration.get_instance().verbosity >= \
                Configuration.OUTPUT_INFO:
            self.app.stdout.write('Successful runs: %d\n' % len(results[0]))
        failed_runs = len(results[1]) + len(session.get_unconnected())
        if failed_runs:
            self.app.stdout.write('There were %d unsuccessful runs on hosts:\n'
                    % failed_runs)
            self.formatter = self.formatters['table']
            data = []
            for hostname in session.get_unconnected():
                data.append((hostname, 'failed to connect'))
            for hostname, error in results[1]:
                if error is None:
                    error = "failed"
                    if (  Configuration.get_instance().verbosity
                       >= Configuration.OUTPUT_INFO
                       and hasattr(self.check_result, 'expected')):
                        error = error + (" (%s != %s)" % (
                            self.check_result.expected, self.result))
                data.append((hostname, error))
            self.produce_output(cmd_args, ('Name', 'Error'), data)

