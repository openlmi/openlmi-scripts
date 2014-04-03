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
LMI service provider client library.
"""

import pywbem
import re

from lmi.shell import LMIInstance
from lmi.shell import LMIInstanceName
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_computer_system
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

SERVICE_KINDS = {'all', 'enabled', 'disabled'}

REQUESTED_STATE_ENABLED = 2
REQUESTED_STATE_DISABLED = 3

RE_SUFFIX = re.compile(r'\.service$')

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
    (rval, _, errorstr) = getattr(inst, method)()
    if rval == 0:
        LOG().info('%s service "%s".', description, service)
    elif errorstr:
        LOG().error('Operation failed on service "%s": %s.',
                service, errorstr)
    return rval

def list_services(ns, kind='enabled'):
    """
    List services. Yields service instances.

    :param string kind: What kind of services to list. Possible options are:

        * 'enabled'  - list only enabled services
        * 'disabled' - list only disabled services
        * 'all'      - list all services

    :returns: Instances of ``LMI_Service``.
    :rtype: generator over :py:class:`lmi.shell.LMIInstance`.
    """
    if not isinstance(kind, basestring):
        raise TypeError("kind must be a string")
    if not kind in SERVICE_KINDS:
        raise ValueError("kind must be one of %s" % SERVICE_KINDS)
    try:
        for service in sorted(ns.LMI_Service.instances(client_filtering=True),
                key=lambda i: i.Name):
            if kind == 'disabled' and service.EnabledDefault != \
                    ns.LMI_Service.EnabledDefaultValues.Disabled:
                continue
            if kind == 'enabled' and service.EnabledDefault != \
                    ns.LMI_Service.EnabledDefaultValues.Enabled:
                # list only enabled
                continue
            yield service
    except pywbem.CIMError as err:
        if err.args[0] == pywbem.CIM_ERR_NOT_SUPPORTED:
            raise LmiFailed('Service provider is not installed or registered.')
        raise LmiFailed('Failed to list services: %s' % err.args[1])

def start_service(ns, service):
    """
    Start service.

    :param service: Service name.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    """
    return invoke_on_service(ns, 'StartService', service, 'Started')

def stop_service(ns, service):
    """
    Stop service.

    :param string service: Service name or instance.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    """
    return invoke_on_service(ns, 'StopService', service, 'Stopped')

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
    return invoke_on_service(ns, method_name, service, 'Restarted')

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
            method_name = 'ReloadOrTryRestartService'
        else:
            method_name = 'ReloadOrRestartService'
    else:
        method_name = 'ReloadService'
    return invoke_on_service(ns, method_name, service, 'Reloaded')

def enable_service(ns, service, enable=True):
    """
    Enable or disable service.

    :param service: Service name or instance.
    :type service: string or :py:class:`lmi.shell.LMIInstanceName`
    :param boolean enable: Whether the service should be enabled or
        disabled. Enabled service is started on system boot.
    """
    if enable:
        method_name = 'TurnServiceOn'
        description = 'Enabled'
    else:
        method_name = 'TurnServiceOff'
        description = 'Disabled'
    return invoke_on_service(ns, method_name, service, description)

def get_service(ns, service):
    """
    Return :py:class:`lmi.shell.LMIInstance` object matching the given
    service name.

    :param string service: Service name.
    """
    try:
        if isinstance(service, basestring):
            if not service.endswith('.service'):
                service += '.service'
            cs = get_computer_system(ns)
            iname = ns.LMI_Service.new_instance_name({
                "Name": service,
                "CreationClassName" : "LMI_Service",
                "SystemName" : cs.Name,
                "SystemCreationClassName" : cs.CreationClassName
            })
            inst = iname.to_instance()

        elif isinstance(service, (LMIInstance, LMIInstanceName)):
            try:
                inst = service
                service = inst.Name
                if isinstance(inst, LMIInstanceName):
                    inst = inst.to_instance()
            except AttributeError:
                raise ValueError('Invalid service instance name. It\'s missing'
                        ' Name property.')

        else:
            raise TypeError("service must be either string or ``LMIInstanceName``")

    except pywbem.CIMError as err:
        if err.args[0] == pywbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed('No such service "%s".' % service)
        else:
            raise LmiFailed('Failed to get service "%s": %s'
                    % (service, err.args[1]))

    if inst is None:
        raise LmiFailed('No such service "%s".' % service)

    return inst


def get_status_string(ns, service):
    """
    Return human friendly status description.

    :param service: Either a service instance or its name.
    :returns: Status description. One of
        ``{ OK, Running, Stopped - OK, Stopped - Error }``.
    :rtype: string
    """
    service = get_service(ns, service)

    status = []
    # first check for common statuses
    if ns.LMI_Service.OperationalStatusValues.Completed in \
            service.OperationalStatus:
        status.append('Stopped')
    if ns.LMI_Service.OperationalStatusValues.OK in service.OperationalStatus:
        if not status:
            status.append('Running')
        else:
            status.append('OK')
    elif ns.LMI_Service.OperationalStatusValues.Error in \
            service.OperationalStatus:
        status.append('Error')

    if not status:
        # build the status from formal names
        status = [  ns.LMI_Service.OperationalStatusValues.value_name(val)
                 for val in service.OperationalStatus]

        if not status:
            status.append = 'Unknown'

    return ' - '.join(status)

def get_enabled_string(ns, service):
    """
    Return human friendly string for enabled state.

    :param service: Either a service instance of its name.
    :returns: Status description. One of:
        ``{ Yes, No, Static }``.
    ``Static`` represents a service that can not be enabled or disabled,
    and are run only if something depends on them. It lacks ``[Install]``
    section.
    :rtype: string
    """
    service = get_service(ns, service)

    if service.EnabledDefault == ns.LMI_Service.EnabledDefaultValues.Enabled:
        return "Yes"
    if service.EnabledDefault == ns.LMI_Service.EnabledDefaultValues.Disabled:
        return "No"
    return "Static"
