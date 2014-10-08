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
List packages, repositories or files.

Usage:
    %(cmd)s all [--allow-duplicates]
    %(cmd)s installed
    %(cmd)s available [--repoid <repository>] [--allow-duplicates]
    %(cmd)s repos [--disabled | --all]
    %(cmd)s files [-t <file_type>] <package>

Commands:
    all        - List installed and available packages. Only nevra strings
                 will be shown which greatly speeds up the operation.
    installed  - List installed packages.
    available  - List available packages.
    repos      - List repositories. Only enabled ones are listed by default.
    files      - List files belonging to a package.

Options:
    --allow-duplicates     Print all possible versions of package found.
                           Normally only the newest version is shown.
    --repoid <repository>  List just packages available in given <repository>.
    --all                  List all repositories.
    --disabled             List only disabled repositories.
    -t --type (file | directory | device | symlink | fifo)
                           List only particular file type.
"""
from lmi.scripts import software
from lmi.scripts.common import command
from lmi.scripts.common import errors
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

class AllLister(command.LmiLister):
    CONNECTION_TIMEOUT = 15*60  # timeout after 15 minutes
    COLUMNS = []

    def execute(self, ns, _allow_duplicates=False):
        installed_nevras = None
        if software.get_backend(ns) == software.BACKEND_PACKAGEKIT:
            installed_nevras = set(software.get_package_nevra(p)
                for p in software.list_installed_packages(ns))

        for pkg in software.find_package(ns,
                allow_duplicates=_allow_duplicates):
            yield (software.get_package_nevra(pkg), )

class InstalledLister(command.LmiInstanceLister):
    CONNECTION_TIMEOUT = 4*60  # timeout after 4 minutes
    PROPERTIES = ( ('NEVRA', 'ElementName')
                 , ('Summary', 'Caption'))
    CALLABLE = software.list_installed_packages


class AvailableLister(command.LmiInstanceLister):
    CONNECTION_TIMEOUT = 15*60  # timeout after 15 minutes
    PROPERTIES = ( ('NEVRA', 'ElementName')
                 , ('Summary', 'Caption'))

    def execute(self, ns, _repoid=None, _allow_duplicates=False):
        for pkg in software.list_available_packages(ns,
                repoid=_repoid, allow_duplicates=_allow_duplicates):
            yield pkg

class RepoLister(command.LmiInstanceLister):
    CONNECTION_TIMEOUT = 4*60  # timeout after 4 minutes
    DYNAMIC_PROPERTIES = True

    def execute(self, ns, _all, _disabled):
        if _all:
            properties = (
                    ('Repo id', 'Name'),
                    ('Name', 'Caption'),
                    ('Enabled', lambda i: i.EnabledState == 2))
            enabled = None
        else:
            properties = (
                    ('Repo id', 'Name'),
                    ('Name', 'Caption'))
            enabled = not _disabled

        return (properties, software.list_repositories(ns, enabled))

class FileLister(command.LmiInstanceLister):
    CONNECTION_TIMEOUT = 10*60  # timeout after 10 minutes
    DYNAMIC_PROPERTIES = True

    def verify_options(self, options):
        file_types = { 'all', 'file', 'directory', 'symlink', 'fifo', 'device'}
        if (   options['--type'] is not None
           and options['--type'] not in file_types):
            raise errors.LmiInvalidOptions(
                    'Invalid file type given, must be one of %s.' % file_types)

    def execute(self, ns, package, _type=None):
        properties = [
                ('Name'),
                ('Type', lambda i:
                         software.FILE_TYPES[i.FileType]
                    if   i.FileExists
                    else 'Missing'),
                ('FileSize', lambda i: i.FileSize),
                ('Passed', lambda i: len(i.FailedFlags) < 1)]
        if _type is not None:
            del properties[1]

        pkgs = list(p.to_instance() for p in software.find_package(
                ns, pkg_spec=package))
        pkgs = [p for p in pkgs if software.is_package_installed(p)]
        if len(pkgs) < 1:
            raise errors.LmiFailed(
                    'No package matching "%s" found.' % package)
        if len(pkgs) > 1:
            LOG().warn('More than one package found for "%s": %s', package,
                    ', '.join(p.ElementName for p in pkgs))

        return ( properties
               , software.list_package_files(ns, pkgs[-1], file_type=_type))

class Lister(command.LmiCommandMultiplexer):
    COMMANDS = {
            'all'       : AllLister,
            'installed' : InstalledLister,
            'available' : AvailableLister,
            'repos'     : RepoLister,
            'files'     : FileLister
    }
    FALLBACK_COMMAND = AllLister
    OWN_USAGE = __doc__
