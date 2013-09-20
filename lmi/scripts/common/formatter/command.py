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
Contains command classes used to control formatters from inside of command
execution functions.
"""

class FormatterCommand(object):
    """
    Base class for formatter commands.
    """
    pass

class NewHostCommand(FormatterCommand):
    """
    Command for formatter to finish current table (if any), print header for
    new host and (if there are any data) print table header.

    :param string hostname: Name of host appearing at the front of new table.
    """
    def __init__(self, hostname):
        self.hostname = hostname

class NewTableCommand(FormatterCommand):
    """
    Command for formatter to finish current table (if any), print the **title**
    and (if there are any data) print table header.

    :param string title: Optional title for new table.
    """
    def __init__(self, title=None):
        self.title = title

class NewTableHeaderCommand(FormatterCommand):
    """
    Command for formatter to finish current table (if any), store new table
    header and (if there are any data) print the table header.
    The table header will be printed in all subsequent tables, until
    new instance of this class arrives.

    :param tuple columns: Array of column names.
    """
    def __init__(self, columns=None):
        self.columns = columns
