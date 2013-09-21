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
Defines base command class for all endpoint commands. Those having no children.
"""
import abc
import inspect
import re
from docopt import docopt

from lmi.scripts.common import errors
from lmi.scripts.common import formatter
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
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
                (util.RE_COMMAND_NAME,         lambda m: m.group(0))):
            match = reg.match(name)
            if match:
                new_name = func(match)
                break
        else:
            raise errors.LmiError(
                    'failed to convert argument "%s" to function option' %
                    name)
        if new_name == '--':
            continue    # ignore double dash
        new_name = opt_name_sanitize(new_name)
        if new_name in kwargs:
            raise errors.LmiError('option clash for "%s" and "%s", which both'
                ' translate to "%s"' % (name, orig_names[new_name], new_name))
        kwargs[new_name] = value
        orig_names[new_name] = name
    return kwargs

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
            an instance of :py:class:`~lmi.scripts.common.formatter.Formatter`.

    Using metaclass:
        :py:class:`.meta.EndPointCommandMetaClass`.
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

        :rtype: :py:class:`~lmi.scripts.common.formatter.Formatter`
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
        :py:class:`~.meta.EndPointCommandMetaClass`
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
        :py:exc:`~lmi.scripts.common.errors.LmiInvalidOptions` exception shall
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
            :py:meth:`~lmi.scripts.common.formatter.Formatter.produce_output`
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

    def _print_errors(self, error_list, new_line=True):
        """
        Print list of errors.

        :param list errors: Errors to print. Each error is a ``tuple``: ::

                (hostname, [error, error])

            Where ``error`` may be a test description or an instance of
            exception.
        :param new_line: Whether to print the new line before new error
            table is printed.
        """
        fmt = formatter.ErrorFormatter(self.app.stderr)
        if new_line:
            fmt.out.write('\n')
        if error_list:
            new_table_cmd = fcmd.NewTableCommand("There %s %d error%s" %
                ( 'were' if len(error_list) > 1 else 'was'
                , len(error_list)
                , 's' if len(error_list) > 1 else ''))
            fmt.produce_output((new_table_cmd, ))
        for hostname, host_errors in error_list:
            fmt.produce_output((fcmd.NewHostCommand(hostname), ))
            fmt.produce_output(host_errors)

