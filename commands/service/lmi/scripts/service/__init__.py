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

