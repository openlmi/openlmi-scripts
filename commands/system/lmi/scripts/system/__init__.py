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

from sys import stdout
from lmi.scripts.service import get_service
from lmi.scripts.common import get_computer_system
from lmi.shell.LMIExceptions import LMIClassNotFound
from lmi.scripts.common.formatter import TableFormatter

GREEN_COLOR = 1
YELLOW_COLOR = 2
RED_COLOR = 3

FIRST_COLUMN_MIN_SIZE = 17

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

def get_hostname(ns):
    """
    :returns: System hostname.
    :rtype: String
    """
    i = get_computer_system(ns)
    return i.Name

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

def get_colored_string(msg, color):
    """
    Returns colored message with ANSI escape sequences for terminal.

    :param msg: Message to be colored.
    :type msg: String
    :param color: Color of the message [GREEN_COLOR, YELLOW_COLOR, RED_COLOR].
    :type color: Integer
    :returns: Colored message.
    :rtype: String
    """
    if not stdout.isatty():
        return msg

    colors = {
        GREEN_COLOR: '\033[92m',
        YELLOW_COLOR: '\033[93m',
        RED_COLOR: '\033[91m',}
    ENDC = '\033[0m'
    return '%s%s%s' % (colors[color], msg, ENDC)

def get_system_info(ns):
    """
    Prints tabular data of all general system information.
    """
    tf = TableFormatter(stdout, 0, True)
    tf.print_host(get_hostname(ns))

    try:
        get_hwinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_storageinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_osinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_langinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_selinuxinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_servicesinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_networkinfo(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    return []

def get_hwinfo(ns):
    """
    Prints tabular data of system hw info.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    # Chassis
    try:
        chassis = get_single_instance(ns, 'LMI_Chassis')
    except Exception:
        result = [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_Chassis. Is openlmi-hardware package installed on the server?')]
        tf.produce_output(result)
        return []

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
    chassis_res = [
       ('Hardware:', hwinfo),
       ('Serial Number:', chassis.SerialNumber),
       ('Asset Tag:', chassis.Tag)]
    tf.produce_output(chassis_res)

    # CPUs
    try:
        cpus = get_all_instances(ns, 'LMI_Processor')
        cpu_caps = get_all_instances(ns, 'LMI_ProcessorCapabilities')
    except Exception:
        cpus = None
        cpu_caps = None
    if cpus and cpu_caps:
        cores = 0
        threads = 0
        for i in cpu_caps:
            cores += i.NumberOfProcessorCores
            threads += i.NumberOfHardwareThreads
        cpus_res = [
            ('CPU:', '%s, %s arch' % (cpus[0].Name, cpus[0].Architecture)),
            ('CPU Topology:', '%d cpu(s), %d core(s), %d thread(s)' % \
                (len(cpus), cores, threads))]
    else:
        cpus_res = [('CPU:', 'N/A')]
    tf.produce_output(cpus_res)

    # Memory
    try:
        memory = get_single_instance(ns, 'LMI_Memory')
    except Exception:
        memory = None
    if memory:
        memory_size = format_memory_size(memory.NumberOfBlocks)
    else:
        memory_size = 'N/A GB'
    tf.produce_output([('Memory:', memory_size)])

    return []

def get_storageinfo(ns):
    """
    Prints tabular data of storage info.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    try:
        localfss = get_all_instances(ns, 'LMI_LocalFileSystem')
    except Exception:
        result = [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_LocalFileSystem. Is openlmi-storage package installed on the server?')]
        tf.produce_output(result)
        return []

    total = 0
    free = 0
    for fs in localfss:
        if fs.FileSystemSize:
            total += fs.FileSystemSize
        if fs.AvailableSpace:
            free += fs.AvailableSpace

    result = [('Disk Space:', '%s total, %s free' % (format_memory_size(total),
         format_memory_size(free)))]
    tf.produce_output(result)
    return []

def get_osinfo(ns):
    """
    Prints tabular data of system OS info.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    try:
        os = get_single_instance(ns, 'PG_OperatingSystem')
    except Exception:
        result = [(get_colored_string('error:', RED_COLOR),
                    'Missing class PG_OperatingSystem on the server.')]
        tf.produce_output(result)
        return []

    os_str = ''
    kernel_str = ''
    if os:
        os_str = os.Caption
        kernel_str = os.Version
    if not os_str:
        os_str = 'N/A'
    if not kernel_str:
        kernel_str = 'N/A'

    result = [
        ('OS:', os_str),
        ('Kernel:', kernel_str)]
    tf.produce_output(result)
    return []

def get_langinfo(ns):
    """
    Prints tabular data of language and time zone info.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    try:
        locale = get_single_instance(ns, 'LMI_Locale')
    except Exception:
        result = [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_Locale. Is openlmi-locale package installed on the server?')]
        tf.produce_output(result)
        return []

    tf.produce_output([('Language:', locale.Lang)])
    try:
        tf.produce_output([('Time Zone:',
            "%s (NTP is %s)" % (locale.Timezone, 'on' if locale.NTP else 'off'))])
    except Exception:
        # Time Zone info was added later to the LMI_Locale class
        pass
    return []

def get_selinuxinfo(ns):
    """
    Prints tabular data of SELinux info.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    try:
        selinux = get_single_instance(ns, 'LMI_SELinuxService')
    except Exception:
        result = [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_SELinuxService. Is openlmi-selinux package installed on the server?')]
        tf.produce_output(result)
        return []

    if selinux.SELinuxState == 0:
        selinux_str = 'disabled'
    else:
        selinux_str = 'enabled (%s)' % \
            ns.LMI_SELinuxService.SELinuxStateValues.value_name(selinux.SELinuxState).lower()

    tf.produce_output([('SELinux:', selinux_str)])
    return []

def get_servicesinfo(ns):
    """
    Prints tabular data of some system services.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    # Firewall
    try:
        fw = ''
        firewalld = get_service(ns, 'firewalld')
        if firewalld and firewalld.Status == 'OK':
            fw = 'on (firewalld)'
        else:
            iptables = get_service(ns, 'iptables')
            if iptables and iptables.Status == 'OK':
                fw = 'on (iptables)'
        if not fw:
            fw = 'off'
    except Exception:
        fw = 'N/A'
    tf.produce_output([('Firewall:', fw)])

    # Logging
    try:
        logging = ''
        journald = get_service(ns, 'systemd-journald')
        if journald and journald.Status == 'OK':
            logging = 'on (journald)'
        else:
            rsyslog = get_service(ns, 'rsyslog')
            if rsyslog and rsyslog.Status == 'OK':
                logging = 'on (rsyslog)'
        if not logging:
            logging = 'off'
    except Exception:
        logging = 'N/A'
    tf.produce_output([('Logging:', logging)])

    return []

def get_networkinfo(ns):
    """
    Prints tabular data of networking status.
    """
    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})

    result = [('', ''), ('Networking:', '')]
    try:
        lan_endpoints = get_all_instances(ns, 'LMI_LANEndpoint')
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_LANEndpoint. Is openlmi-networking package installed on the server?')]
        tf.produce_output(result)
        return []

    nic = 1
    for lan_endpoint in lan_endpoints:
        if lan_endpoint.Name == 'lo':
            continue
        result += [
            ('  NIC %d' % nic, ''),
            ('    Name:', lan_endpoint.Name)]
        try:
            ip_net_con = lan_endpoint.associators(
                AssocClass='LMI_EndpointForIPNetworkConnection',
                ResultClass='LMI_IPNetworkConnection')[0]
            result += [('    Status:',
                ns.LMI_IPNetworkConnection.OperatingStatusValues.value_name(
                ip_net_con.OperatingStatus))]
        except Exception:
            pass
        try:
            for ip_protocol_endpoint in lan_endpoint.associators(
                    AssocClass='LMI_BindsToLANEndpoint',
                    ResultClass='LMI_IPProtocolEndpoint'):
                if ip_protocol_endpoint.ProtocolIFType == \
                        ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv4:
                    result += [('    IPv4 Address:',
                        ip_protocol_endpoint.IPv4Address)]
                elif ip_protocol_endpoint.ProtocolIFType == \
                        ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv6:
                    result += [('    IPv6 Address:',
                        ip_protocol_endpoint.IPv6Address)]
        except Exception:
            pass
        result += [
            ('    MAC Address:', lan_endpoint.MACAddress)]
        tf.produce_output(result)
        result = []
        nic += 1

    return []
