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

