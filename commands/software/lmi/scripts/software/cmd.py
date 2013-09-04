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
        [(--available | --all) [--repoid <repository>]]
        [--allow-duplicates] [<package> ...]
    %(cmd)s list repos [--disabled | --all]
    %(cmd)s list files [-t <file_type>] <package>
    %(cmd)s show pkg [(--repoid <repository>) | --installed] <package>
    %(cmd)s show repo <repository>
    %(cmd)s install [--force] [--repoid <repository>] <package> ...
    %(cmd)s install --uri <uri>
    %(cmd)s update [--force] [--repoid <repository>] <package> ...
    %(cmd)s remove <package> ...
    %(cmd)s verify <package> ...
    %(cmd)s enable <repository> ...
    %(cmd)s disable <repository> ...

Commands:
    list        List various information about packages, repositories or
                files.
    show        Show detailed informations about package or repository.
    install     Install packages on system. See below, how package can be
                specified. Installation from URI is also supported, it must
                be prefixed with --uri option.
    update      Update package.
    remove      Remove installed package.
    verify      Verify package. Files that did not pass the verification are
                listed prefixed with a sequence of characters, each
                representing particular attribute, that failed. Those are:
                   S file Size differs
                   M Mode differs (includes permissions and file type)
                   5 digest (formerly MD5 sum) differs
                   D Device major/minor number mismatch
                   L readLink(2) path mismatch
                   U User ownership differs
                   G Group ownership differs
                   T mTime differs
                   P caPabilities differ
    enable      Enable one or more repositories.
    disable     Disable one or more repositories.

Options:
    --force        Force installation. This allows to install package already
                   installed -- make a reinstallation or to downgrade package
                   to older version.
    --repoid <repository>
                   Select a repository, where the given package will be
                   searched for.
    --uri <uri>    Operate upon an rpm package available on remote system
                   through http or ftp service.
    -t --type (file | directory | device | symlink | fifo)
                   List only particular file type.
    --installed    Limit the query only on installed packages.

Specifying <package>:
    Package can be given in one of following notations:
        <name>
        <name>.<arch>
        <name>-<version>-<release>.<arch>           # nvra
        <name>-<epoch>:<version>-<release>.<arch>   # nevra
        <epoch>:<name>-<version>-<release>.<arch>   # envra
    Bottom most notations allow to precisely identify particular package.
"""

import docopt
import itertools

from lmi.scripts import software
from lmi.scripts.common import command
from lmi.scripts.common import errors
from lmi.scripts.common import formatter
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

class PkgLister(command.LmiInstanceLister):
    DYNAMIC_PROPERTIES = True
    ARG_ARRAY_SUFFIX = '_array'

    def execute(self, ns,
            _available=False,
            _all=False,
            _repoid=None,
            _allow_duplicates=False,
            package_array=None):
        properties = (
                ('NEVRA', 'ElementName'),
                ('Summary', 'Caption'))
        if package_array:
            package_generators = []
            for pkg_spec in package_array:
                exact_match = any(reg.match(pkg_spec) for reg in (
                        software.RE_ENVRA, software.RE_NEVRA, software.RE_NA))
                generator = (   i.to_instance()
                            for i in software.find_package(ns,
                                    pkg_spec=pkg_spec,
                                    allow_duplicates=_allow_duplicates,
                                    exact_match=exact_match))
                if _available and not _repoid:
                    # filter out installed packages
                    # if repoid is given, there's no need to filter them out
                    generator = (i for i in generator if i.InstallDate is None)
                elif not _all and not _available:
                    # filter out not installed packages
                    generator = (  i for i in generator
                                if i.InstallDate is not None)
                # else: # _all is given - no need to filter
                package_generators.append(generator)
            instances = itertools.chain(*package_generators)

        elif _all or _available:
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
                    ('Name', 'Caption'),
                    ('Enabled', lambda i: i.EnabledState == 2))
            enabled = None
        else:
            properties = (
                    ('Repo id', 'Name'),
                    ('Name', 'Description'))
            enabled = not _disabled

        return (properties, software.list_repositories(ns, enabled))

class FileLister(command.LmiInstanceLister):
    DYNAMIC_PROPERTIES = True

    def verify_options(self, options):
        file_types = { 'all', 'file', 'directory', 'symlink', 'fifo', 'device'}
        if (   options['--type'] is not None
           and options['--type'] not in file_types):
            raise errors.LmiInvalidOptions(
                    'invalid file type given, must be one of %s' % file_types)

    def execute(self, ns, package, _type=None):
        properties = [
                ('Name'),
                ('Type', lambda i: software.FILE_TYPES[i.FileType]),
                ('FileSize', lambda i: i.FileSize),
                ('Passed', lambda i: len(i.FailedFlags) < 1)]
        if _type is not None:
            del properties[1]

        pkgs = list(software.find_package(ns, pkg_spec=package[0]))
        if len(pkgs) < 1:
            raise errors.LmiFailed(
                    'no package matching "%s" found' % package[0])
        if len(pkgs) > 1:
            LOG().warn('more than one package found for "%s": %s',
                    package[0], ', '.join(p.ElementName for p in pkgs))

        return ( properties
               , software.list_package_files(ns, pkgs[-1], file_type=_type))

class Lister(command.LmiCommandMultiplexer):
    """ List information about packages, repositories or files. """
    COMMANDS = {
            'pkgs' : PkgLister,
            'repos' : RepoLister,
            'files' : FileLister
    }

class PkgInfo(command.LmiShowInstance):
    DYNAMIC_PROPERTIES = True

    def execute(self, ns, package, _repoid=None, _installed=False):
        properties = [
                'Name',
                ('Arch', 'Architecture'),
                'Version',
                'Release',
                ('Summary', 'Caption'),
                'Description']
        pkgs = [   p.to_instance()
               for p in software.find_package(ns,
                        pkg_spec=package[0],
                        repoid=_repoid)]
        pkgs = [p for p in pkgs if not _installed or bool(p.InstallDate)]
        if len(pkgs) < 1:
            raise errors.LmiFailed('no such package "%s" found' % package[0])
        if len(pkgs) > 1:
            LOG().warn('more than one package found for "%s" : %s',
                    package[0], ', '.join(p.ElementName for p in pkgs))

        return (properties, pkgs[-1])

class RepoInfo(command.LmiShowInstance):
    CALLABLE = software.get_repository
    PROPERTIES = (
            ('Repository Id', 'Name'),
            ('Name', 'Caption'),
            ('URL', 'AccessInfo'),
            ('Enabled', lambda i: i.EnabledState == 2),
            'Description')

    def transform_options(self, options):
        options['repoid'] = options.pop('<repository>')[0]

class Show(command.LmiCommandMultiplexer):
    """ Show information about packages or repositories. """
    COMMANDS = { 'pkg' : PkgInfo, 'repo' : RepoInfo }

class Install(command.LmiCheckResult):
    ARG_ARRAY_SUFFIX = '_array'

    def check_result(self, options, result):
        """
        :param result: (``list``) List of packages installed. For ``--uri``
            option, this should contain 1 argument equal to --uri. Otherwise we
            expect the same list as ``<package_array>``.
        """
        if options['--uri']:
            return [options['--uri']] == result
        if options['<package_array>'] != result:
            return (False, ('failed to install packages: %s' %
                    ", ".join(set(options['<package_array>']) - set(result))))
        return True

    def execute(self, ns,
            package_array=None,
            _uri=None,
            _force=False,
            _repoid=None):
        installed = []
        if _uri is not None:
            package_array = []
            try:
                software.install_from_uri(ns, _uri, force=_force)
                installed.append(_uri)
            except errors.LmiFailed as err:
                LOG().warn('failed to install "%s": %s', _uri, err)

        for pkg_spec in package_array:
            identities = list(software.find_package(ns,
                pkg_spec=pkg_spec,
                repoid=_repoid))
            if len(identities) < 1:
                LOG().warn('failed to find any matching package for "%s",'
                    ' skipping', pkg_spec)
                continue
            if len(identities) > 1:
                LOG().warn('more than one package found for "%s": %s',
                        pkg_spec,
                        ', '.join(software.get_package_nevra(i)
                            for i in identities))
            try:
                software.install_package(ns, identities[-1], force=_force)
                installed.append(pkg_spec)
            except errors.LmiFailed as err:
                LOG().warn('failed to install "%s": %s', pkg_spec, err)

        return installed

class Update(command.LmiCheckResult):
    ARG_ARRAY_SUFFIX = '_array'

    def check_result(self, options, result):
        """
        :param result: (``list``) List of packages installed. For ``--uri``
            option, this should contain 1 argument equal to --uri. Otherwise we
            expect the same list as ``<package_array>``.
        """
        if options['<package_array>'] != result:
            return (False, ('failed to update packages: %s' %
                    ", ".join(set(options['<package_array>']) - set(result))))
        return True

    def execute(self, ns,
            package_array=None,
            _force=False,
            _repoid=None):
        installed = []

        for pkg_spec in package_array:
            identities = list(software.find_package(ns,
                pkg_spec=pkg_spec,
                repoid=_repoid))
            if len(identities) < 1:
                LOG().warn('failed to find any matching package for "%s",'
                    ' skipping', pkg_spec)
                continue
            if len(identities) > 1:
                LOG().warn('more than one package found for "%s": %s',
                        pkg_spec,
                        ', '.join(software.get_package_nevra(i)
                            for i in identities))
            try:
                software.install_package(ns,
                        identities[-1],
                        force=_force,
                        update=True)
                installed.append(pkg_spec)
            except errors.LmiFailed as err:
                LOG().warn('failed to update "%s": %s', pkg_spec, err)

        return installed

class Remove(command.LmiCheckResult):
    ARG_ARRAY_SUFFIX = '_array'

    def check_result(self, options, result):
        if options['<package_array>'] != result:
            return (False, ('failed to remove packages: %s' %
                    ", ".join(set(options['<package_array>']) - set(result))))
        return True

    def execute(self, ns, package_array=None):
        """
        :rtype: (``list``) Packages from ``package_array``, that were
            successfuly removed.
        """
        removed = []
        for pkg_spec in package_array:
            identities = list(software.find_package(ns,
                pkg_spec=pkg_spec))
            if len(identities) < 1:
                LOG().warn('failed to find any matching package for "%s",'
                    ' skipping', pkg_spec)
                continue
            if len(identities) > 1:
                LOG().warn('more than one package found for "%s": %s',
                        pkg_spec,
                        ', '.join(software.get_package_nevra(i)
                            for i in identities))
            for identity in identities:
                try:
                    software.remove_package(ns, identity)
                    removed.append(pkg_spec)
                except errors.LmiFailed as err:
                    LOG().warn('failed to remove "%s": %s', pkg_spec, err)
        return removed

class Verify(command.LmiLister):
    ARG_ARRAY_SUFFIX = '_array'
    COLUMNS = ('Result', 'Failed file path')

    def execute(self, ns, package_array=None):
        for pkg_spec in package_array:
            identities = list(
                        p.to_instance()
                    for p in software.find_package(ns, pkg_spec=pkg_spec))
            # filter out installed
            identities = [p for p in identities if p.InstallDate is not None]
            if len(identities) < 1:
                LOG().warn('failed to find any matching package for "%s",'
                    ' skipping', pkg_spec)
                continue
            if len(identities) > 1:
                LOG().warn('more than one package found for "%s": %s', pkg_spec,
                        ", ".join(software.get_package_nevra(i)
                            for i in identities))
            failed_checks = list(software.verify_package(ns, identities[-1]))
            if len(failed_checks):
                yield formatter.NewTableCommand(title=pkg_spec)
                for file_check in failed_checks:
                    yield ( software.render_failed_flags(file_check.FailedFlags)
                          , file_check.Name)
            else:
                LOG().debug('package "%s" passed', pkg_spec)

Software = command.register_subcommands(
        'Software', __doc__,
        { 'list'    : Lister
        , 'show'    : Show
        , 'install' : Install
        , 'update'  : Update
        , 'remove'  : Remove
        , 'verify'  : Verify
        }
    )
