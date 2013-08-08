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

def list_pkgs(ns, **kwargs):
    if not kwargs['__available'] and not kwargs['__all']:
        yield ("NEVRA", "Summary")
        cs = ns.Linux_ComputerSystem.first_instance()
        for identity in cs.associators(
                Role="System",
                ResultRole="InstalledSoftware",
                ResultClass="LMI_SoftwareIdentity"):
            yield (identity.ElementName, identity.Caption)

    if kwargs['__available'] or kwargs['__all']:
        if kwargs['repo']:
            inst = ns.LMI_SoftwareIdentityResource.first_instance(
                    key='Name', value=kwargs['repo'])
            if inst is None:
                raise LmiFailed('no such repository "%s"' % kwargs['repo'])
            repos = [inst]
        else:
            repos = ns.LMI_SoftwareIdentityResource.instances()
        yield ("NEVRA", "Repository", "Summary")
        pkg_names = []
        data = defaultdict(list)    # (pkg_name, [(nevra, repo, summary)])
        for repo in repos:
            if repo.EnabledState != 2:    # != Enabled
                continue                  # skip disabled repositories
            for iname in repo.associator_names(
                    Role="AvailableSAP", ResultRole="ManagedElement",
                    ResultClass="LMI_SoftwareIdentity"):
                identity = iname.to_instance()
                if not kwargs['__all'] and identity.InstallDate is None:
                    continue
                heapq.push(pkg_names, identity.Name)
                info = ( identity.path["InstanceID"]
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

def list_repos(ns, __disabled, __all):
    if __all:
        yield ('Repo id', 'Name', 'Enabled')
    else:
        yield ('Repo id', 'Name')
    for repo in ns.LMI_SoftwareIdentityResource.instances():
        if not __disabled and not __all and repo.EnabledState != 2:
            continue
        if __disabled and repo.EnabledState != 3:
            continue
        if __all:
            yield (repo.Name, repo.Caption, repo.EnabledState == 2)
        else:
            yield (repo.Name, repo.Caption)
