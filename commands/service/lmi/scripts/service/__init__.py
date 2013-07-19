# Software Management Providers
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
# Authors: Michal Minar <miminar@redhat.com>
#
"""
LMI service provider client library.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

def _invoke_on_service(c, method, service, description):
    inst = c.root.cimv2.LMI_Service.first_instance(
            key="Name", value=service)
    if inst is None:
        raise LmiFailed('No such service "%s"' % service)
    res = getattr(inst, method)()
    if res == 0:
        LOG().debug('%s service "%s" on hostname "%s"',
                description, service, c.hostname)
    return res

def list(c, __all, __disabled, __oneshot):
    for s in sorted(c.root.cimv2.LMI_Service.instances(),
            key=lambda i: i.Name):
        if __disabled and s.EnabledDefault != 3:
            continue
        if __oneshot and s.EnabledDefault != 5:
            continue
        if not any((__disabled, __all, __oneshot)) and s.EnabledDefault != 2:
            # list only enabled
            continue
        yield (s.Name, s.Started, s.Status)

def start(c, service):
    return _invoke_on_service(c, 'StartService', service, 'started')

def stop(c, service):
    return _invoke_on_service(c, 'StopService', service, 'stopped')

def restart(c, service):
    return _invoke_on_service(c, 'RestartService', service, 'restarted')

