# SSSD Providers
#
# Copyright (C) 2013-2014 Red Hat, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# Authors: Pavel Brezina <pbrezina@redhat.com>
#
"""
LMI SSSD provider client library.

This set of functions can list and manage SSSD's responders and domains.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.shell.LMIInstanceName import LMIInstanceName
from lmi.scripts.common import get_computer_system
from lmi.scripts.common import get_logger
try:
    import lmiwbem as wbem
except ImportError:
    import pywbem as wbem
import lmi.scripts.common

LOG = get_logger(__name__)

def debug_level(level):
    """
    Return hexadecimal representation of debug level.
    
    :type level: int
    :param level: Debug level.
    :rtype: string
    """
    return "%#.4x" % level

#
# SSSD
#

def set_debug_level(ns, level, all, until_restart, components):
    """
    Configure log level of given components.

    :type level: int
    :param level: Log level.
    :type all: boolean
    :param all: Whether the log level should be set to all components or not.
    :type until_restart: boolean
    :param until_restart: Whether the log level should be set permanently
        (False) or just until next SSSD restart (True).
    :type components: list
    :param components: List of strings with name of components, which should be
        configured.
    :rtype: int
    :rvalue: 0 on success
    """
    rval = 0
    for component in ns.LMI_SSSDComponent.instances():
        found = False
        if all or components is None or len(components) == 0:
            found = True
        else:
            for name in components:
                if component.Name == name:
                    found = True
                    continue
        if not found:
            continue
        if until_restart:
            (rval, _, msg) = component.SetDebugLevelTemporarily({'debug_level' : int(level, 16)})
        else:
            (rval, _, msg) = component.SetDebugLevelPermanently({'debug_level' : int(level, 16)})
        if rval == 0:
            LOG().info('Debug level of "%s" changed to "%#.4x".',
                       component.Name, level)
        elif msg:
            LOG().error('Operation failed on "%s": %s.',
                        component.Name, errorstr)
    return rval

#
# Services
#

def list_services(ns, kind='all'):
    """
    Generates LMIInstances of LMI_SSSDResponder. Optionally, only the enabled
    or disabled are listed.

    :type kind: string
    :param kind: Either 'all', 'disabled' or 'enabled'.
    :rtype: (list of) LMIInstances
    """
    for svc in ns.LMI_SSSDResponder.instances():
        if kind == 'disabled' and svc.IsEnabled == True:
            continue
        if kind == 'enabled' and svc.IsEnabled == False:
            continue
        yield svc

def get_service(ns, service):
    """
    Return LMIInstance of LMI_SSSDResponder.

    :type service: string
    :param service: Name of the service to return.
    :rtype: LMIInstance
    """
    keys = {'Name': service}
    try:
        inst = ns.LMI_SSSDResponder.new_instance_name(keys).to_instance()
    except wbem.CIMError, err:
        if err[0] == wbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the service: %s" % service)
        raise
    return inst

def enable_service(ns, service):
    """
    Enable given SSSD service.

    :type service: string
    :param service: Name of the service to enable.
    :rtype: int
    :rvalue: 0 on success.
    """
    instance = get_service(ns, service)
    (rval, _, msg) = instance.Enable()
    if rval == 0:
        LOG().info('Service "%s" enabled', service)
    elif msg:
        LOG().error('Operation failed on "%s": %s.', service, errorstr)
    return rval

def disable_service(ns, service):
    """
    Disable given SSSD service.

    :type service: string
    :param service: Name of the service to disable.
    :rtype: int
    :rvalue: 0 on success.
    """
    instance = get_service(ns, service)
    (rval, _, msg) = instance.Disable()
    if rval == 0:
        LOG().info('Service "%s" disabled', service)
    elif msg:
        LOG().error('Operation failed on "%s": %s.', service, errorstr)
    return rval

#
# Domains
#

def list_backends(ns, kind='all'):
    """
    Generate list of SSSD backends.

    :type kind: string
    :param kind: Either 'all', 'disabled' or 'enabled'.
    :rtype: (list of) LMIInstances
    """
    for backend in ns.LMI_SSSDBackend.instances():
        if kind == 'disabled' and backend.IsEnabled == True:
            continue
        if kind == 'enabled' and backend.IsEnabled == False:
            continue
        yield backend

def get_provider(ns, type, backend):
    """
    Returns SSSD provider for given backend.

    :type type: string
    :param type: Type of the provider (= value of its LMI_SSSDProvider.Type
        property).
    :type backend: LMIInstance of LMI_SSSDBackend
    :param backed: SSSD backend to inspect.
    :rtype: string
    :rvalue: The provider module (= value of LMI_SSSDProvider.Module property).
    """
    for provider in backend.associators(AssocClass="LMI_SSSDBackendProvider"):
        if provider.Type == type:
            return provider.Module
    return 'ldap'

def get_domain(ns, domain):
    """
    Return LMIInstance of given LMI_SSSDDomain.

    :type domain: string
    :param domain: Name of the domain to find.
    :rtype: LMIInstance of LMI_SSSDDomain
    """
    keys = {'Name': domain}
    try:
        inst = ns.LMI_SSSDDomain.new_instance_name(keys).to_instance()
    except wbem.CIMError, err:
        if err[0] == wbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the domain: %s" % domain)
        raise
    return inst

def get_backend(ns, domain):
    """
    Return LMIInstance of LMI_SSSDBackend for given domain.

    :type domain: string
    :param domain: Name of domain to inspect.
    :rtype: LMIInstance of LMI_SSSDBackend
    """
    keys = {'Name': domain}
    try:
        inst = ns.LMI_SSSDBackend.new_instance_name(keys).to_instance()
    except wbem.CIMError, err:
        if err[0] == wbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the backend: %s" % domain)
        raise
    return inst

def enable_backend(ns, domain):
    """
    Enables backend of given domain.

    :type domain: string
    :param domain: Name of the domain to enable.
    :rtype: int
    :rvalue: 0 on success
    """
    instance = get_backend(ns, domain)
    (rval, _, msg) = instance.Enable()
    if rval == 0:
        LOG().info('Domain "%s" enabled', domain)
    elif msg:
        LOG().error('Operation failed on "%s": %s.', domain, errorstr)
    return rval

def disable_backend(ns, domain):
    """
    Disables backend of given domain.

    :type domain: string
    :param domain: Name of the domain to disable.
    :rtype: int
    :rvalue: 0 on success
    """
    instance = get_backend(ns, domain)
    (rval, _, msg) = instance.Disable()
    if rval == 0:
        LOG().info('Domain "%s" disabled', domain)
    elif msg:
        LOG().error('Operation failed on "%s": %s.', domain, errorstr)
    return rval

#
# Subdomains
#

def list_subdomains_names(ns, domain):
    """
    List subdomains of given domain.

    :type domain: LMIInstance of LMI_SSSDDomain
    :param domain: Domain to inspect.
    :rtype: list of LMIInstances of LMI_SSSDDomain.
    """
    subdomains = domain.associators(AssocClass="LMI_SSSDDomainSubdomain",
                                    ResultRole="Subdomain")

    for subdomain in subdomains:
        yield subdomain.Name

def list_subdomains_comma_separated(ns, domain):
    """
    List subdomains of given domain.

    :type domain: LMIInstance of LMI_SSSDDomain
    :param domain: Domain to inspect.
    :rtype: string
    :rvalue: Comma-separated list of subdomains.
    """
    return ', '.join(list_subdomains_names(ns, domain))
