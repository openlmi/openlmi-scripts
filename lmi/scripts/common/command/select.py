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
Defines command class used to choose other commands depending on
profile and class requirements.
"""

from docopt import docopt
from pyparsing import ParseException

from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common.command import base
from lmi.scripts.common.command import meta
from lmi.scripts.common.session import SessionProxy
from lmi.scripts.common.versioncheck import eval_respl

class LmiSelectCommand(base.LmiBaseCommand):
    """
    Base class for command selectors. It does not process command line
    arguments. Thery are passed unchanged to selected command whose
    requirements are met. Its doc string is not interpreted in any way.

    If there are more hosts, conditions are evaluated per each. They are then
    split into groups, each fulfilling particular condition. Associated
    commands are then invoked on these groups separately.

    Example usage: ::

        class MySelect(LmiSelectCommand):
            SELECT = [
                ( 'OpenLMI-Hardware >= 0.4.2'
                , 'lmi.scripts.hardware.current.Cmd'),
                ('OpenLMI-Hardware', 'lmi.scripts.hardware.pre042.Cmd')
            ]
            DEFAULT = MissingHwProviderCmd

    Using metaclass: :py:class:`.meta.SelectMetaClass`.
    """
    __metaclass__ = meta.SelectMetaClass

    @classmethod
    def is_end_point(cls):
        return False

    @classmethod
    def is_multiplexer(cls):
        return False

    @classmethod
    def get_conditionals(cls):
        """
        Get the expressions with associated commands. This shall be overriden
        by a subclass.

        :returns: Pair of ``(expressions, default)``.
            Where ``expressions`` is a list of pairs ``(condition, command)``.
            And ``default`` is the same as ``command`` used in case no
            ``condition`` is satisfied.
        :rtype: list
        """
        raise NotImplementedError(
                "get_conditionals needs to be defined in subclass")

    def eval_expr(self, expr, hosts, cache=None):
        """
        Evaluate expression on group of hosts.

        :param string expr: Expression to evaluate.
        :param list hosts: Group of hosts that shall be checked.
        :param dictionary cache: Optional cache object speeding up evaluation
            by reducing number of queries to broker.
        :returns: Subset of hosts satisfying *expr*.
        :rtype: list
        """
        if cache is None:
            cache = dict()
        session = self.session
        satisfied = []
        try:
            for host in hosts:  # TODO: could be done concurrently
                conn = session[host]
                if not conn:
                    continue
                if eval_respl(expr, conn, cache=cache):
                    satisfied.append(host)
        except ParseException:
            raise errors.LmiBadSelectExpression(self.__class__.__module__,
                    self.__class__.__name__, "Bad select expression: %s" % expr)
        return satisfied

    def select_cmds(self, cache=None):
        """
        Generator of command factories with associated groups of hosts. It
        evaluates given expressions on session. In this process all expressions
        from :py:meth:`get_conditionals` are checked in a row. Host satisfying
        some expression is added to group associated with it and is excluded
        from processing following expressions.

        :param dictionary cache: Optional cache object speeding up the evaluation
            by reducing number of queries to broker.
        :returns: Pairs in form ``(command_factory, session_proxy)``.
        :rtype: generator
        :raises:
            * :py:class:`~lmi.scripts.common.errors.LmiUnsatisfiedDependencies`
                if no condition is satisfied for at least one host. Note that
                this exception is raised at the end of evaluation. This lets
                you choose whether you want to process satisfied hosts - by
                processing the generator at once. Or whether you want to be
                sure it is satisfied by all of them - you turn the generator
                into a list.
            * :py:class:`~lmi.scripts.common.errors.LmiNoConnections`
                if no successful connection was done.
        """
        if cache is None:
            cache = dict()
        conds, default = self.get_conditionals()
        def get_cmd_factory(cmd):
            if isinstance(cmd, basestring):
                i = cmd.rindex('.')
                module = __import__(cmd[:i], fromlist=cmd[i+1:])
                return getattr(module, cmd[i+1:])
            else:
                return cmd

        session = self.session
        unsatisfied = set(session.hostnames)

        for expr, cmd in conds:
            hosts = self.eval_expr(expr, unsatisfied, cache)
            if hosts:
                yield get_cmd_factory(cmd), SessionProxy(session, hosts)
            hosts = set(hosts).union(set(session.get_unconnected()))
            unsatisfied.difference_update(hosts)
            if not unsatisfied:
                break
        if default is not None and unsatisfied:
            yield get_cmd_factory(default), SessionProxy(session, unsatisfied)
            unsatisfied.clear()
        if len(unsatisfied):
            raise errors.LmiUnsatisfiedDependencies(unsatisfied)
        if len(session) == len(session.get_unconnected()):
            raise errors.LmiNoConnections("No successful connection!")

    def get_usage(self, proper=False):
        """
        Try to get usage of any command satisfying some expression.

        :raises: Same exceptions as :py:meth:`select_cmds`.
        """
        for cmd_cls, _ in self.select_cmds():
            cmd = cmd_cls(self.app, self.cmd_name, self.parent)
            return cmd.get_usage(proper)

    def run(self, args):
        """
        Iterate over command factories with associated sessions and
        execute them with unchanged *args*.
        """
        result = 0
        for cmd_cls, session in self.select_cmds():
            cmd = cmd_cls(self.app, self.cmd_name, self.parent)
            cmd.set_session_proxy(session)
            ret = cmd.run(args)
            if result == 0:
                result = ret
        return result

