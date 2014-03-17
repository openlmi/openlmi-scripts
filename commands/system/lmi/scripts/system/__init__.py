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
# Author: Peter Schiffer <pschiffe@redhat.com>
#
"""
LMI system client library.
"""

from lmi.scripts.common import get_computer_system
from lmi.scripts.service import get_service
from lmi.shell.LMIExceptions import LMIClassNotFound

def _cache_replies(ns, class_name, method):
    """
    Get the reply from cimom and cache it. Cache is cleared
    once the namespace object changes.

    :param str class_name: Name of class to operate on.
    :param str method_name: Name of method to invoke on lmi class object.
    :returns: Whatever the requested method returns.
    """
    if not hasattr(_cache_replies, 'cache'):
        _cache_replies.cache = (ns, {})
    old_ns, cache = _cache_replies.cache
    if old_ns is not ns:
        # keep the cache until namespace object changes
        cache.clear()
        _cache_replies.cache = (ns, cache)
    if not (class_name, method) in cache:
        i = getattr(ns, class_name)
        cache[(class_name, method)] = getattr(i, method)()
    return cache[(class_name, method)]

def get_single_instance(ns, class_name):
    """
    Returns single instance of instance_name.

    :param instance_name: Instance name
    :type instance_name: String
    :returns: Instance of instance_name
    :rtype: :py:class:`lmi.shell.LMIInstance`
    """
    return _cache_replies(ns, class_name, 'first_instance')

def get_all_instances(ns, class_name):
    """
    Returns all instances of instance_name.

    :param instance_name: Instance name
    :type instance_name: String
    :returns: List of instances of instance_name
    :rtype: List of :py:class:`lmi.shell.LMIInstance`
    """
    return _cache_replies(ns, class_name, 'instances')

def format_memory_size(size):
    """
    Returns formatted memory size.

    :param size: Size in bytes
    :type size: Number
    :returns: Formatted size string.
    :rtype: String
    """
    if not size:
        return 'N/A GB'
    if size >= 1099511627776:
        sizestr = '%.1f TB' % (float(size) / 1099511627776.0)
    elif size >= 1073741824:
        sizestr = '%.1f GB' % (float(size) / 1073741824.0)
    elif size >= 1048576:
        sizestr = '%d MB' % (int(size) / 1048576)
    elif size >= 1024:
        sizestr = '%d KB' % (int(size) / 1024)
    else:
        sizestr = '%d B' % int(size)
    return sizestr

def get_system_info(ns):
    """
    :returns: Tabular data of all general system information.
    :rtype: List of tuples
    """
    result = get_hostname(ns)
    result += get_hwinfo(ns)
    result += get_osinfo(ns)
    result += get_servicesinfo(ns)
    result += get_networkinfo(ns)
    return result

def get_hostname(ns):
    """
    :returns: Tabular data of system hostname.
    :rtype: List of tuples
    """
    i = get_computer_system(ns)
    return [('Computer Name:', i.Name)]

def get_hwinfo(ns):
    """
    :returns: Tabular data of system hw info.
    :rtype: List of tuples
    """
    # Chassis
    try:
        chassis = get_single_instance(ns, 'LMI_Chassis')
    except LMIClassNotFound:
        chassis = None
    if chassis:
        hwinfo = chassis.Manufacturer
        if chassis.Model and chassis.Model != 'Not Specified' \
                and chassis.Model != chassis.Manufacturer:
            hwinfo += ' ' + chassis.Model
        elif chassis.ProductName and chassis.ProductName != 'Not Specified' \
                and chassis.ProductName != chassis.Manufacturer:
            hwinfo += ' ' + chassis.ProductName
        virt = getattr(chassis, 'VirtualMachine', None)
        if virt and virt != 'No':
            hwinfo += ' (%s virtual machine)' % virt
    else:
        hwinfo = 'N/A'
    # CPUs
    try:
        cpus = get_all_instances(ns, 'LMI_Processor')
    except LMIClassNotFound:
        cpus = None
    if cpus:
        cpus_str = '%dx %s' % (len(cpus), cpus[0].Name)
    else:
        cpus_str = 'N/A'
    # Memory
    try:
        memory = get_single_instance(ns, 'LMI_Memory')
    except LMIClassNotFound:
        memory = None
    if memory:
        memory_size = format_memory_size(memory.NumberOfBlocks)
    else:
        memory_size = 'N/A GB'
    # Result
    result = [
        ('Hardware:', hwinfo),
        ('Processors:', cpus_str),
        ('Memory:', memory_size)]
    return result

def get_osinfo(ns):
    """
    :returns: Tabular data of system OS info.
    :rtype: List of tuples
    """
    # OS
    try:
        os = get_single_instance(ns, 'PG_OperatingSystem')
    except LMIClassNotFound:
        os = None
    os_str = ''
    kernel_str = ''
    if os:
        os_str = os.Caption
        kernel_str = os.Version
    if not os_str:
        os_str = 'N/A'
    if not kernel_str:
        kernel_str = 'N/A'
    # Result
    result = [
        ('OS:', os_str),
        ('Kernel:', kernel_str)]
    return result

def get_servicesinfo(ns):
    """
    :returns: Tabular data of some system services.
    :rtype: List of tuples
    """
    # Firewall
    try:
        fw = ''
        firewalld = get_service(ns, 'firewalld.service')
        if firewalld and firewalld.Status == 'OK':
            fw = 'on (firewalld)'
        else:
            iptables = get_service(ns, 'iptables.service')
            if iptables and iptables.Status == 'OK':
                fw = 'on (iptables)'
        if not fw:
            fw = 'off'
    except LMIClassNotFound:
        fw = 'N/A'
    # Logging
    try:
        logging = ''
        journald = get_service(ns, 'systemd-journald.service')
        if journald and journald.Status == 'OK':
            logging = 'on (journald)'
        else:
            rsyslog = get_service(ns, 'rsyslog.service')
            if rsyslog and rsyslog.Status == 'OK':
                logging = 'on (rsyslog)'
        if not logging:
            logging = 'off'
    except LMIClassNotFound:
        logging = 'N/A'
    # Result
    result = [
        ('Firewall:', fw),
        ('Logging:', logging)]
    return result

def get_networkinfo(ns):
    """
    :returns: Tabular data of networking status.
    :rtype: List of tuples
    """
    result = [('', ''), ('Networking', '')]
    try:
        lan_endpoints = get_all_instances(ns, 'LMI_LANEndpoint')
    except LMIClassNotFound:
        result.append(('  N/A', ''))
        return result
    nic = 1
    for lan_endpoint in lan_endpoints:
        if lan_endpoint.Name == 'lo':
            continue
        result += [
            ('  NIC %d' % nic, ''),
            ('    Name:', lan_endpoint.Name)]
        try:
            ip_net_con = lan_endpoint.associators(
                ResultClass='LMI_IPNetworkConnection')[0]
            result.append(('    Status:',
                ns.LMI_IPNetworkConnection.OperatingStatusValues.value_name(
                ip_net_con.OperatingStatus)))
        except LMIClassNotFound:
            pass
        try:
            for ip_protocol_endpoint in lan_endpoint.associators(
                    ResultClass='LMI_IPProtocolEndpoint'):
                if ip_protocol_endpoint.ProtocolIFType == \
                        ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv4:
                    result.append(('    IPv4 Address:',
                        ip_protocol_endpoint.IPv4Address))
                elif ip_protocol_endpoint.ProtocolIFType == \
                        ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv6:
                    result.append(('    IPv6 Address:',
                        ip_protocol_endpoint.IPv6Address))
        except LMIClassNotFound:
            pass
        result += [
            ('    MAC Address:', lan_endpoint.MACAddress)]
        nic += 1
    return result
