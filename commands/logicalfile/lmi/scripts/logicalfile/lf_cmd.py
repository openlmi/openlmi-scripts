# LogicalFile Management Providers
#
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
# Authors: Jan Synacek <jsynacek@redhat.com>
#

"""
File and directory management functions.

Usage:
    %(cmd)s list <directory> [ <depth> ]
    %(cmd)s createdir <directory>
    %(cmd)s deletedir <directory>
    %(cmd)s show <target>

Commands:
    list       List a directory. When depth is specified, at most depth levels
               will be listed recursively.

               The files and directories are listed in a tree-like structure.

               Possible listed file types are:
                   * F   : Regular data file.
                   * Dev : Device file. Can be either block or character device.
                   * Dir : Directory.
                   * P   : Pipe file.
                   * L   : Symbolic link.
                   * S   : Unix socket.

    createdir  Create a directory. The parent directory must exist.

    deletedir  Delete a directory. The directory must be empty.

    show       Show detailed information about target. Target can be any file
               on the remote system.
"""

from lmi.scripts.common import command
from lmi.scripts.logicalfile import logicalfile

class Lister(command.LmiLister):
    COLUMNS = ('Type', 'Name', 'Mode', 'Current SELinux Context')
    OPT_NO_UNDERSCORES = True
    CALLABLE = logicalfile.lf_list

class Show(command.LmiLister):
    COLUMNS = ('Name', 'Value')
    OPT_NO_UNDERSCORES = True
    CALLABLE = logicalfile.lf_show

class CreateDir(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = logicalfile.lf_createdir

class DeleteDir(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = logicalfile.lf_deletedir

Lf = command.register_subcommands(
        'Lf', __doc__,
        { 'list'    : Lister,
          'createdir'  : CreateDir,
          'deletedir'  : DeleteDir,
          'show'    : Show,
        },
    )
