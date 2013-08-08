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
System software management.

Usage:
    %(cmd)s list pkgs [(--available [--repo <repo>] | --all)] [--allow-duplicates]
    %(cmd)s list repos [--disabled | --all]
    %(cmd)s list files <pkg>
    %(cmd)s show pkg [--repo <repo>] <pkg> ...
    %(cmd)s show repo <repo> ...
    %(cmd)s install [--force] <pkg> ...
    %(cmd)s install --uri <uri>
    %(cmd)s remove <pkg> ...
    %(cmd)s verify <pkg> ...
    %(cmd)s update <pkg> ...
    %(cmd)s enable <repo> ...
    %(cmd)s disable <repo> ...

Commands:
    list        List various information about packages, repositories or
                files.
    start       Show detailed informations about package or repository.
    install     Install packages specified in one of following notations:
                    <name>
                    <name>.<arch>
                    <name>-<epoch>:<version>-<release>.<arch>
                Installation from URI is also supported, it must be prefixed
                with --uri option.
    remove      Remove installed package.
    verify      Verify package.
    update      Update package.
    enable      Enable one or more repositories.

Options:
    --force        Force installation
    --repo <repo>  Select a repository, where the given package will be
                   searched.
    --uri <uri>    Operate upon an rpm package available on remote system
                   through http or ftp service.
"""

from lmi.scripts.common import command

CALLABLE = 'lmi.scripts.software:list'
COLUMNS = ('Name', "Started", 'Status')

class PkgLister(command.LmiLister):
    CALLABLE = 'lmi.scripts.software:list_pkgs'

class RepoLister(command.LmiLister):
    CALLABLE = 'lmi.scripts.software:list_repos'

class Lister(command.LmiCommandMultiplexer):
    """ List information about packages, repositories or files. """
    COMMANDS = { 'pkgs' : PkgLister, 'repos' : RepoLister }

Software = command.register_subcommands(
        'Software', __doc__,
        { 'list'    : Lister },
    )
