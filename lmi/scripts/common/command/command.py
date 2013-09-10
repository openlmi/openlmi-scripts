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
Module with abstractions for representing subcommand of lmi meta-command.
"""

import abc
import inspect
import re
from docopt import docopt

from lmi.shell import LMIUtil
from lmi.shell import LMIConnection
from lmi.scripts.common import Configuration
from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common import formatter
from lmi.scripts.common.session import Session
from lmi.scripts.common.command import base
from lmi.scripts.common.command import meta
from lmi.scripts.common.command import util

LOG = get_logger(__name__)

def opt_name_sanitize(opt_name):
    """
    Make a function parameter name out of option name. This replaces any
    character not suitable for python identificator with ``'_'`` and
    make the whole string lowercase.

    :param string opt_name: Option name.
    :returns: Modified option name.
    :rtype: string
    """
    return re.sub(r'[^a-zA-Z]+', '_', opt_name).lower()

def options_dict2kwargs(options):
    """
    Convert option name from resulting ``docopt`` dictionary to a valid python
    identificator token used as function argument name.

    :param dictionary options: Dictionary returned by docopt call.
    :returns:  New dictionary with keys passable to function as argument
        names.
    :rtype: dictionary
    """
    # (new_name, value) for each pair in options dictionary
    kwargs = {}
    # (new_name, name)
    orig_names = {}
    for name, value in options.items():
        for (reg, func) in (
                (util.RE_OPT_BRACKET_ARGUMENT, lambda m: m.group('name')),
                (util.RE_OPT_UPPER_ARGUMENT,   lambda m: m.group('name')),
                (util.RE_OPT_SHORT_OPTION,     lambda m: m.group(0)),
                (util.RE_OPT_LONG_OPTION,      lambda m: m.group(0)),
                (base.RE_COMMAND_NAME,         lambda m: m.group(0))):
            match = reg.match(name)
            if match:
                new_name = func(match)
                break
        else:
            raise errors.LmiError(
                    'failed to convert argument "%s" to function option' %
                    name)
        new_name = opt_name_sanitize(new_name)
        if new_name in kwargs:
            raise errors.LmiError('option clash for "%s" and "%s", which both'
                ' translate to "%s"' % (name, orig_names[new_name], new_name))
        kwargs[new_name] = value
        orig_names[new_name] = name
    return kwargs

class LmiCommandMultiplexer(base.LmiBaseCommand):
    """
    Base class for node commands. It consumes just part of command line
    arguments and passes the remainder to one of its subcommands.

    Example usage: ::

        class MyCommand(LmiCommandMultiplexer):
            '''
            My command description.

            Usage: %(cmd)s mycommand (subcmd1 | subcmd2)
            '''
            COMMANDS = {'subcmd1' : Subcmd1, 'subcmd2' : Subcmd2}

    Where ``Subcmd1`` and ``Subcmd2`` are some other ``LmiBaseCommand``
    subclasses. Documentation string must be parseable with ``docopt``.

    ``COMMANDS`` property will be translated to
    :py:meth:`LmiCommandMultiplexer.child_commands` class method by
    :py:class:`lmi.scripts.common.command.meta.MultiplexerMetaClass`.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.MultiplexerMetaClass`.
    """
    __metaclass__ = meta.MultiplexerMetaClass

    @classmethod
    def child_commands(cls):
        """
        Abstract class method, that needs to be implemented in subclass.
        This is done by associated meta-class, when defining a command with
        assigned ``COMMANDS`` property.

        :returns: Dictionary of subcommand names with assigned command
            factories.
        :rtype: dictionary
        """
        raise NotImplementedError("child_commands must be implemented in"
                " a subclass")
    @classmethod
    def is_end_point(cls):
        return False

    def run_subcommand(self, cmd_name, args):
        """
        Pass control to a subcommand identified by given name.

        :param string cmd_name: Name of direct subcommand, whose
            :py:meth:`lmi.scripts.common.command.base.LmiBaseCommand.run`
            method shall be invoked.
        :param list args: List of arguments for particular subcommand.
        :returns: Application exit code.
        :rtype: integer
        """
        if not isinstance(cmd_name, basestring):
            raise TypeError("cmd_name must be a string, not %s" %
                    repr(cmd_name))
        if not isinstance(args, (list, tuple)):
            raise TypeError("args must be a list, not %s" % repr(args))
        try:
            cmd_cls = self.child_commands()[cmd_name]
            cmd = cmd_cls(self.app, cmd_name, self)
        except KeyError:
            self.app.stderr.write(self.get_usage())
            LOG().critical('unexpected command "%s"', cmd_name)
            return 1
        return cmd.run(args)

    def run(self, args):
        """
        Handle optional parameters, retrieve desired subcommand name and
        pass the remainder of arguments to it.

        :param list args: List of arguments with at least subcommand name.
        """
        if not isinstance(args, (list, tuple)):
            raise TypeError("args must be a list")
        full_args = self.cmd_name_args[1:] + args
        # check the --help ourselves (the default docopt behaviour checks
        # also for --version)
        docopt_kwargs = {
                'help' : False,
                # let's ignore options following first command for generated
                # usage string
                'options_first' : not self.has_own_usage()
        }
        options = docopt(self.get_usage(), full_args, **docopt_kwargs)
        if options.pop('--help', False):
            self.app.stdout.write(self.get_usage())
            return 0
        return self.run_subcommand(args[0], args[1:])

class LmiEndPointCommand(base.LmiBaseCommand):
    """
    Base class for any leaf command.

    List of additional recognized properties:

        ``CALLABLE`` : ``tuple``
            Associated function. Will be wrapped in
            :py:meth:`LmiEndPointCommand.execute` method and will be accessible
            directly as a ``cmd.execute.dest`` property. It may be specified
            either as a string in form ``"<module_name>:<callable>"`` or as a
            reference to callable itself.
        ``ARG_ARRAY_SUFFIX`` : ``str``
            String appended to every option parsed by ``docopt`` having list as
            an associated value. It defaults to empty string. This modification
            is applied before calling
            :py:meth:`LmiEndPointCommand.verify_options` and
            :py:meth:`LmiEndPointCommand.transform_options`.
        ``FORMATTER`` : callable
            Default formatter factory for instances of given command. This
            factory accepts an output stream as the only parameter and returns
            an instance of :py:class:`lmi.scripts.common.formatter.Formatter`.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.EndPointCommandMetaClass`.
    """
    __metaclass__ = meta.EndPointCommandMetaClass

    def __init__(self, *args, **kwargs):
        super(LmiEndPointCommand, self).__init__(*args, **kwargs)
        self._formatter = None
        # saved options dictionary after call to transform_options()
        self._options = None

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        """
        Subclasses must override this method to pass given arguments to
        command library function. This function shall be specified in
        ``CALLABLE`` property.
        """
        raise NotImplementedError("execute method must be overriden"
                " in subclass")

    def formatter_factory(self):
        """
        Subclasses shall override this method to provide default formatter
        factory for printing output.

        :returns: Subclass of basic formatter.
        """
        return formatter.Formatter

    @classmethod
    def dest_pos_args_count(cls):
        """
        Number of positional arguments the associated function takes from
        command. These arguments are created by the command alone -- they do
        not belong to options in usage string. Function can take additional
        positional arguments that need to be covered by usage string.

        :rtype: integer
        """
        dest = getattr(cls.execute, "dest", cls.execute)
        abstract = dest == cls.execute and util.is_abstract_method(
                cls, 'execute', True)
        # if the destination function is not yet defined (abstract is True)
        # let's assume it's not a method => 0 positional arguments needed
        return 1 if not abstract and inspect.ismethod(dest) else 0

    def run_with_args(self, args, kwargs):
        """
        Process end-point arguments and exit.

        :param list args: Positional arguments to pass to associated
            function in command library.
        :param dictionary kwargs: Keyword arguments as a dictionary.
        :returns: Exit code of application.
        :rtype: integer
        """
        self.execute(*args, **kwargs)

    @property
    def formatter(self):
        """
        Return instance of default formatter.

        :rtype: :py:class:`lmi.scripts.common.formatter.Formatter`
        """
        if self._formatter is None:
            self._formatter = self.formatter_factory()(
                    self.app.stdout, no_headings=self.app.config.no_headings)
        return self._formatter

    def _make_end_point_args(self, options):
        """
        Creates a pair of positional and keyword arguments for a call to
        associated function from command line options. All keyword
        options not expected by target function are removed.

        :param dictionary options: Output of ``docopt`` parser.
        :returns: Positional and keyword arguments as a pair.
        :rtype: tuple
        """
        # if execute method does not have a *dest* attribute, then it's
        # itself a destination
        dest = getattr(self.execute, "dest", self.execute)
        argspec = inspect.getargspec(dest)
        kwargs = options_dict2kwargs(options)
        # number of positional arguments not covered by usage string
        pos_args_count = self.dest_pos_args_count()
        to_remove = []
        # if associated function takes keyword arguments in a single
        # dictionary (kwargs), we can pass all options
        if argspec.keywords is None:
            # otherwise we need to remove any unhandled
            for opt_name in kwargs:
                if opt_name not in argspec.args[pos_args_count:]:
                    LOG().debug('option "%s" not handled in function "%s",'
                        ' ignoring', opt_name, self.cmd_name)
                    to_remove.append(opt_name)
        for opt_name in to_remove:
            # remove options unhandled by function
            del kwargs[opt_name]
        args = []
        for arg_name in argspec.args[pos_args_count:]:
            if arg_name not in kwargs:
                raise errors.LmiCommandError(
                    self.__module__, self.__class__.__name__,
                    'registered command "%s" expects option "%s", which'
                    ' is not covered in usage string'
                    % (self.cmd_name, arg_name))
            args.append(kwargs.pop(arg_name))
        return args, kwargs

    def _preprocess_options(self, options):
        """
        This method may be overriden by
        :py:class:`lmi.scripts.common.command.meta.EndPointCommandMetaClass`
        as a result of processing ``ARG_ARRAY_SUFFIX`` and other properties
        modifying names of parsed options.

        This should not be overriden in command class's body.

        :param dictionary options: The result of ``docopt`` parser invocation
            which can be modified by this method.
        """
        pass

    def _parse_args(self, args):
        """
        Run ``docopt`` command line parser on given list of arguments.
        Removes all unrelated commands from created dictionary of options.

        :param list args: List of command line arguments just after the
            current command.
        :returns: Dictionary with parsed options. Please refer to
            docopt_ documentation for more informations.
        :rtype: dictionary

        .. _docopt: http://docopt.org/
        """
        full_args = self.cmd_name_args[1:] + args
        options = docopt(self.get_usage(), full_args, help=False)
        self._preprocess_options(options)

        # remove all command names from options
        cmd = self.parent
        while cmd is not None and not cmd.has_own_usage():
            cmd = cmd.parent
        if cmd is not None:
            for scn in cmd.child_commands():
                try:
                    del options[scn]
                except KeyError:
                    LOG().warn('usage string of "%s.%s" command does not'
                            ' contain registered command "%s" command',
                            cmd.__module__, cmd.__class__.__name__, scn)
        # remove also the root command name from options
        if cmd is not None and cmd.cmd_name in options:
            del options[cmd.cmd_name]
        return options

    def verify_options(self, options):
        """
        This method can be overriden in subclasses to check, whether the
        options given on command line are valid. If any flaw is discovered, an
        :py:exc:`lmi.scripts.common.errors.LmiInvalidOptions` exception shall
        be raised. Any returned value is ignored.
        
        .. note::
            This is run before :py:meth:`transform_options()` method.

        :param dictionary options: Dictionary as returned by ``docopt`` parser.
        """
        pass

    def transform_options(self, options):
        """
        This method can be overriden in subclasses if options shall be somehow
        modified before passing them associated function.
        
        .. note::
            Run after :py:meth:`verify_options()` method.

        :param dictionary options: Dictionary as returned by ``docopt`` parser.
        """
        pass

    def produce_output(self, data):
        """
        This method can be use to render and print results with default
        formatter.

        :param data: Is an object expected by the
            :py:meth:`lmi.scripts.common.formatter.Formatter.produce_output`
            method of formatter.
        """
        self.formatter.produce_output(data)

    def run(self, args):
        """
        Create options dictionary from input arguments, verify them,
        transform them, make positional and keyword arguments out of them and
        pass them to ``process_session()``.

        :param list args: List of command arguments.
        :returns: Exit code of application.
        :rtype: integer
        """
        options = self._parse_args(args)
        self.verify_options(options)
        self.transform_options(options)
        self._options = options.copy()
        args, kwargs = self._make_end_point_args(options)
        return self.run_with_args(args, kwargs)

    def _print_errors(self, errors):
        """
        Print list of errors.
        Each error is a ``tuple``: ::

            (hostname, error_text)

        :param list errors: Errors to print.
        """
        fmt = formatter.TableFormatter(self.app.stderr,
                no_headings=self.app.config.no_headings)
        command1 = formatter.NewTableCommand(
                "There were %d errors" % len(errors))
        command2 = formatter.NewTableHeaderCommand(("Host", "Error"))
        fmt.produce_output((command1, command2))
        fmt.produce_output(errors)

class LmiSessionCommand(LmiEndPointCommand):
    """
    Base class for end-point commands operating upon a session object.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.SessionCommandMetaClass`.
    """
    __metaclass__ = meta.SessionCommandMetaClass

    @classmethod
    def cim_namespace(cls):
        """
        This returns default cim namespace, the connection object will be
        nested into before being passed to associated function.
        It can be overriden in few ways:

            1. by setting ``[CIM] Namespace`` option in configuration
            2. by giving ``--namespace`` argument on command line to the
               ``lmi`` meta-command
            3. by setting ``NAMESPACE`` property in declaration of command

        Higher number means higher priority.
        """
        return Configuration.get_instance().namespace

    @classmethod
    def dest_pos_args_count(cls):
        """
        There is a namespace/connection object passed as the first positional
        argument.
        """
        return LmiEndPointCommand.dest_pos_args_count.im_func(cls) + 1

    @abc.abstractmethod
    def process_session(self, session, args, kwargs):
        """
        Process each host of given session, call the associated command
        function, collect results and print it to standard output.

        This shall be overriden by a subclass.

        :param session: Session object with set of hosts.
        :type session: :py:class:`lmi.scripts.common.session.Session`
        :param list args: Positional arguments to pass to associated function
            in command library.
        :param dictionary kwargs: Keyword arguments as a dictionary.
        :returns: Exit code of application.
        :rtype: integer
        """
        raise NotImplementedError("process_session must be overriden"
                " in subclass")

    def execute_on_connection(self, connection, *args, **kwargs):
        if not isinstance(connection, LMIConnection):
            raise TypeError("expected an instance of LMIConnection for"
                    " connection argument, not %s" % repr(connection))
        namespace = self.cim_namespace()
        if namespace is not None:
            connection = LMIUtil.lmi_wrap_cim_namespace(
                    connection, namespace)
        return self.execute(connection, *args, **kwargs)

    def run_with_args(self, args, kwargs):
        self.process_session(self.app.session, args, kwargs)

class LmiBaseListerCommand(LmiSessionCommand):

    @classmethod
    def get_columns(cls):
        """
        :returns: Column names for resulting table. ``COLUMNS`` property
            will be converted to this class method. If ``None``, the associated
            function shall return column names as the first tuple of returned
            list.
        :rtype: list or None
        """
        return None

    def formatter_factory(self):
        if self.app.config.lister_format == Configuration.LISTER_FORMAT_CSV:
            return formatter.CsvFormatter
        else:
            return formatter.TableFormatter

    @abc.abstractmethod
    def take_action(self, connection, args, kwargs):
        """
        Collects results of single host.

        :param  connection: Connection to a single host.
        :type connection: :py:class:`lmi.shell.LMIConnection`
        :param list args: Positional arguments for associated function.
        :param dictionary kwargs: Keyword arguments for associated function.
        :returns: Column names and item list as a pair.
        :rtype: tuple
        """
        raise NotImplementedError("take_action must be implemented in subclass")

    def process_session(self, session, args, kwargs):
        if not isinstance(session, Session):
            raise TypeError("session must be an object of Session, not %s"
                    % repr(session))
        for connection in session:
            if len(session) > 1:
                command = formatter.NewHostCommand(connection.hostname)
                self.produce_output((command,))
            data = self.take_action(connection, args, kwargs)
            self.produce_output(data)
            if len(session) > 1:
                self.app.stdout.write("\n")
        return 0

class LmiLister(LmiBaseListerCommand):
    """
    End point command outputting a table for each host. Associated function
    shall return a list of rows. Each row is represented as a tuple holding
    column values.

    List of additional recognized properties:

        ``COLUMNS`` : ``tuple``
            Column names. It's a tuple with name for each column. Each row
            shall then contain the same number of items as this tuple. If
            omitted, associated function is expected to provide them in the
            first row of returned list. It's translated to ``get_columns()``
            class method.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.ListerMetaClass`.
    """
    __metaclass__ = meta.ListerMetaClass

    def take_action(self, connection, args, kwargs):
        """
        Collects results of single host.

        :param connection:  Connection to a single host.
        :type connection: :py:class:`lmi.shell.LMIConnection`
        :param list args: Positional arguments for associated function.
        :param dictionary kwargs: Keyword arguments for associated function.
        :returns: Column names and item list as a pair.
        :rtype: tuple
        """
        res = self.execute_on_connection(connection, *args, **kwargs)
        columns = self.get_columns()
        if columns is not None:
            command = formatter.NewTableHeaderCommand(columns)
            self.formatter.produce_output((command,))
        return res

class LmiInstanceLister(LmiBaseListerCommand):
    """
    End point command outputting a table of instances for each host.
    Associated function shall return a list of instances. They may be
    prepended with column names depending on value of ``DYNAMIC_PROPERTIES``.
    Each instance will occupy single row of table with property values being a
    content of cells.

    List of additional recognized properties is the same as for
    :py:class:`LmiShowInstance`. There is just one difference. Either
    ``DYNAMIC_PROPERTIES`` must be ``True`` or ``PROPERTIES`` must be filled.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.InstanceListerMetaClass`.
    """
    __metaclass__ = meta.InstanceListerMetaClass

    @abc.abstractmethod
    def render(self, result):
        """
        This method can either be overriden in a subclass or left alone. In the
        latter case it will be generated by
        :py:class:`lmi.scripts.common.meta.InstanceListerMetaClass` metaclass
        with regard to ``PROPERTIES`` and ``DYNAMIC_PROPERTIES``.

        :param result: Either an instance to render or pair of properties and
            instance.
        :type result: :py:class:`lmi.shell.LMIInstance` or tuple
        :returns: List of pairs, where the first item is a label and second a
            value to render.
        :rtype: list
        """
        raise NotImplementedError(
                "render method must be overriden in subclass")

    def take_action(self, connection, args, kwargs):
        """
        Collects results of single host.

        :param connection: Connection to a single host.
        :type connection: :py:class:`lmi.shell.LMIConnection`
        :param list args: Positional arguments for associated function.
        :param dictionary kwargs: Keyword arguments for associated function.
        :returns: Column names and item list as a pair.
        :rtype: tuple
        """
        cols = self.get_columns()
        if cols is None:
            result = self.execute_on_connection(
                    connection, *args, **kwargs)
            if not isinstance(result, tuple) or len(result) != 2:
                raise errors.LmiUnexpectedResult(
                        self.__class__, "(properties, instances)", result)
            cols, data = result
            if not isinstance(cols, (tuple, list)):
                raise errors.LmiUnexpectedResult(
                        self.__class__, "(tuple, ...)", (cols, '...'))
            header = [c if isinstance(c, basestring) else c[0] for c in cols]
            cmd = formatter.NewTableHeaderCommand(columns=header)
            self.produce_output((cmd,))
            return [self.render((cols, inst)) for inst in data]
        else:
            data = self.execute_on_connection(connection, *args, **kwargs)
            if not hasattr(data, '__iter__'):
                raise errors.LmiUnexpectedResult(
                        self.__class__, 'list or generator', data)
            cmd = formatter.NewTableHeaderCommand(columns=cols)
            self.produce_output((cmd,))
            return [self.render(inst) for inst in data]

class LmiShowInstance(LmiSessionCommand):
    """
    End point command producing a list of properties of particular CIM
    instance. Either reduced list of properties to print can be specified, or
    the associated function alone can decide, which properties shall be
    printed. Associated function is expected to return CIM instance as a
    result.

    List of additional recognized properties:

        ``DYNAMIC_PROPERTIES`` : ``bool``
            A boolean saying, whether the associated function alone shall
            specify the list of properties of rendered instance. If ``True``,
            the result of function must be a pair: ::
            
                (props, inst)
                
            Where props is the same value as can be passed to ``PROPERTIES``
            property. Defaults to ``False``.
        ``PROPERTIES`` : ``tuple``
            May contain list of instance properties, that will be produced in
            the same order as output. Each item of list can be either:

                name : ``str``
                    Name of property to render.
                pair : ``tuple``
                    A tuple ``(Name, render_func)``, where former item an
                    arbitraty name for rendered value and the latter is a
                    function taking as the only argument particular instance
                    and returning value to render.

    ``DYNAMIC_PROPERTIES`` and ``PROPERTIES`` are mutually exclusive. If none
    is given, all instance properties will be printed.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.ShowInstanceMetaClass`.
    """
    __metaclass__ = meta.ShowInstanceMetaClass

    def formatter_factory(self):
        return formatter.SingleFormatter

    @abc.abstractmethod
    def render(self, result):
        """
        This method can either be overriden in a subclass or left alone. In the
        latter case it will be generated by
        :py:class:`lmi.scripts.common.meta.ShowInstanceMetaClass` metaclass
        with regard to ``PROPERTIES`` and ``DYNAMIC_PROPERTIES``.

        :param result: Either an instance to
            render or pair of properties and instance.
        :type: :py:class:`lmi.shell.LMIInstance` or ``tuple``
        :returns: List of pairs, where the first item is a label and second a
            value to render.
        :rtype: list
        """
        raise NotImplementedError(
                "render method must be overriden in subclass")

    def take_action(self, connection, args, kwargs):
        """
        Process single connection to a host, render result and return a value
        to render.

        :returns: List of pairs, where the first item is a label and
            second a value to render.
        :rtype: list
        """
        res = self.execute_on_connection(connection, *args, **kwargs)
        return self.render(res)

    def process_session(self, session, args, kwargs):
        failures = []
        for connection in session:
            if len(session) > 1:
                command = formatter.NewHostCommand(connection.hostname)
                self.produce_output(command)
            try:
                self.produce_output(self.take_action(connection, args, kwargs))
            except Exception as exc:
                if self.app.config.trace:
                    LOG().exception('show instance failed for host "%s"',
                            connection.hostname)
                else:
                    LOG().error('show instance failed for host "%s": %s',
                            connection.hostname, exc)
                failures.append((connection.hostname, exc))
            if len(session) > 1:
                self.app.stdout.write("\n")
        if len(failures) > 0:
            self._print_errors(failures)
        return 0

class LmiCheckResult(LmiSessionCommand):
    """
    Run an associated action and check its result. It implicitly makes no
    output if the invocation is successful and expected result matches.

    List of additional recognized properties:

        ``EXPECT`` :
            Value, that is expected to be returned by invoked associated
            function. This can also be a callable taking two arguments:

                1. options - Dictionary with parsed command line options
                   returned by ``docopt``.
                2. result - Return value of associated function.

    Using metaclass:
        :py:class:`lmi.scripts.common.command.meta.CheckResultMetaClass`.
    """
    __metaclass__ = meta.CheckResultMetaClass

    def __init__(self, *args, **kwargs):
        LmiSessionCommand.__init__(self, *args, **kwargs)
        # dictionary of hosts with associated results
        self.results = {}

    def formatter_factory(self):
        return formatter.TableFormatter

    @abc.abstractmethod
    def check_result(self, options, result):
        """
        Check the returned value of associated function.

        :param options: (``dict``) Dictionary as returned by ``docopt`` parser
            after running ``transform_options()``.
        :param result: Any return value that will be compared against what is
            expected.
        :rtype: (``bool`` or ``tuple``) Whether the result is expected value or
            not. If ``tuple`` is returned, it contains
            ``(passed_flag, error_description)``.
        """
        raise NotImplementedError("check_result must be overriden in subclass")

    def take_action(self, connection, args, kwargs):
        """
        Invoke associated method and check its return value for single host.

        :param list args: List of arguments to pass to the associated
            function.
        :param dictionary kwargs: Keyword arguments to pass to the associated
            function.
        :returns: A pair of ``(passed, error)``, where `error`` is an
            instance of exception if any occured, an error string or ``None``.
        :rtype: tuple
        """
        try:
            res = self.execute_on_connection(connection, *args, **kwargs)
            self.results[connection.hostname] = res
            res = self.check_result(self._options, res)
            if isinstance(res, tuple):
                if len(res) != 2:
                    raise ValueError('check_result() must return either boolean'
                        ' or (passed_flag, error_description), not "%s"' %
                        repr(res))
                return res
            return (res, None)
        except Exception as exc:
            if self.app.config.trace:
                LOG().exception("failed to execute wrapped function")
            else:
                LOG().warn("failed to execute wrapped function: %s", exc)
            return (False, exc)

    def process_session(self, session, args, kwargs):
        # first list contain passed hosts, the second one failed ones
        results = ([], [])
        for connection in session:
            passed, error = self.take_action(connection, args, kwargs)
            results[0 if passed else 1].append((connection.hostname, error))
            if not passed and error:
                LOG().warn('invocation failed on host "%s": %s',
                        connection.hostname, error)
                if self.app.config.verbosity >= Configuration.OUTPUT_DEBUG:
                    self.app.stdout.write('invocation failed on host "%s":'
                            ' %s\n"' % (connection.hostname, str(error)))
        if self.app.config.verbosity >= Configuration.OUTPUT_INFO:
            self.app.stdout.write('Successful runs: %d\n' % len(results[0]))
        failed_runs = len(results[1]) + len(session.get_unconnected())
        if failed_runs:
            data = []
            for hostname in session.get_unconnected():
                data.append((hostname, 'failed to connect'))
            for hostname, error in results[1]:
                if error is None:
                    error = "failed"
                    if (self.app.config.verbosity >= Configuration.OUTPUT_INFO
                       and hasattr(self.check_result, 'expected')):
                        error = error + (" (%s != %s)" % (
                            self.check_result.expected,
                            self.results[hostname]))
                data.append((hostname, error))
            self._print_errors(data)
