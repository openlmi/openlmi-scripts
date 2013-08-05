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
Sub package with formatter classes used to render and output results.

Each formatter has an ``produce_output()`` method taking one argument which
gets rendered and printed to output stream. Each formatter expects different
argument, please refer to doc string of particular class.
"""

import itertools

class Formatter(object):
    """
    Base formatter class.
    
    It produces string representation of given argument and prints it.

    :param stream: (``file``) Output stream.
    :param padding: (``int``) Number of leading spaces to print at each line.
    """

    def __init__(self, stream, padding=0):
        if not isinstance(padding, (int, long)):
            raise TypeError("padding must be an integer")
        if padding < 0:
            padding = 0
        self.out = stream
        self.padding = padding

    def render_value(self, val):
        """
        Rendering function for single value.

        :param val: Any value to render.
        :rtype: (``str``) Value converted to its string representation.
        """
        if isinstance(val, unicode):
            return val.encode('utf-8')
        if not isinstance(val, str):
            val = str(val)
        return val

    def print_line(self, line, *args, **kwargs):
        """
        Prints single line. Output message is prefixed with ``padding`` spaces,
        formated and printed to output stream.

        :param line: (``str``) Message to print, it can contain markers for
            other arguments to include according to ``format_spec`` language.
            Please refer to ``Format Specification Mini-Language`` in python
            documentation.
        :param args: (``list``) Positional arguemnts to ``format`` function of
            ``line`` argument.
        :param kwargs: (``dict``) Keyword arguments to ``format()`` function.
        """
        self.out.write(' '*self.padding + line.format(*args, **kwargs))
        self.out.write("\n")

    def produce_output(self, data):
        """
        Render and print given data.

        This shall be overriden by subclasses.

        :param data: Any value to print. Subclasses may specify their
            requirements for this argument.
        """
        self.print_line(str(data))

class ListFormatter(Formatter):
    """
    Base formatter taking care of list of items. It renders input data in a
    form of table with mandatory column names at the beginning followed by
    items, one occupyin single line (row).
    
    This class should be subclassed to provide nice output. 
    """

    def print_row(self, row):
        """
        Print single item. This should be overriden by subclass.

        :param row: (``tuple``) Attributes of single item.
        """
        self.out.write(self.render_value(row))

    def produce_output(self, data):
        """
        Takes a pair of ``(columns, rows)`` where ``columns`` is a list of
        column names and rows is a list of rows to print.

        :param data: (``tuple``) A pair of column names and rows.
        """
        if not isinstance(data, tuple):
            raise TypeError("data must be a tuple")
        if not len(data) == 2:
            raise ValueError(
                "data must contain: (list_of_columns, list of rows)")
        columns, data = data
        self.out.write(' '*self.padding)
        self.print_row(columns)
        for row in data:
            self.print_row(row)

class CsvFormatter(ListFormatter):
    """
    Renders data in a csv (Comma-separated values) format.
    """

    def render_value(self, val):
        if isinstance(val, basestring):
            if isinstance(val, unicode):
                val.encode('utf-8')
            val = '"%s"' % val.replace('"', '""')
        elif val is None:
            val = ''
        else:
            val = str(val)
        return val

    def print_row(self, row):
        self.print_line(",".join(self.render_value(v) for v in row))

class SingleFormatter(Formatter):
    """
    Meant to render and print attributes of single object.
    Attributes are rendered as a list of assignments of values to
    variables (attribute names).
    """

    def produce_output(self, data):
        """
        Render and print attributes of single item.

        :param data: (``tuple`` or ``dict``) Is either a pair of property
            names with list of values or a dictionary with property names as
            keys. Using the pair allows to order the data the way it should be
            printing. In the latter case the properties will be sorted by the
            property names.
        """
        if not isinstance(data, (tuple, dict)):
            raise TypeError("data must be a tuple")
        if isinstance(data, tuple):
            if not len(data) == 2:
                raise ValueError(
                    "data must contain: (list of columns, list of rows)")
            dataiter = itertools.izip(data[0], data[1])
        else:
            dataiter = itertools.imap(
                    lambda k: (k, self.render_value(data[k])),
                    sorted(data.keys()))
        for name, value in dataiter:
            self.print_line("{0}={1}", name, value)

class ShellFormatter(SingleFormatter):
    """
    Specialization of ``SingleFormatter`` having its output eexecutable as a
    shell script.
    """

    def render_value(self, val):
        if isinstance(val, basestring):
            if isinstance(val, unicode):
                val.encode('utf-8')
            val = "'%s'" % val.replace("'", "\\'")
        elif val is None:
            val = ''
        else:
            val = str(val)
        return val
