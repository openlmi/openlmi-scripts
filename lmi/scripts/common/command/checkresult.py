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
This module defines LmiCheckResult command class and related utilities.
"""

import abc

from lmi.scripts.common import Configuration
from lmi.scripts.common import get_logger
from lmi.scripts.common import formatter
from lmi.scripts.common import errors
from lmi.scripts.common.command import meta
from lmi.scripts.common.command.session import LmiSessionCommand

LOG = get_logger(__name__)

class LmiResultFailed(errors.LmiFailed):
    """
    Exception raised when associated function returns unexpected result. This
    is evaluated by :py:meth:`LmiCheckResult.check_result` method.
    """
    pass

def _make_result_failed(expected, result):
    """
    Instantiate :py:exc:`LmiResultFailed` exception with descriptive message
    composed of what was expected and what was returned instead.

    :rtype: :py:class:`LmiResultFailed`
    """
    return LmiResultFailed('failed (%s != %s)' % (repr(expected), repr(result)))

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

    Using metaclass: :py:class:`~.meta.CheckResultMetaClass`.
    """
    __metaclass__ = meta.CheckResultMetaClass

    def __init__(self, *args, **kwargs):
        LmiSessionCommand.__init__(self, *args, **kwargs)

    def formatter_factory(self):
        return formatter.TableFormatter

    @abc.abstractmethod
    def check_result(self, options, result):
        """
        Check the returned value of associated function.

        :param dictionary options: Dictionary as returned by ``docopt`` parser
            after running
            :py:meth:`~.endpoint.LmiEndPointCommand.transform_options`.
        :param result: Any return value that will be compared against what is
            expected.
        :returns:  Whether the result is expected value or not. If ``tuple``
            is returned, it contains ``(passed_flag, error_description)``.
        :rtype: boolean or tuple.
        """
        raise NotImplementedError("check_result must be overriden in subclass")

    def take_action(self, connection, args, kwargs):
        """
        Invoke associated method and check its return value for single host.

        :param list args: List of arguments to pass to the associated
            function.
        :param dictionary kwargs: Keyword arguments to pass to the associated
            function.
        :returns: Exit code (0 on success).
        :rtype: integer
        """
        try:
            result = self.execute_on_connection(connection, *args, **kwargs)
            passed = self.check_result(self._options, result)
            if isinstance(passed, tuple):
                if len(passed) != 2:
                    raise errors.LmiUnexpectedResult('check_result() must'
                        ' return either boolean or (passed_flag,'
                        ' error_description), not "%s"' % repr(passed))
                if not passed[0]:
                    raise LmiResultFailed(passed[1])
            elif not passed and hasattr(self.check_result, 'expected'):
                err = _make_result_failed(self.check_result.expected, result)
                raise err
        except LmiResultFailed:
            raise
        except Exception as err:
            if self.app.config.trace:
                LOG().exception("failed to execute wrapped function")
            else:
                LOG().error("failed to execute wrapped function: %s", err)
            raise
        return 0

    def process_host_result(self, hostname, success, result):
        pass

    def process_session_results(self, session, results):
        if self.app.config.verbosity >= Configuration.OUTPUT_INFO:
            self.app.stdout.write('Successful runs: %d\n' %
                    len([r for r in results.values() if r[0]]))
        LmiSessionCommand.process_session_results(self, session, results)
