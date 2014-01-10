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
Defines a base class for all command classes operating upon a
:py:class:`~lmi.scripts.common.session.Session` object.
"""
import abc
from collections import OrderedDict

from lmi.scripts.common import get_logger
from lmi.scripts.common.command import meta
from lmi.scripts.common.command.endpoint import LmiEndPointCommand
from lmi.scripts.common.configuration import Configuration
from lmi.scripts.common.session import Session
from lmi.shell import LMIConnection
from lmi.shell import LMIUtil

LOG = get_logger(__name__)

class LmiSessionCommand(LmiEndPointCommand):
    """
    Base class for end-point commands operating upon a session object.

    Using metaclass: :py:class:`~.meta.SessionCommandMetaClass`.
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

    def process_session(self, session, args, kwargs):
        """
        Process each host of given session, call the associated command
        function, collect results and print it to standard output.

        :param session: Session object with set of hosts.
        :type session: :py:class:`~lmi.scripts.common.session.Session`
        :param list args: Positional arguments to pass to associated function
            in command library.
        :param dictionary kwargs: Keyword arguments as a dictionary.
        :returns: Exit code of application.
        :rtype: integer
        """
        if not isinstance(session, Session):
            raise TypeError("session must be an object of Session, not %s"
                    % repr(session))
        # { ( hostname : (passed, result) ), ... }
        # where passed is a boolean and result is returned value if passed is
        # True and exception otherwise
        results = OrderedDict()
        for connection in session:
            try:
                result = self.take_action(connection, args, kwargs)
                # result may be a generator which may throw in the following
                # function
                results[connection.uri] = (True, result)
                self.process_host_result(connection.uri, True, result)
            except Exception as exc:
                if self.app.config.trace:
                    LOG().exception('invocation failed for host "%s"',
                            connection.uri)
                else:
                    LOG().error('invocation failed for host "%s": %s',
                            connection.uri, exc)
                results[connection.uri] = (False, exc)
                self.process_host_result(connection.uri, False, exc)
        self.process_session_results(session, results)
        return all(r[0] for r in results.values())

    def process_host_result(self, hostname, success, result):
        """
        Called from :py:meth:`process_session` after single host gets
        processed. By default this prints obtained *result* with default
        formatter if the execution was successful. Children of this class may
        want to override this.

        :param string hostname: Name of host involved.
        :param boolean success: Whether the action on host succeeded.
        :param result: Either the value returned by associated function upon a
            successful invocation or an exception.
        """
        if success:
            if len(self.app.session) > 1:
                self.formatter.print_host(hostname)
            self.produce_output(result)

    def process_session_results(self, session, results):
        """
        Called at the end of :py:meth:`process_session`'s execution. It's
        supposed to do any summary work upon results from all hosts. By default
        it just prints errors in a form of list.

        :param session: Session object.
        :type session: :py:class:`lmi.scripts.common.command.session.Session`
        :param dictionary results: Dictionary of form: ::

                { 'hostname' : (success_flag, result), ... }

            where *result* is either an exception or returned value of
            associated function, depending on *success_flag*. See the
            :py:meth:`Session.process_host_result`.
        """
        if not isinstance(session, Session):
            raise TypeError("session must be a Session object")
        if not isinstance(results, dict):
            raise TypeError("results must be a dictionary")
            # check whether any output has been produced
        if (  len(session.get_unconnected())
           or any(not r[0] for r in results.values())):
            data = []
            for hostname in session.get_unconnected():
                data.append((hostname, ['failed to connect']))
            for hostname, (success, error) in results.items():
                if not success:
                    data.append((hostname, [error]))
            self._print_errors(data,
                    new_line=any(r[0] for r in results.values()))

    @abc.abstractmethod
    def take_action(self, connection, args, kwargs):
        """
        Executes an action on single host and collects results.

        :param connection: Connection to a single host.
        :type connection: :py:class:`lmi.shell.LMIConnection`
        :param list args: Positional arguments for associated function.
        :param dictionary kwargs: Keyword arguments for associated function.
        :returns: Column names and item list as a pair.
        :rtype: tuple
        """
        raise NotImplementedError("take_action must be implemented in subclass")

    def execute_on_connection(self, connection, *args, **kwargs):
        """
        Wraps the :py:meth:`~.endpoint.LmiEndPointCommand.execute` method with
        connection adjustments. Connection object is not usually passed
        directly to associated function. Mostly it's the namespace object that
        is expected. This method checks, whether the namespace object is
        desired and modifies connection accordingly.

        :param connection: Connection to single host.
        :type connection: :py:class:`lmi.shell.LMIConnection` 
        :param list args: Arguments handed over to associated function.
        :param dictionary kwargs: Keyword arguments handed over to associated
            function.
        """
        if not isinstance(connection, LMIConnection):
            raise TypeError("expected an instance of LMIConnection for"
                    " connection argument, not %s" % repr(connection))
        namespace = self.cim_namespace()
        if namespace is not None:
            connection = LMIUtil.lmi_wrap_cim_namespace(
                    connection, namespace)
        return self.execute(connection, *args, **kwargs)

    def run_with_args(self, args, kwargs):
        return self.process_session(self.app.session, args, kwargs)

