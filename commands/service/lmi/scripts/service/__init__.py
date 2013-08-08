# Software Management Providers
#
# Copyright (ns) 2012-2013 Red Hat, Inc.  All rights reserved.
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

def _invoke_on_service(ns, method, service, description):
    """
    Invoke parameter-less method on given service.

    :param method: (``str``) Name of method of LMI_Service to invoke.
    :param service: (``str``) Name of service to operate on.
    :param description: (``str``) Description of what has been done with service.
        This is used just for logging.
    """
    inst = ns.LMI_Service.first_instance(key="Name", value=service)
    if inst is None:
        raise LmiFailed('No such service "%s"' % service)
    res = getattr(inst, method)()
    if res == 0:
        LOG().debug('%s service "%s" on hostname "%s"',
                description, service, ns.hostname)
    return res

def list(ns, all, disabled, oneshot):
    """
    List services. Only enabled ones are listed at default.

    :param all: (``bool``) List all services available.
    :param disabled: (``bool``) List only disabled services.
    :param oneshot: (``bool``) List only oneshot services.
    """
    for s in sorted(ns.LMI_Service.instances(), key=lambda i: i.Name):
        if disabled and s.EnabledDefault != 3:
            continue
        if oneshot and s.EnabledDefault != 5:
            continue
        if not any((disabled, all, oneshot)) and s.EnabledDefault != 2:
            # list only enabled
            continue
        yield (s.Name, s.Started, s.Status)

def start(ns, service):
    """
    Start service.

    :param service: (``str``) Service name.
    """
    return _invoke_on_service(ns, 'StartService', service, 'started')

def stop(ns, service):
    """
    Stop service.

    :param service: (``str``) Service name.
    """
    return _invoke_on_service(ns, 'StopService', service, 'stopped')

def restart(ns, service):
    """
    Restart service.

    :param service: (``str``) Service name.
    """
    return _invoke_on_service(ns, 'RestartService', service, 'restarted')

def get_instance(ns, service):
    """
    Return LmiInstance object matching the given service.

    :param service: (``str``) Service name.
    """
    inst = ns.LMI_Service.first_instance(key="Name", value=service)
    if inst is None:
        raise LmiFailed('No such service "%s"' % service)
    return inst
    
