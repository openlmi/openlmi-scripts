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
Module containing help command.
"""

from lmi.scripts.common.command import LmiEndPointCommand

class Help(LmiEndPointCommand):
    """
    Print the list of supported commands with short description.
    If a subcommand is given, its detailed help will be printed.

    Usage: %(cmd)s [<subcommand>]
    """
    OWN_USAGE = True

    def execute(self, subcommand):
        mgr = self.app.command_manager
        if subcommand is not None:
            # print the details of given command
            cmd = mgr[subcommand](self.app, subcommand,
                    parent=self.parent)
            self.app.stdout.write(cmd.get_usage(True))
        else:
            # let's print the summary of available commands
            self.app.stdout.write("Commands:\n")
            max_cmd_len = max(len(n) for n in mgr)
            cmd_line = "  %%-%ds - %%s\n" % max_cmd_len
            for cmd in sorted(mgr):
                self.app.stdout.write(cmd_line
                        % (cmd, mgr[cmd].get_description()
                            .strip().split("\n", 1)[0]))
        return 0

