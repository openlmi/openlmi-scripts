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
LMI service provider client library.
"""

from lmi.shell import LMIInstance
from lmi.shell import LMIInstanceName
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

SERVICE_KINDS = {'all', 'enabled', 'disabled', 'oneshot'}

def invoke_on_service(ns, method, service, description):
    """
    Invoke parameter-less method on given service.

    :param string method: Name of method of ``LMI_Service`` to invoke.
    :param service: Name of service or an instance to operate upon.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    :param string description: Description of what has been done with
        service. This is used just for logging.
    :returns: Success flag.
    :rtype: boolean
    """
    inst = get_service(ns, service)
    service = inst.Name
    res = getattr(inst, method)()
    if res == 0:
        LOG().debug('%s service "%s" on hostname "%s"',
                description, service, ns.hostname)
    return res

def list_services(ns, kind='enabled'):
    """
    List services. Yields service instances.

    :param string kind: What kind of services to list. Possible options are:

        * 'enabled'  - list only enabled services
        * 'disabled' - list only disabled services
        * 'oneshot'  - list only oneshot services
        * 'all'      - list all services

    :returns: Instances of ``LMI_Service``.
    :rtype: generator over :py:class:`lmi.shell.LMIInstance`.
    """
    if not isinstance(kind, basestring):
        raise TypeError("kind must be a string")
    if not kind in SERVICE_KINDS:
        raise ValueError("kind must be one of %s" % SERVICE_KINDS)
    for service in sorted(ns.LMI_Service.instances(), key=lambda i: i.Name):
        if kind == 'disabled' and service.EnabledDefault != \
                ns.LMI_Service.EnabledDefaultValues.Disabled:
            continue
        if kind == 'oneshot' and service.EnabledDefault != \
                ns.LMI_Service.EnabledDefaultValues.NotApplicable:
            continue
        if kind == 'enabled' and service.EnabledDefault != \
                ns.LMI_Service.EnabledDefaultValues.Enabled:
            # list only enabled
            continue
        yield service

def start_service(ns, service):
    """
    Start service.

    :param service: Service name.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    """
    return invoke_on_service(ns, 'StartService', service, 'started')

def stop_service(ns, service):
    """
    Stop service.

    :param string service: Service name or instance.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    """
    return invoke_on_service(ns, 'StopService', service, 'stopped')

def restart_service(ns, service, just_try=False):
    """
    Restart service.

    :param service: Service name or instance.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    :param boolean just_try: When ``False``, the service will be started even
        if it is not running. Otherwise only running service will be
        restarted.
    """
    method_name = 'RestartService'
    if just_try:
        method_name = 'Try' + method_name
    return invoke_on_service(ns, method_name, service, 'restarted')

def reload_service(ns, service, force=False, just_try=False):
    """
    Reload service.

    :param service: Service name or instance.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    :param boolean force: Whether the service should be restarted if the
        reload can no be done.
    :param boolean just_try: This applies only when ``force is True``.
        If ``True``, only the the running service will be restarted. Nothing
        is done for stopped service.
    """
    if force:
        if just_try:
            method_name = 'ReloadOrTryRestart'
        else:
            method_name = 'ReloadOrRestart'
    else:
        method_name = 'Reload'
    return invoke_on_service(ns, method_name, service, 'reloaded')

def get_service(ns, service):
    """
    Return :py:class:`lmi.shell.LMIInstance` object matching the given
    service name.

    :param string service: Service name.
    """
    if isinstance(service, basestring):
        cs = ns.Linux_ComputerSystem.first_instance_name()
        iname = ns.LMI_Service.new_instance_name({
            "Name": service,
            "CreationClassName" : "LMI_Service",
            "SystemName" : cs.path['Name'],
            "SystemCreationClassName" : cs.path['CreationClassName']
        })
        inst = iname.to_instance()
        if inst is None:
            raise LmiFailed('No such service "%s"' % service)
    elif isinstance(service, (LMIInstance, LMIInstanceName)):
        inst = service
        service = inst.Name
        if isinstance(inst, LMIInstanceName):
            inst = inst.to_instance()
    else:
        raise TypeError("service must be either string or ``LMIInstanceName``")

    return inst

