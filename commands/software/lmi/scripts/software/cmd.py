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
    %(cmd)s list pkgs
        [--available [--repoid <repository>] | --all]
        [--allow-duplicates]
    %(cmd)s list repos [--disabled | --all]
    %(cmd)s list files <package>
    %(cmd)s show pkg [--repoid <repository>] <package> ...
    %(cmd)s show repo <repository> ...
    %(cmd)s install [--force] <package> ...
    %(cmd)s install --uri <uri>
    %(cmd)s remove <package> ...
    %(cmd)s verify <package> ...
    %(cmd)s update <package> ...
    %(cmd)s enable <repository> ...
    %(cmd)s disable <repository> ...

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
    --repoid <repository>  Select a repository, where the given package will
                   be searched for.
    --uri <uri>    Operate upon an rpm package available on remote system
                   through http or ftp service.
"""

from lmi.scripts import software
from lmi.scripts.common import command

class PkgLister(command.LmiInstanceLister):
    DYNAMIC_PROPERTIES = True

    def execute(self, ns,
            _available=False,
            _all=False,
            _repoid=None,
            _allow_duplicates=False):
        properties = (
                ('NEVRA', 'ElementName'),
                ('Summary', 'Caption'))
        if _all or _available:
            instances = software.list_available_packages(ns,
                    allow_installed=_all,
                    allow_duplicates=_allow_duplicates,
                    repoid=_repoid)

        else:
            instances = software.list_installed_packages(ns)

        return (properties, instances)

class RepoLister(command.LmiInstanceLister):
    DYNAMIC_PROPERTIES = True

    def execute(self, ns, _all, _disabled):
        if _all:
            properties = (
                    ('Repo id', 'Name'),
                    ('Name', 'Description'),
                    ('Enabled', lambda i: i.EnabledState == 2))
            enabled = None
        else:
            properties = (
                    ('Repo id', 'Name'),
                    ('Name', 'Description'))
            enabled = not _disabled

        return (properties, software.list_repos(ns, enabled))

class Lister(command.LmiCommandMultiplexer):
    """ List information about packages, repositories or files. """
    COMMANDS = { 'pkgs' : PkgLister, 'repos' : RepoLister }

class PkgInfo(command.LmiShowInstance):
    CALLABLE = 'lmi.scripts.software:show_pkg'
    ARG_ARRAY_SUFFIX = '_array'

    def transform_options(self, options):
        options['repo'] = options.pop('--repo')

class Show(command.LmiCommandMultiplexer):
    """ Show information about packages or repositories. """
    COMMANDS = { 'package' : PkgInfo }

Software = command.register_subcommands(
        'Software', __doc__,
        { 'list'    : Lister
        , 'show'    : Show
        }
    )
