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
import pywbem
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

def set_debug_level(ns, level, until_restart, components):
    rval = 0
    for component in ns.LMI_SSSDComponent.instances():
        found = False
        if components is not None and len(components) > 0:
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
    for svc in ns.LMI_SSSDResponder.instances():
        if kind == 'disabled' and svc.IsEnabled == True:
            continue
        if kind == 'enabled' and svc.IsEnabled == False:
            continue
        yield svc
        
def get_service(ns, service):
    keys = {'Name': service}
    try:
        inst = ns.LMI_SSSDResponder.new_instance_name(keys).to_instance()
    except pywbem.CIMError, err:
        if err[0] == pywbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the service: %s" % service)
        raise
    return inst

def enable_service(ns, service):
    instance = get_service(ns, service)
    (rval, _, msg) = instance.Enable()
    if rval == 0:
        LOG().info('Service "%s" enabled', service)
    elif msg:
        LOG().error('Operation failed on "%s": %s.', service, errorstr)
    return rval

def disable_service(ns, service):
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
    for backend in ns.LMI_SSSDBackend.instances():
        if kind == 'disabled' and backend.IsEnabled == True:
            continue
        if kind == 'enabled' and backend.IsEnabled == False:
            continue
        yield backend
        
def get_provider(ns, type, backend):
    for provider in backend.associators(AssocClass="LMI_SSSDBackendProvider"):
        if provider.Type == type:
            return provider.Module
    return 'ldap'

def get_domain(ns, domain):
    keys = {'Name': domain}
    try:
        inst = ns.LMI_SSSDDomain.new_instance_name(keys).to_instance()
    except pywbem.CIMError, err:
        if err[0] == pywbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the domain: %s" % service)
        raise
    return inst

def get_backend(ns, domain):
    keys = {'Name': domain}
    try:
        inst = ns.LMI_SSSDBackend.new_instance_name(keys).to_instance()
    except pywbem.CIMError, err:
        if err[0] == pywbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the backend: %s" % service)
        raise
    return inst

def enable_backend(ns, domain):
    instance = get_backend(ns, domain)
    (rval, _, msg) = instance.Enable()
    if rval == 0:
        LOG().info('Domain "%s" enabled', domain)
    elif msg:
        LOG().error('Operation failed on "%s": %s.', domain, errorstr)
    return rval

def disable_backend(ns, domain):
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
    subdomains = domain.associators(AssocClass="LMI_SSSDDomainSubdomain",
                                    ResultRole="Subdomain")
    
    for subdomain in subdomains:
        yield subdomain.Name
        
def list_subdomains_comma_separated(ns, domain):
    return ', '.join(list_subdomains_names(ns, domain))
