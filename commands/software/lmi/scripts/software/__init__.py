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

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

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
            raise LmiFailed('no such repository "%s"' % kwargs['repo'])
        repos = [inst]
    else:
        repos = ns.LMI_SoftwareIdentityResource.instances()

    pkg_names = []
    data = defaultdict(list)    # (pkg_name, [instance, ...])
    for repo in repos:
        if repo.EnabledState != \
                ns.LMI_SoftwareIdentityResource.EnabledStateValues.Enabled:
            continue                  # skip disabled repositories
        for iname in repo.associator_names(
                Role="AvailableSAP", ResultRole="ManagedElement",
                ResultClass="LMI_SoftwareIdentity"):
            identity = iname.to_instance()
            if not allow_installed and identity.InstallDate:
                continue
            heapq.heappush(pkg_names, identity)
            identities = data[identity.Name]
            if allow_duplicates:
                identities.append(identity)
            else:
                identities[:] = [identity]

    for pkg_name in pkg_names:
        for identity in data[pkg_name]:
            yield identity

def list_repos(ns, enabled=True):
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

def show_pkg(ns, pkg_array, repo=None):
    """
    TODO
    """
    pass
