# Storage Management Providers
#
# Copyright (C) 2012-2013 Red Hat, Inc.  All rights reserved.
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
LMI storage provider client library.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
from lmi.scripts.storage.partition import *

LOG = get_logger(__name__)

def list_pkgs(c, **kwargs):
    if not kwargs['__available'] and not kwargs['__all']:
        yield ("NEVRA", "Summary")
        cs = c.root.cimv2.Linux_ComputerSystem.first_instance()
        for identity in cs.associators(
                Role="System",
                ResultRole="InstalledSoftware",
                ResultClass="LMI_SoftwareIdentity"):
            yield (identity.ElementName, identity.Caption)

    if kwargs['__available'] or kwargs['__all']:
        if kwargs['repo']:
            inst = c.root.cimv2.LMI_SoftwareIdentityResource.first_instance(
                    key='Name', value=kwargs['repo'])
            if inst is None:
                raise LmiFailed('no such repository "%s"' % kwargs['repo'])
            repos = [inst]
        else:
            repos = c.root.cimv2.LMI_SoftwareIdentityResource.instances()
        yield ("NEVRA", "Repository", "Summary")
        pkg_names = []
        data = defaultdict(list)  # (pkg_name, [(nevra, repo, summary)])
        for repo in repos:
            if repo.EnabledState != 2:  # != Enabled
                continue  # skip disabled repositories
            for iname in repo.associator_names(
                    Role="AvailableSAP", ResultRole="ManagedElement",
                    ResultClass="LMI_SoftwareIdentity"):
                identity = iname.to_instance()
                if not kwargs['__all'] and identity.InstallDate is None:
                    continue
                heapq.push(pkg_names, identity.Name)
                info = (identity.path["InstanceID"]
                            [len("LMI:LMI_SoftwareIdentity:"):]
                       , repo.Name, identity.Caption)
                infolist = data[identity.Name]
                if kwargs['__allow_duplicates']:
                    infolist.append(out, info)
                else:
                    infolist[:] = [info]
        for pkg_name in pkg_names:
            for info in data[pkg_name]:
                yield info

def list_repos(c, __disabled, __all):
    if __all:
        yield ('Repo id', 'Name', 'Enabled')
    else:
        yield ('Repo id', 'Name')
    for repo in c.root.cimv2.LMI_SoftwareIdentityResource.instances():
        if not __disabled and not __all and repo.EnabledState != 2:
            continue
        if __disabled and repo.EnabledState != 3:
            continue
        if __all:
            yield (repo.Name, repo.Caption, repo.EnabledState == 2)
        else:
            yield (repo.Name, repo.Caption)
