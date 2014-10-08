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
# Authors: Michal Minar <miminar@redhat.com>
#
"""
System software management.

Usage:
    %(cmd)s search [(--repoid <repository>)] [--allow-duplicates]
        [(--installed | --available)] <package>...
    %(cmd)s list (--help | <what> [<args>...])
    %(cmd)s show (--help | <what> [<args>...])
    %(cmd)s install [--force] [--repoid <repository>] <package> ...
    %(cmd)s install --uri <uri>
    %(cmd)s update [--force] [--repoid <repository>] <package> ...
    %(cmd)s remove <package> ...
    %(cmd)s verify <package> ...
    %(cmd)s enable <repository> ...
    %(cmd)s disable <repository> ...

Commands:
    search      Search packages. Produces a list of packages matching given
                package specifications (see below). All packages with name with
                given pattern as a substring will match. Allows filtering by
                repository. By default only newest packages will be printed.
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

                   * S file Size differs
                   * M Mode differs (includes permissions and file type)
                   * 5 digest (formerly MD5 sum) differs
                   * D Device major/minor number mismatch
                   * L readLink(2) path mismatch
                   * U User ownership differs
                   * G Group ownership differs
                   * T mTime differs
                   * P caPabilities differ

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
    --installed    Limit the query to installed packages only.
    --available    Limit the query just to not installed packages.
    --help         Get a detailed help for subcommand.

Specifying <package>:
    Package can be given in one of following notations:

        * <name>
        * <name>.<arch>
        * <name>-<version>-<release>.<arch>           # nvra
        * <name>-<epoch>:<version>-<release>.<arch>   # nevra
        * <epoch>:<name>-<version>-<release>.<arch>   # envra

    Bottom most notations allow to precisely identify particular package.
"""

from lmi.scripts import software
from lmi.scripts.common import command
from lmi.scripts.common import errors
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.software.cmd_list import Lister

LOG = get_logger(__name__)

class Search(command.LmiLister):
    CONNECTION_TIMEOUT = 10*60   # timeout after 10 minutes
    ARG_ARRAY_SUFFIX = '_array'

    def execute(self, ns, package_array,
            _allow_duplicates=False,
            _installed=False,
            _available=False,
            _repoid=None):
        if _installed or _available:
            _installed = not _available
        else:
            _installed = None
        if _installed is None:
            yield ('NEVRA', 'Installed', 'Summary')
        else:
            yield ('NEVRA', 'Summary')
        for pkg_spec in package_array:
            for pkg in software.find_package(ns,
                    allow_duplicates=_allow_duplicates,
                    exact_match=False,
                    installed=_installed,
                    pkg_spec=pkg_spec,
                    repoid=_repoid):
                inst = pkg.to_instance()
                nevra = software.get_package_nevra(inst)
                if _installed is None:
                    yield (nevra,
                        'Yes' if software.is_package_installed(inst) else 'No',
                        inst.Caption)
                else:
                    yield (nevra, inst.Caption)

class PkgInfo(command.LmiShowInstance):
    CONNECTION_TIMEOUT = 4*60   # timeout after 4 minutes
    DYNAMIC_PROPERTIES = True

    def execute(self, ns, package, _repoid=None, _installed=False):
        def _render_installed(package):
            result = "No"
            if software.get_backend(ns) == software.BACKEND_YUM and \
                    package.InstallDate is not None:
                result = package.InstallDate.datetime.strftime(
                        '%a %b %d/%Y  %H:%M')
            elif software.get_backend(ns) == software.BACKEND_PACKAGEKIT and \
                    software.is_package_installed(package):
                result = "Yes"
            return result

        properties = [
                'Name',
                ('Arch', 'Architecture'),
                'Version',
                'Release',
                ('Summary', 'Caption'),
                ('Installed', _render_installed),
                'Description']
        pkgs = [   p.to_instance()
               for p in software.find_package(ns,
                        pkg_spec=package,
                        repoid=_repoid)]
        pkgs = [p for p in pkgs if not _installed or \
                software.is_package_installed(p)]
        if len(pkgs) < 1:
            raise errors.LmiFailed('No such package "%s" found.' % package)
        if len(pkgs) > 1:
            LOG().warn('More than one package found for "%s" : %s',
                    package, ', '.join(p.ElementName for p in pkgs))

        return (properties, pkgs[-1])

class RepoInfo(command.LmiShowInstance):
    CONNECTION_TIMEOUT = 4*60   # timeout after 4 minutes
    CALLABLE = software.get_repository
    PROPERTIES = (
            ('Repository Id', 'Name'),
            ('Name', 'Caption'),
            ('URL', 'AccessInfo'),
            ('Enabled', lambda i: i.EnabledState == 2),
            'Description')

    def transform_options(self, options):
        options['repoid'] = options.pop('<repository>')

class Show(command.LmiCommandMultiplexer):
    """
    Show details of package or repository.

    Usage:
        %(cmd)s pkg [--installed | --repoid <repository>] <package>
        %(cmd)s repo <repository>

    Options:
        --installed            Do not search available packages. This speeds up
                               the operation when only installed packages shall
                               be queried.
        --repoid <repository>  Search just this repository.
    """
    COMMANDS = { 'pkg' : PkgInfo, 'repo' : RepoInfo }
    OWN_USAGE = True

def for_each_package_specs(ns, pkg_specs, info, func,
        repoid=None, just_on_installed=True):
    """
    Iterate over package specification strings, find them on remote host,
    make them into ``LMI_SoftwareIdentity``, and pass them to given function.

    :param list pkg_specs: Package specification strings.
    :param string info: What is done with package. This is used in log messages.
    :param callable func: Any callable taking instance of
        ``LMI_SoftwareIdentity`` as the first and only argument.
    :param string repoid: Optional repository id used in a search
        for corresponding software identity.
    :param boolean just_on_installed: Skip uninstalled software identities
        found.
    :returns: Pair with list containing a subset of ``pkg_specs`` with items,
        that were processed successfuly and a list of errors for other packages.
    :rtype: tuple
    """
    done_on = []
    failed = []
    for pkg_spec in pkg_specs:
        if just_on_installed:
            identities = [
                        i.to_instance()
                    for i in software.find_package(ns,
                        pkg_spec=pkg_spec, repoid=repoid)]

            identities = [p for p in identities
                            if software.is_package_installed(p)]
        else:
            identities = list(software.find_package(ns,
                pkg_spec=pkg_spec, repoid=repoid))
        if len(identities) < 1:
            if just_on_installed:
                msg = 'No such installed package "%s".' % pkg_spec
            else:
                msg = 'Failed to find package "%s".' % pkg_spec
            LOG().warn(msg + ' Skipping.')
            failed.append(msg)
            continue
        if len(identities) > 1:
            LOG().debug('More than one package found for "%s": %s',
                    pkg_spec,
                    ', '.join(software.get_package_nevra(i)
                        for i in identities))
        try:
            func(identities[-1])
            done_on.append(pkg_spec)
        except errors.LmiFailed as err:
            failed.append(err)
    return done_on, failed

class Install(command.LmiCheckResult):
    CONNECTION_TIMEOUT = 4*60   # timeout after 4 minutes
    ARG_ARRAY_SUFFIX = '_array'

    def check_result(self, options, result):
        """
        :param tuple result: A pair of (done, failed) where the former is a
            subset of packages given on command line and the latter a list of
            errors for the rest. For ``--uri`` option, the first item should
            contain 1 argument equal to uri. Otherwise we expect the same list
            as ``<package_array>``.
        """
        done_on, failed = result
        if options['--uri']:
            return [options['--uri']] == done_on
        if options['<package_array>'] != done_on:
            if len(options['<package_array>']) == 1:
                return (False, failed[0])
            return (False, ('Failed to install packages: %s' %
                    ", ".join(set(options['<package_array>']) - set(done_on))))
        return True

    def execute(self, ns,
            package_array=None,
            _uri=None,
            _force=False,
            _repoid=None):
        if _uri is not None:
            try:
                software.install_from_uri(ns, _uri, force=_force)
                return ([_uri], [])
            except errors.LmiFailed as err:
                LOG().warn('Failed to install "%s": %s', _uri, err)
                return ([], [err])

        else:
            return for_each_package_specs(ns, package_array, 'install',
                    lambda identity: software.install_package(
                        ns, identity, force=_force),
                    repoid=_repoid,
                    just_on_installed=False)

class Update(command.LmiCheckResult):
    CONNECTION_TIMEOUT = 4*60   # timeout after 4 minutes
    ARG_ARRAY_SUFFIX = '_array'

    def check_result(self, options, result):
        """
        :param tuple result: A pair of (done, failed) where the former is a
            subset of packages given on command line and the latter a list of
            errors for the rest. For ``--uri`` option, the first item should
            contain 1 argument equal to uri. Otherwise we expect the same list
            as ``<package_array>``.
        """
        done_on, failed = result
        if options['<package_array>'] != done_on:
            if len(options['<package_array>']) == 1:
                return (False, failed[0])
            return (False, ('Failed to update packages: %s' %
                    ", ".join(set(options['<package_array>']) - set(done_on))))
        return True

    def execute(self, ns,
            package_array=None,
            _force=False,
            _repoid=None):
        return for_each_package_specs(ns, package_array, 'update',
                lambda identity: software.install_package(ns,
                        identity,
                        force=_force,
                        update=True),
                repoid=_repoid)

class Remove(command.LmiCheckResult):
    ARG_ARRAY_SUFFIX = '_array'

    def check_result(self, options, result):
        """
        :param tuple result: A pair of (done, failed) where the former is a
            subset of packages given on command line and the latter a list of
            errors for the rest. For ``--uri`` option, the first item should
            contain 1 argument equal to uri. Otherwise we expect the same list
            as ``<package_array>``.
        """
        done_on, failed = result
        if options['<package_array>'] != done_on:
            if len(options['<package_array>']) == 1:
                return (False, failed[0])
            return (False, ('Failed to remove packages: %s' %
                    ", ".join(set(options['<package_array>']) - set(done_on))))
        return True

    def execute(self, ns, package_array):
        """
        :rtype: (``list``) Packages from ``package_array``, that were
            successfuly removed.
        """
        return for_each_package_specs(ns, package_array, 'remove',
                lambda identity: software.remove_package(ns, identity))

class Verify(command.LmiLister):
    CONNECTION_TIMEOUT = 4*60   # timeout after 4 minutes
    ARG_ARRAY_SUFFIX = '_array'
    COLUMNS = []

    def execute(self, ns, package_array):
        identity_checks = []
        def _verify_identity(identity):
            failed_checks = list(software.verify_package(ns, identity))
            identity_checks.append((identity, failed_checks))

        for_each_package_specs(ns, package_array, 'verify', _verify_identity)
        for identity, failed_checks in identity_checks:
            if len(failed_checks):
                yield fcmd.NewTableCommand(title=identity.ElementName)
                for file_check in failed_checks:
                    yield ( software.render_failed_flags(file_check.FailedFlags)
                          , file_check.Name)
            elif self.app.config.verbose:
                yield fcmd.NewTableCommand(title=identity.ElementName)
                yield ('', 'passed')
            else:
                LOG().debug('Package "%s" passed.', identity.ElementName)

class ChangeEnabledState(command.LmiCheckResult):
    """
    Class for 'enable' and 'disable' commands. This particular class allows
    to enable repositories. To make a disable command out of it, it needs
    to be overrided with ``enable`` property returning ``False``.
    """
    CONNECTION_TIMEOUT = 4*60   # timeout after 4 minutes
    ARG_ARRAY_SUFFIX = '_array'

    @property
    def enable(self):
        """ Whether to enable or disable repository. """
        return True

    def check_result(self, options, result):
        if options['<repository_array>'] != result:
            return (False, ('Failed to %s repositories: %s' % (
                'enable' if self.enable else 'disable',
                ", ".join(set(options['<repository_array>']) - set(result)))))
        return True

    def execute(self, ns, repository_array):
        modified = []
        for repoid in repository_array:
            try:
                repo = software.get_repository(ns, repoid)
                software.set_repository_enabled(ns, repo, enable=self.enable)
                modified.append(repoid)
            except errors.LmiFailed as err:
                LOG().warn(str(err))
        return modified

class DisableRepository(ChangeEnabledState):

    @property
    def enable(self):
        return False

Software = command.register_subcommands(
        'Software', __doc__,
        { 'list'    : Lister
        , 'search'  : Search
        , 'show'    : Show
        , 'install' : Install
        , 'update'  : Update
        , 'remove'  : Remove
        , 'verify'  : Verify
        , 'enable'  : ChangeEnabledState
        , 'disable' : DisableRepository
        }
    )
