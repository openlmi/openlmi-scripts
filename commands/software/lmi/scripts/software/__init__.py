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
LMI software provider client library.
"""

from collections import defaultdict
import heapq
import re
import time

from lmi.shell import LMIInstance, LMIInstanceName
from lmi.shell import LMIJob
from lmi.shell import LMIMethod
from lmi.shell import LMIUtil
from lmi.shell import LMIExceptions
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger

# matches <name>.<arch>
RE_NA  = re.compile(r'^(?P<name>.+)\.(?P<arch>[^.]+)$')
# matches both nevra and nvra
RE_NEVRA = re.compile(
    r'^(?P<name>.+)-(?P<evra>((?P<epoch>\d+):)?(?P<version>[0-9.]+)'
    r'-(?P<release>.+)\.(?P<arch>[^.]+))$')
RE_ENVRA = re.compile(
    r'^(?P<epoch>\d+):(?P<name>.+)-(?P<evra>(?P<version>[0-9.]+)'
    r'-(?P<release>.+)\.(?P<arch>[^.]+))$')

FILE_TYPES = (
    'Unknown',
    'File',
    'Directory',
    'Symlink',
    'FIFO',
    'Character Device',
    'Block Device'
)

LOG = get_logger(__name__)

def _wait_for_job_finished(job):
    """
    This function waits for asynchronous job to be finished.

    :param job: (``LMIInstance``) Instance of ``LMI_SoftwareJob``.
    """
    if not isinstance(job, LMIInstance):
        raise TypeError("job must be an LMIInstance")
    LOG().debug('waiting for a job "%s" to finish', job.InstanceId)
    sleep_time = 0.5
    while not LMIJob.lmi_is_job_finished(job):
        # Sleep, a bit longer in every iteration
        time.sleep(sleep_time)
        if sleep_time < LMIMethod._POLLING_ADAPT_MAX_WAITING_TIME:
            sleep_time *= 1.5
        (refreshed, _, errorstr) = job.refresh()
        if not refreshed:
            raise LMIExceptions.LMISynchroMethodCallError(errorstr)

def get_package_nevra(package):
    """
    Get a nevra from an instance of ``LMI_SoftwareIdentity``.

    :param package: (``LMIInstance``) Instance or instance name of
        ``LMI_SoftwareIdentity`` representing package to install.
    :rtype: (``str``) Nevra string of particular package.
    """
    if not isinstance(package, (LMIInstanceName, LMIInstance)):
        raise TypeError("package must be an instance or instance name")
    return (    package.path['InstanceId']
           if   isinstance(package, LMIInstanceName)
           else package.InstanceId)[len('LMI:LMI_SoftwareIdentity:'):]

def list_installed_packages(ns):
    """
    Yields instances of LMI_SoftwareIdentity representing installed packages.
    """
    for identity in ns.Linux_ComputerSystem.first_instance().associators(
            Role="System",
            ResultRole="InstalledSoftware",
            ResultClass="LMI_SoftwareIdentity"):
        yield identity

def list_available_packages(ns,
        allow_installed=False,
        allow_duplicates=False,
        repoid=None):
    """
    Yields instances of LMI_SoftwareIdentity representing available packages.

    :param allow_installed: (``bool``) Whether to include available packages
        that are installed.
    :param allow_duplicates: (``bool``) Whether to include duplicates packages
        (those having same name and architecture). Otherwise only the newest
        packages available for each (name, architecture) pair will be contained
        in result.
    :param repoid: (``str``) Repository identification string. This will filter
        available packages just for those provided by this repository.
    """
    if repoid is not None:
        inst = ns.LMI_SoftwareIdentityResource.first_instance(
                key='Name', value=repoid)
        if inst is None:
            raise LmiFailed('no such repository "%s"' % repoid)
        repos = [inst]
    else:
        repos = ns.LMI_SoftwareIdentityResource.instances()

    pkg_names = []
    data = defaultdict(list)    # (pkg_name, [instance, ...])
    for repo in repos:
        if repo.EnabledState != \
                ns.LMI_SoftwareIdentityResource.EnabledStateValues.Enabled:
            continue                  # skip disabled repositories
        for identity in repo.associators(
                Role="AvailableSAP", ResultRole="ManagedElement",
                ResultClass="LMI_SoftwareIdentity"):
            if not allow_installed and identity.InstallDate:
                continue
            if not identity.Name in data:
                heapq.heappush(pkg_names, identity.Name)
            identities = data[identity.Name]
            if allow_duplicates:
                identities.append(identity)
            else:
                identities[:] = [identity]

    for pkg_name in pkg_names:
        for identity in data[pkg_name]:
            yield identity

def pkg_spec_to_filter(pkg_spec):
    """
    Converts package specification to a set of keys, that can be used to
    query package properties.

    :param pkg_spec: (``str``) Package specification (see usage). Only keys
        given in this string will appear in resulting dictionary.
    :rtype: (``dict``) Dictionary with possible keys being a subset of
        following: ``{'name', 'epoch', 'version', 'release', 'arch'}``.
    """
    if not isinstance(pkg_spec, basestring):
        raise TypeError("pkg_spec must be a string")
    result = {}
    for notation in ('envra', 'nevra'):
        match = globals()['RE_' + notation.upper()].match(pkg_spec)
        if match:
            for key in ('name', 'version', 'release', 'arch'):
                result[key] = match.group(key)
            if match.group('epoch'):
                result['epoch'] = match.group('epoch')
            return result
    match = RE_NA.match(pkg_spec)
    if match:
        for key in ('name', 'arch'):
            result[key] = match.group(key)
        return result
    result['name'] = pkg_spec
    return result

def find_package(ns, allow_duplicates=False, exact_match=True, **kwargs):
    """
    Yields just a limited set of packages matching particular filter.
    Keyword arguments are used to specify this filter, which can contain
    following keys:

        * name - package name
        * epoch - package's epoch
        * version - version of package
        * release - release of package
        * arch - requested architecture of package
        * nevra - string containing all previous keys in following notation:
            <name>-<epoch>:<version>-<release>.<arch>
        * envra - similar to nevra, the notation is different:
            <epoch>:<name>-<version>-<release>.<arch>   # envra
        * repoid - repository identification string, where package must be
            available
        * pkg_spec - one of:
            * <name>
            * <name>.<arch>
            * <name>-<version>-<release>.<arch>           # nvra
            * <name>-<epoch>:<version>-<release>.<arch>   # nevra
            * <epoch>:<name>-<version>-<release>.<arch>   # envra

    :param allow_duplicates: (``bool``) Whether the output shall contain
        multiple versions of the same packages identified with
        ``<name>.<architecture>``.
    :param exact_match: (``bool``) Whether the ``name`` key shall be tested for
        exact match. If ``False`` it will be tested for inclusion.
    :rtype: (``LmiInstanceName``) Generator over instance names of
        ``LMI_SoftwareIdentity``.
    """
    opts = {}
    for key in ('name', 'epoch', 'version', 'release', 'arch'):
        if key in kwargs:
            opts[key] = kwargs.pop(key)
    repoid = kwargs.pop('repoid', None)
    if repoid:
        repo_iname = ns.LMI_SoftwareIdentityResource.first_instance_name(
                {'Name' : repoid})
        opts['repository'] = repo_iname.path
    if 'envra' in kwargs:   # takes precedence over pkg_spec and nevra
        if not RE_ENVRA.match(kwargs['envra']):
            raise ValueError('invalid envra string "%s"' % kwargs['envra'])
        kwargs['pkg_spec'] = kwargs.pop("envra")
    elif 'nevra' in kwargs: # takes precedence over pkg_spec
        if not RE_NEVRA.match(kwargs['nevra']):
            raise ValueError('invalid nevra string "%s"' % kwargs['nevra'])
        kwargs['pkg_spec'] = kwargs.pop("nevra")
    if 'pkg_spec' in kwargs:
        pkg_spec = kwargs.pop('pkg_spec')
        opts.update(pkg_spec_to_filter(pkg_spec))
    if not opts:
        raise LmiFailed("no supported package query key given")
    if 'arch' in opts:
        opts['architecture'] = opts.pop('arch')
    ret = ns.LMI_SoftwareInstallationService.first_instance() \
            .FindIdentity(
                    AllowDuplicates=allow_duplicates,
                    ExactMatch=exact_match, **opts)
    for identity in ret.rparams['Matches']:
        yield identity

def list_repositories(ns, enabled=True):
    """
    Yields instances of LMI_SoftwareIdentityResource representing
    software repositories.

    :param enabled: (``bool`` or ``None``) Whether to list only enabled
        repositories. If ``False`` only disabled repositories shall be listed.
        If ``None``, all repositories shall be listed.
    """
    if not isinstance(enabled, bool) and enabled is not None:
        raise TypeError("kind must be a boolean or None")

    for repo in ns.LMI_SoftwareIdentityResource.instances():
        if enabled and repo.EnabledState != \
                ns.LMI_SoftwareIdentityResource.EnabledStateValues.Enabled:
            continue
        if enabled is False and repo.EnabledState != \
                ns.LMI_SoftwareIdentityResource.EnabledStateValues.Disabled:
            continue
        yield repo

def list_package_files(ns, package, file_type=None):
    """
    Get a list of files belonging to package. Yields instances of
        LMI_SoftwareIdentityFileCheck.

    :param package: (``LMIInstance``) Instance or instance name of
        ``LMI_SoftwareIdentity``.
    :param file_type: Either an index to ``FILE_TYPES`` array or one of:
        ``{ "all", "file", "directory", "symlink", "fifo", "device" }``.
    """
    if not isinstance(package, (LMIInstance, LMIInstanceName)):
        raise TypeError("package must be an LMIInstance")
    file_types = ['file', 'directory', 'symlink', 'fifo', 'device']
    if file_type is not None:
        if isinstance(file_type, (int, long)):
            if file_type < 1 or file_type >= len(FILE_TYPES):
                raise ValueError('invalid file_type value "%d"' % file_type)
        elif isinstance(file_type, basestring):
            if file_type.lower() == 'all':
                file_type = None
            elif not file_type.lower() in file_types:
                raise ValueError('file_type must be one of "%s", not "%s"' %
                        (set(file_types), file_type))
            else:
                file_type = file_types.index(file_type.lower()) + 1
    if isinstance(package, LMIInstanceName):
        package = package.to_instance()
    if package.InstallDate is None:
        raise LmiFailed('can not list files of not installed package "%s"' %
                package.ElementName)
    for file_inst in package.associators(
            Role="Element",
            ResultRole="Check",
            ResultClass="LMI_SoftwareIdentityFileCheck"):
        if file_type is not None and file_inst.FileType != file_type:
            continue
        yield file_inst

def get_repository(ns, repoid):
    """
    Return an instance of repository identified by its identification string.

    :param repoid: (``str``) Identification string of repository.
    :rtype: (``LMIInstance``) Instance of ``LMI_SoftwareIdentityResource``.
    """
    if not isinstance(repoid, basestring):
        raise TypeError("repoid must be a string")
    repo = ns.LMI_SoftwareIdentityResource.first_instance({'Name' : repoid})
    if repo is None:
        raise LmiFailed('no such repository "%s"' % repoid)
    return repo

def set_repository_enabled(ns, repository, enable=True):
    """
    Enable or disable repository.

    :param repository: (``LMIInstance``) Instance of
        ``LMI_SoftwareIdentityResource``.
    :param enable: (``bool``) New value of ``EnabledState`` property.
    :rtype: (``bool``) Previous value of repository's ``EnabledState``.
    """
    if not isinstance(repository, (LMIInstance, LMIInstanceName)):
        raise TypeError("repository must be an LMIInstance")
    cls = ns.LMI_SoftwareIdentityResource
    if not LMIUtil.lmi_isinstance(repository, cls):
        raise ValueError("repository must be an instance of"
            " LMI_SoftwareIdentityResource")
    requested_state = cls.EnabledStateValues.Enabled if enable else \
            cls.EnabledStateValues.Disabled
    if repository.EnabledState != requested_state:
        results = repository.RequestStateChange(RequestedState=requested_state)
        if results.rval != 0:
            msg = 'failed to enable repository "%s" (rval=%d)' % (
                    repository.Name, results.rval)
            if results.errorstr:
                msg += ': ' + results.errorstr
            raise LmiFailed(msg)
    return repository.EnabledState

def install_package(ns, package, force=False, update=False):
    """
    Install package on system.

    :param package: (``LMIInstance``) Instance or instance name of
        ``LMI_SoftwareIdentity`` representing package to install.
    :param force: (``bool``) Whether the installation shall be done even if
        installing the same (re-installation) or older version, than already
        installed.
    :param update: (``bool``) Whether this is an update. Update fails, if
        package is not already installed on system.
    :rtype: (``LMIInstance``) Software identity installed on remote system.
    """
    if not isinstance(package, (LMIInstance, LMIInstanceName)):
        raise TypeError("package must be an LMIInstance or LMIInstanceName")
    service = ns.LMI_SoftwareInstallationService.first_instance()
    options = [4 if not update else 5]  # Install (4) or Update (5)
    if force:
        options.append(3) # Force Installation
    # we can not use synchronous invocation because the reference to a job is
    # needed
    results = service.InstallFromSoftwareIdentity(
            Source=package.path,
            Collection=ns.LMI_SystemSoftwareCollection.first_instance().path,
            InstallOptions=options)
    nevra = (    package.path['InstanceId']
            if   isinstance(package, LMIInstanceName)
            else package.InstanceId)[len('LMI:LMI_SoftwareIdentity:'):]
    if results.rval != 4096:
        msg = 'failed to %s package "%s" (rval=%d)' % (
                'update' if update else 'install', nevra, results.rval)
        if results.errorstr:
            msg += ': ' + results.errorstr
        raise LmiFailed(msg)

    job = results.rparams['Job'].to_instance()
    _wait_for_job_finished(job)
    if not LMIJob.lmi_is_job_completed(job):
        msg = 'failed to %s package "%s"' % (
                'update' if update else 'install', nevra)
        if job.ErrorDescription:
            msg += ': ' + job.ErrorDescription
        raise LmiFailed(msg)
    else:
        LOG().info('installed package "%s" on remote host "%s"',
                nevra, ns.connection.hostname)

    installed = job.associators(
            Role='AffectingElement',
            ResultRole='AffectedElement',
            ResultClass='LMI_SoftwareIdentity')
    if len(installed) < 1:
        raise LmiFailed('failed to find installed package "%s"' % nevra)
    if len(installed) > 1:
        LOG().warn('expected just one affected software identity, got: %s',
                {get_package_nevra(p) for p in installed})

    return installed[-1]

def install_from_uri(ns, uri, force=False, update=False):
    """
    Install package from URI on remote system.

    :param uri: (``str``) Identifier of RPM package available via http, https,
        or ftp service.
    :param force: (``bool``) Whether the installation shall be done even if
        installing the same (re-installation) or older version, than already
        installed.
    :param update: (``bool``) Whether this is an update. Update fails, if
        package is not already installed on system.
    """
    if not isinstance(uri, basestring):
        raise TypeError("uri must be a string")
    service = ns.LMI_SoftwareInstallationService.first_instance()
    options = [4 if not update else 5]  # Install (4) or Update (5)
    if force:
        options.append(3) # Force Installation
    results = service.SyncInstallFromURI(
            URI=uri,
            Target=ns.Linux_ComputerSystem.first_instance().path,
            InstallOptions=options)
    if results.rval != 0:
        msg = 'failed to %s package from uri (rval=%d)' % (
                'update' if update else 'install', results.rval)
        if results.errorstr:
            msg += ': ' + results.errorstr
        raise LmiFailed(msg)
    else:
        LOG().info('installed package from uri')

def remove_package(ns, package):
    """
    Uninstall given pacakge from system. ``LmiFailed`` will be raised on
    failure.

    :param package: (``LMIInstance``) Instance or instance name of
        ``LMI_SoftwareIdentity`` representing package to remove.
    """
    if not isinstance(package, (LMIInstance, LMIInstanceName)):
        raise TypeError("package must be an LMIInstance or LMIInstanceName")
    if isinstance(package, LMIInstanceName):
        package = package.to_instance()
    installed_assocs = package.reference_names(
            Role="InstalledSoftware",
            ResultClass="LMI_InstalledSoftwareIdentity")
    if len(installed_assocs) > 0:
        for assoc in installed_assocs:
            assoc.to_instance().delete()
    else:
        raise LmiFailed('given package "%s" is not installed!' %
                get_package_nevra(package))

def render_failed_flags(failed_flags):
    """
    :param failed_flags: (``list``) Value of ``FailedFlags`` property
        of ``LMI_SoftwareIdentityFileCheck``.
    :rtype: (``str``) Verification string with format matching the output
        of ``rpm -V`` command.
    """
    if 0 in failed_flags:
        return 'missing'
    result = []
    for _name, letter, flag_num in (
                ('file size',     'S', 1),
                ('file mode',     'M', 2),
                ('digest',        '5', 3),
                ('device number', 'D', 4),
                ('link target',   'L', 5),
                ('user id',       'U', 6),
                ('group id',      'G', 7),
                ('last modification time', 'T', 8),
                ('capabilities', 'P', -1)   # not yet supported by provider
            ):
        if flag_num in failed_flags:
            result.append(letter)
        else:
            result.append('.')
    return ''.join(result)

def verify_package(ns, package):
    """
    Returns the instances of ``LMI_SoftwareIdentityFileCheck`` representing
    files, that did not pass the verification.

    :param package: (``LMIInstance``) Instance or instance name of
        ``LMI_SoftwareIdentity`` representing package to verify.
    :rtype: (``list``) List of instances of ``LMI_SoftwareIdentityFileCheck``
        with not empty ``FailedFlags`` property.
    """
    if not isinstance(package, (LMIInstance, LMIInstanceName)):
        raise TypeError("package must be an LMIInstance or LMIInstanceName")
    # we can not use synchronous invocation because the reference to a job is
    # needed - for enumerating of affected software identities
    service = ns.LMI_SoftwareInstallationService.first_instance()
    results = service.VerifyInstalledIdentity(
            Source=package.path,
            Target=ns.Linux_ComputerSystem.first_instance().path)
    nevra = (    package.path['InstanceId']
            if   isinstance(package, LMIInstanceName)
            else package.InstanceId)[len('LMI:LMI_SoftwareIdentity:'):]
    if results.rval != 4096:
        msg = 'failed to verify package "%s (rval=%d)"' % (nevra, results.rval)
        if results.errorstr:
            msg += ': ' + results.errorstr
        raise LmiFailed(msg)

    job = results.rparams['Job'].to_instance()
    _wait_for_job_finished(job)
    if not LMIJob.lmi_is_job_completed(job):
        msg = 'failed to verify package "%s"' % nevra
        if job.ErrorDescription:
            msg += ': ' + job.ErrorDescription
        raise LmiFailed(msg)
    LOG().debug('verified package "%s" on remote host "%s"',
            nevra, ns.connection.hostname)

    failed = job.associators(
            Role='AffectingElement',
            ResultRole='AffectedElement',
            ResultClass='LMI_SoftwareIdentityFileCheck')
    LOG().debug('verified package "%s" on remote host "%s" with %d failures',
            nevra, ns.connection.hostname, len(failed))

    return failed
