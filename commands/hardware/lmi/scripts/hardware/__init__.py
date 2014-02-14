# -*- coding: utf-8 -*-
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
"""
LMI hardware provider client library.
"""

from lmi.scripts.common import get_computer_system

GREEN_COLOR = 1
YELLOW_COLOR = 2
RED_COLOR = 3

EMPTY_LINE = ('', '')
# GLOBAL variable - modified in get_all_info(), accessed in init_result()
STANDALONE = True

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
    :returns: Tabular data of system hostname.
    :rtype: List of tuples
    """
    i = get_computer_system(ns)
    return [('Hostname:', i.Name)]

def init_result(ns):
    """
    Returns initialized result list.

    :returns: Initialized result list.
    :rtype: List
    """
    if STANDALONE:
        result = get_hostname(ns)
        result.append(EMPTY_LINE)
    else:
        result = []
    return result

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
    colors = {
        GREEN_COLOR: '\033[92m',
        YELLOW_COLOR: '\033[93m',
        RED_COLOR: '\033[91m',}
    ENDC = '\033[0m'
    return '%s%s%s' % (colors[color], msg, ENDC)

def get_all_info(ns):
    """
    :returns: Tabular data of all available info.
    :rtype: List of tuples
    """
    global STANDALONE
    STANDALONE = False
    result = get_hostname(ns)
    result.append(EMPTY_LINE)
    result += get_system_info(ns)
    result.append(EMPTY_LINE)
    result += get_motherboard_info(ns)
    result.append(EMPTY_LINE)
    result += get_cpu_info(ns)
    result.append(EMPTY_LINE)
    result += get_memory_info(ns)
    result.append(EMPTY_LINE)
    result += get_disks_info(ns)
    STANDALONE = True
    return result

def get_system_info(ns):
    """
    :returns: Tabular data of system info, from the ``LMI_Chassis`` instance.
    :rtype: List of tuples
    """
    i = get_single_instance(ns, 'LMI_Chassis')
    if i.Model and i.ProductName:
        model = '%s (%s)' % (i.Model, i.ProductName)
    elif i.Model:
        model = i.Model
    elif i.ProductName:
        model = i.ProductName
    else:
        model = 'N/A'
    if i.VirtualMachine:
        virt = i.VirtualMachine
    else:
        virt = 'N/A'
    result = init_result(ns)
    result += [
          ('Chassis Type:', ns.LMI_Chassis.ChassisPackageTypeValues.value_name(
               i.ChassisPackageType)),
          ('Manufacturer:', i.Manufacturer),
          ('Model:', model),
          ('Serial Number:', i.SerialNumber),
          ('Asset Tag:', i.Tag),
          ('Virtual Machine:', virt)]
    return result

def get_motherboard_info(ns):
    """
    :returns: Tabular data of motherboard info.
    :rtype: List of tuples
    """
    i = get_single_instance(ns, 'LMI_Baseboard')
    model = ''
    manufacturer = ''
    if i:
        model = i.Model
        manufacturer = i.Manufacturer
    if not model:
        model = 'N/A'
    if not manufacturer:
        manufacturer = 'N/A'
    result = init_result(ns)
    result += [
          ('Motherboard:', model),
          ('Manufacturer:', manufacturer)]
    return result

def get_cpu_info(ns):
    """
    :returns: Tabular data of processor info.
    :rtype: List of tuples
    """
    cpus = get_all_instances(ns, 'LMI_Processor')
    cpu_caps = get_all_instances(ns, 'LMI_ProcessorCapabilities')
    cores = 0
    threads = 0
    for i in cpu_caps:
        cores += i.NumberOfProcessorCores
        threads += i.NumberOfHardwareThreads
    result = init_result(ns)
    result += [
          ('CPU:', cpus[0].Name),
          ('Topology:', '%d cpu(s), %d core(s), %d thread(s)' % \
                (len(cpus), cores, threads)),
          ('Max Freq:', '%d MHz' % cpus[0].MaxClockSpeed),
          ('Arch:', cpus[0].Architecture)]
    return result

def get_memory_info(ns):
    """
    :returns: Tabular data of memory info.
    :rtype: List of tuples
    """
    memory = get_single_instance(ns, 'LMI_Memory')
    phys_memory = get_all_instances(ns, 'LMI_PhysicalMemory')
    memory_slots = get_all_instances(ns, 'LMI_MemorySlot')

    size = format_memory_size(memory.NumberOfBlocks)

    slots = ''
    if len(phys_memory):
        slots += '%d' % len(phys_memory)
    else:
        slots += 'N/A'
    slots += ' used, '
    if len(memory_slots):
        slots += '%d' % len(memory_slots)
    else:
        slots += 'N/A'
    slots += ' total'

    modules = []
    for m in phys_memory:
        module = format_memory_size(m.Capacity)
        if m.MemoryType:
            module += ', %s' % \
                ns.LMI_PhysicalMemory.MemoryTypeValues.value_name(m.MemoryType)
            if m.FormFactor:
                module += ' (%s)' % \
                    ns.LMI_PhysicalMemory.FormFactorValues.value_name(
                    m.FormFactor)
        if m.ConfiguredMemoryClockSpeed:
            module += ', %d MHz' % m.ConfiguredMemoryClockSpeed
        if m.Manufacturer:
            module += ', %s' % m.Manufacturer
        if m.BankLabel:
            module += ', %s' % m.BankLabel
        if not modules:
            modules.append(('Modules:', module))
        else:
            modules.append(('', module))
    if not modules:
        modules.append(('Modules:', 'N/A'))

    result = init_result(ns)
    result.append(('Memory:', size))
    result += modules
    result.append(('Slots:', slots))
    return result

def get_disks_info(ns):
    """
    :returns: Tabular data of disk info.
    :rtype: List of tuples
    """
    result = init_result(ns)
    result.append(('Disks:', ''))

    hdds = get_all_instances(ns, 'LMI_DiskDrive')
    if not hdds:
        result.append((' N/A', ''))
        return result

    first_disk = True

    for hdd in hdds:
        phys_hdds = hdd.associators(ResultClass='LMI_DiskPhysicalPackage')
        manufacturer = ''
        model = ''
        if phys_hdds:
            manufacturer = phys_hdds[0].Manufacturer
            model = phys_hdds[0].Model
        if not manufacturer:
            manufacturer = 'N/A'
        if not model:
            model = 'N/A'

        form_factor_dict = {
            3: '5.25"',
            4: '3.5"',
            5: '2.5"',
            6: '1.8"',}
        if hdd.FormFactor in form_factor_dict:
            form_factor = form_factor_dict[hdd.FormFactor]
        else:
            form_factor = 'N/A'

        if hdd.RPM != 0xffffffff:
            rpm = hdd.RPM
        else:
            rpm = 'N/A'

        if hdd.DiskType == 2:
            disk_type = 'HDD'
        elif hdd.DiskType == 3:
            disk_type = 'SSD'
        else:
            disk_type = 'N/A'

        port_type = ''
        port_speed_current = ''
        port_speed_max = ''
        hdd_endpoints = hdd.associators(
            ResultClass='LMI_DiskDriveATAProtocolEndpoint')
        if hdd_endpoints:
            hdd_ports = hdd_endpoints[0].associators(
                ResultClass='LMI_DiskDriveATAPort')
            if hdd_ports:
                if hdd_ports[0].PortType:
                    port_type = ns.LMI_DiskDriveATAPort.PortTypeValues.value_name(
                        hdd_ports[0].PortType)
                if hdd_ports[0].Speed:
                    port_speed_current = '%.1f Gb/s' % \
                        (float(hdd_ports[0].Speed) / 1000000000.0)
                if hdd_ports[0].MaxSpeed:
                    port_speed_max = '%.1f Gb/s' % \
                        (float(hdd_ports[0].MaxSpeed) / 1000000000.0)
        if not port_type:
            port_type = 'N/A'
        if not port_speed_current:
            port_speed_current = 'N/A Gb/s'
        if not port_speed_max:
            port_speed_max = 'N/A Gb/s'

        status_to_color = {
            'OK': GREEN_COLOR,
            'Unknown': YELLOW_COLOR,
            'Predictive Failure': RED_COLOR,}
        if hdd.OperationalStatus:
            smart = ns.LMI_DiskDrive.OperationalStatusValues.value_name(
                hdd.OperationalStatus[0])
            smart = get_colored_string(smart, status_to_color[smart])
        else:
            smart = get_colored_string('Unknown', YELLOW_COLOR)

        temp = ''
        if hdd.Temperature:
            temp = '%d' % hdd.Temperature
        if not temp:
            temp = 'N/A'
        temp = temp + u' °C'

        if not first_disk:
            result.append(EMPTY_LINE)
        else:
            first_disk = False

        if hdd.Name != hdd.DeviceID and hdd.Name != model:
            result.append(('  %s' % hdd.DeviceID, hdd.Name))
        else:
            result.append(('  %s' % hdd.DeviceID, ''))
        result += [('    Manufacturer:', manufacturer),
            ('    Model:', model),
            ('    Capacity:', format_memory_size(hdd.Capacity)),
            ('    Form Factor:', form_factor),
            ('    HDD/SSD:', disk_type),
            ('    RPM:', rpm),
            ('    Port Type:', port_type),
            ('    Port Speed:', '%s current, %s max' % \
                (port_speed_current, port_speed_max)),
            ('    SMART Status:', smart),
            ('    Temperature:', temp)]
    return result
