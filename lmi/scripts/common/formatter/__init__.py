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
Subpackage with formatter classes used to render and output results.

Each formatter has a :py:meth:`Formatter.produce_output` method taking one
argument which gets rendered and printed to output stream. Each formatter
expects different argument, please refer to doc string of particular class.
"""

import itertools
import locale
import os
import pywbem

from lmi.scripts.common import errors
from lmi.scripts.common.formatter import command as fcmd

def get_terminal_width():
    """
    Get the number of columns of current terminal if attached to it. It
    defaults to 79 characters.

    :returns: Number of columns of attached terminal.
    :rtype: integer
    """
    try:
        term_cols = int(os.popen('stty size', 'r').read().split()[1])
    except (IOError, OSError, ValueError):
        term_cols = 79  # fallback
    return term_cols

class Formatter(object):
    """
    Base formatter class.

    It produces string representation of given argument and prints it.

    This formatter supports following commands:

        * :py:class:`~.command.NewHostCommand`.

    :param file stream: Output stream.
    :param integer padding: Number of leading spaces to print at each line.
    :param boolean no_headings: If table headings should be omitted.
    """

    def __init__(self, stream, padding=0, no_headings=False):
        if not isinstance(padding, (int, long)):
            raise TypeError("padding must be an integer")
        if padding < 0:
            padding = 0
        self.out = stream
        self.padding = padding
        self.no_headings = no_headings
        #: counter of hosts printed
        self.host_counter = 0
        #: counter of tables produced for current host
        self.table_counter = 0
        #: counter of lines producted for current table
        self.line_counter = 0

    @property
    def encoding(self):
        """
        Try to determine encoding for output terminal.

        :returns: Encoding used to encode unicode strings.
        :rtype: string
        """
        enc = getattr(self.out, 'encoding')
        if not enc:
            enc = locale.getpreferredencoding()
        return enc

    def render_value(self, val):
        """
        Rendering function for single value.

        :param val: Any value to render.
        :returns: Value converted to its string representation.
        :rtype: str
        """
        if isinstance(val, unicode):
            return val.encode(self.encoding)
        if not isinstance(val, str):
            val = str(val)
        return val

    def print_line(self, line, *args, **kwargs):
        """
        Prints single line. Output message is prefixed with ``padding`` spaces,
        formated and printed to output stream.

        :param string line: Message to print, it can contain markers for
            other arguments to include according to ``format_spec`` language.
            Please refer to ``Format Specification Mini-Language`` in python
            documentation.
        :param list args: Positional arguments to ``format()`` function of
            ``line`` argument.
        :param dictionary kwargs: Keyword arguments to ``format()`` function.
        """
        line = ' ' * self.padding + line.format(*args, **kwargs)
        self.out.write(line.encode(self.encoding))
        self.out.write("\n")
        self.line_counter += 1

    def print_host(self, hostname):
        """
        Prints header for new host.

        :param string hostname: Hostname to print.
        """
        if (  self.host_counter > 0
           or self.table_counter > 0
           or self.line_counter > 0):
            self.out.write("\n")
        term_width = get_terminal_width()
        self.out.write("="*term_width + "\n")
        self.out.write("Host: %s\n" % hostname)
        self.out.write("="*term_width + "\n")
        self.host_counter += 1
        self.table_counter = 0
        self.line_counter = 0

    def produce_output(self, data):
        """
        Render and print given data.

        Data can be also instance of
        :py:class:`~.command.FormatterCommand`, see
        documentation of this class for list of
        allowed commands.

        This shall be overridden by subclasses.

        :param data: Any value to print. Subclasses may specify their
            requirements for this argument. It can be also am instance of
            :py:class:`~.command.FormatterCommand`.
        """
        self.print_line(str(data))
        self.line_counter += 1

class ListFormatter(Formatter):
    """
    Base formatter taking care of list of items. It renders input data in a
    form of table with mandatory column names at the beginning followed by
    items, one occupying single line (row).

    This formatter supports following commands:
        * :py:class:`~.command.NewHostCommand`
        * :py:class:`~.command.NewTableCommand`
        * :py:class:`~.command.NewTableHeaderCommand`

    The command must be provided as content of one row. This row is then not
    printed and the command is executed.

    This class should be subclassed to provide nice output.
    """
    def __init__(self, stream, padding=0, no_headings=False):
        super(ListFormatter, self).__init__(stream, padding, no_headings)
        self.column_names = None

    def print_text_row(self, row):
        """
        Print data row without any header.

        :param tuple row: Data to print.
        """
        self.out.write(" "*self.padding + self.render_value(row) + "\n")
        self.line_counter += 1

    def print_row(self, data):
        """
        Print data row. Optionaly print header, if requested.

        :param tuple data: Data to print.
        """
        if self.line_counter == 0 and not self.no_headings:
            self.print_header()
        self.print_text_row(data)

    def print_table_title(self, title):
        """
        Prints title of next tale.

        :param string title: Title to print.
        """
        if self.table_counter > 0 or self.line_counter > 0:
            self.out.write('\n')
        self.out.write("%s:\n" % title)
        self.table_counter += 1
        self.line_counter = 0

    def print_header(self):
        """ Print table header. """
        if self.no_headings:
            return
        if self.column_names:
            self.print_text_row(self.column_names)

    def produce_output(self, rows):
        """
        Prints list of rows.

        There can be a :py:class:`~.command.FormatterCommand` instance instead
        of a row. See documentation of this class for list of allowed commands.

        :param rows:  List of rows to print.
        :type rows: list, generator or :py:class:`.command.FormatterCommand`
        """
        for row in rows:
            if isinstance(row, fcmd.NewHostCommand):
                self.print_host(row.hostname)
            elif isinstance(row, fcmd.NewTableCommand):
                self.print_table_title(row.title)
            elif isinstance(row, fcmd.NewTableHeaderCommand):
                self.column_names = row.columns
            else:
                self.print_row(row)

class TableFormatter(ListFormatter):
    """
    Print nice human-readable table to terminal.

    To print the table nicely aligned, the whole table must be populated first.
    Therefore this formatter stores all rows locally and does not print
    them until the table is complete. Column sizes are computed afterwards
    and the table is printed at once.

    This formatter supports following commands:
        * :py:class:`~.command.NewHostCommand`
        * :py:class:`~.command.NewTableCommand`
        * :py:class:`~.command.NewTableHeaderCommand`

    The command must be provided as content of one row. This row is then not
    printed and the command is executed.
    """
    def __init__(self, stream, padding=0, no_headings=False):
        super(TableFormatter, self).__init__(stream, padding, no_headings)
        self.stash = []

    def print_text_row(self, row, column_size):
        for i in xrange(len(row)):
            size = column_size[i]
            item = self.render_value(row[i])
            if i < len(row) - 1:
                item = item.ljust(size)
            self.out.write(item)
            self.out.write(" ")
        self.out.write("\n")
        self.line_counter += 1

    def print_stash(self):
        if not self.stash:
            return

        # Compute column sizes
        column_sizes = []
        for i in xrange(len(self.column_names)):
            column_sizes.append(len(self.column_names[i]))
        for row in self.stash:
            for i in xrange(len(row)):
                row_length = len(unicode(row[i]))
                if column_sizes[i] < row_length:
                    column_sizes[i] = row_length

        # print headers
        if not self.no_headings:
            self.print_text_row(self.column_names, column_sizes)
        # print stashed rows
        for row in self.stash:
            self.print_text_row(row, column_sizes)
        self.stash = []

    def print_row(self, data):
        """
        Print data row.

        :param tuple data: Data to print.
        """
        self.stash.append(data)

    def print_host(self, hostname):
        """
        Prints header for new host.

        :param string hostname: Hostname to print.
        """
        self.print_stash()
        super(TableFormatter, self).print_host(hostname)

    def print_table_title(self, title):
        """
        Prints title of next tale.

        :param string title: Title to print.
        """
        self.print_stash()
        if self.table_counter > 0 or self.line_counter > 0:
            self.out.write('\n')
        self.out.write("%s:\n" % title)
        self.table_counter += 1
        self.line_counter = 0

    def produce_output(self, rows):
        """
        Prints list of rows.

        There can be :py:class:`~.command.FormatterCommand` instance instead of
        a row. See documentation of this class for list of allowed commands.

        :param rows: List of rows to print.
        :type rows: list or generator
        """
        super(TableFormatter, self).produce_output(rows)
        self.print_stash()

class CsvFormatter(ListFormatter):
    """
    Renders data in a csv (Comma-separated values) format.

    This formatter supports following commands:
        * :py:class:`~.command.NewHostCommand`
        * :py:class:`~.command.NewTableCommand`
        * :py:class:`~.command.NewTableHeaderCommand`
    """

    def render_value(self, val):
        if isinstance(val, basestring):
            if isinstance(val, unicode):
                val.encode(self.encoding)
            val = '"%s"' % val.replace('"', '""')
        elif val is None:
            val = ''
        else:
            val = str(val)
        return val

    def print_text_row(self, row):
        self.print_line(",".join(self.render_value(v) for v in row))
        self.line_counter += 1

class SingleFormatter(Formatter):
    """
    Meant to render and print attributes of single object. Attributes are
    rendered as a list of assignments of values to variables (attribute names).

    This formatter supports following commands:
        * :py:class:`~.command.NewHostCommand`
    """

    def produce_output(self, data):
        """
        Render and print attributes of single item.

        There can be a :py:class:`~.command.FormatterCommand` instance instead
        of a data. See documentation of this class for list of allowed
        commands.

        :param data: Is either a pair of property names with list of values or
            a dictionary with property names as keys. Using the pair allows to
            order the data the way it should be printing. In the latter case
            the properties will be sorted by the property names.
        :type data: tuple or dict
        """
        if isinstance(data, fcmd.NewHostCommand):
            self.print_host(data.hostname)
            return

        if not isinstance(data, (tuple, dict)):
            raise ValueError("data must be tuple or dict")

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
            self.line_counter += 1

class ShellFormatter(SingleFormatter):
    """
    Specialization of :py:class:`SingleFormatter` having its output executable
    as a shell script.

    This formatter supports following commands:
        * :py:class:`~.command.NewHostCommand`
    """

    def render_value(self, val):
        if isinstance(val, basestring):
            if isinstance(val, unicode):
                val.encode(self.encoding)
            val = "'%s'" % val.replace("'", "\\'")
        elif val is None:
            val = ''
        else:
            val = str(val)
        return val

class ErrorFormatter(ListFormatter):
    """
    Render error strings for particular host. Supported commands:
        * :py:class:`~.command.NewHostCommand`
    """
    def __init__(self, stream, padding=4):
        super(ErrorFormatter, self).__init__(stream, padding)

    def print_row(self, data):
        if isinstance(data, Exception):
            if isinstance(data, pywbem.CIMError):
                self.print_text_row("%s: %s" % (data.args[1], data.message))
            elif not isinstance(data, errors.LmiFailed):
                self.print_text_row("(%s) %s" % (data.__class__.__name__,
                    str(data)))
            else:
                self.print_text_row(data)
        else:
            self.print_text_row(data)

    def print_host(self, hostname):
        self.out.write("host %s\n" % hostname)
        self.host_counter += 1
        self.table_counter = 0
        self.line_counter = 0

    def produce_output(self, rows):
        for row in rows:
            if isinstance(row, fcmd.NewHostCommand):
                self.print_host(row.hostname)
            elif isinstance(row, fcmd.NewTableCommand):
                self.print_table_title(row.title)
            else:
                self.print_row(row)

