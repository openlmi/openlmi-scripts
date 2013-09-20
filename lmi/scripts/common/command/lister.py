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
Defines command classes producing tablelike output.
"""

import abc
from itertools import chain

from lmi.scripts.common import errors
from lmi.scripts.common import formatter
from lmi.scripts.common import get_logger
from lmi.scripts.common.command import meta
from lmi.scripts.common.command.session import LmiSessionCommand
from lmi.scripts.common.configuration import Configuration
from lmi.scripts.common.formatter import command as fcmd

LOG = get_logger(__name__)

class LmiBaseListerCommand(LmiSessionCommand):
    """
    Base class for all lister commands.
    """

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

    Using metaclass: :py:class:`~.meta.ListerMetaClass`.
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
            command = fcmd.NewTableHeaderCommand(columns)
            res = chain((command, ), res)
        return res

class LmiInstanceLister(LmiBaseListerCommand):
    """
    End point command outputting a table of instances for each host.
    Associated function shall return a list of instances. They may be
    prepended with column names depending on value of ``DYNAMIC_PROPERTIES``.
    Each instance will occupy single row of table with property values being a
    content of cells.

    List of additional recognized properties is the same as for
    :py:class:`~.show.LmiShowInstance`. There is just one difference. Either
    ``DYNAMIC_PROPERTIES`` must be ``True`` or ``PROPERTIES`` must be filled.

    Using metaclass: :py:class:`~.meta.InstanceListerMetaClass`.
    """
    __metaclass__ = meta.InstanceListerMetaClass

    @abc.abstractmethod
    def render(self, result):
        """
        This method can either be overriden in a subclass or left alone. In the
        latter case it will be generated by
        :py:class:`~.meta.InstanceListerMetaClass` metaclass with regard to
        ``PROPERTIES`` and ``DYNAMIC_PROPERTIES``.

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
            cmd = fcmd.NewTableHeaderCommand(columns=header)
            return chain((cmd, ), (self.render((cols, inst)) for inst in data))
        else:
            data = self.execute_on_connection(connection, *args, **kwargs)
            if not hasattr(data, '__iter__'):
                raise errors.LmiUnexpectedResult(
                        self.__class__, 'list or generator', data)
            cmd = fcmd.NewTableHeaderCommand(columns=cols)
            return chain((cmd, ), (self.render(inst) for inst in data))
