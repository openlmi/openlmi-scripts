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
#
# Author: Peter Schiffer <pschiffe@redhat.com>
#
"""
LMI hardware provider client library.
"""

try:
    import lmiwbem as wbem
except ImportError:
    import pywbem as wbem

from sys import stdout
from lmi.shell import LMIClassNotFound
from lmi.scripts.common import get_logger
from lmi.scripts.common import get_computer_system
from lmi.scripts.common.formatter import TableFormatter

GREEN_COLOR = 1
YELLOW_COLOR = 2
RED_COLOR = 3

EMPTY_LINE = ('', '')
FIRST_COLUMN_MIN_SIZE = 17
# GLOBAL variable - modified in get_all_info(), accessed in init_result()
STANDALONE = True

LOG = get_logger(__name__)

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
    try:
        if not (class_name, method) in cache:
            i = getattr(ns, class_name)
            cache[(class_name, method)] = getattr(i, method)()
    except (LMIClassNotFound, wbem.CIMError) as err:
        if (   isinstance(err, wbem.CIMError)
           and err.args[0] != wbem.CIM_ERR_NOT_SUPPORTED):
            raise
        LOG().info('System has old openlmi-hardware package installed,'
            ' class "%s" is not available.', class_name)
        return []
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

def get_all_info(ns):
    """
    Prints tabular data of all available info.
    """
    global STANDALONE
    STANDALONE = False

    tf = TableFormatter(stdout, 0, True)
    tf.print_host(get_hostname(ns))

    try:
        get_system_info(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_motherboard_info(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_cpu_info(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_memory_info(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_pci_info(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    try:
        get_disks_info(ns)
    except Exception as e:
        tf.produce_output([(get_colored_string('error:', RED_COLOR), str(e))])

    STANDALONE = True
    return []

def get_system_info(ns):
    """
    Prints tabular data of system info, from the ``LMI_Chassis`` instance.
    """
    result = []

    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})
    if STANDALONE:
        tf.print_host(get_hostname(ns))

    try:
        i = get_single_instance(ns, 'LMI_Chassis')
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_Chassis. Is openlmi-hardware package installed on the server?')]
        tf.produce_output(result)
        return []

    if i.Model and i.ProductName:
        model = '%s (%s)' % (i.Model, i.ProductName)
    elif i.Model:
        model = i.Model
    elif i.ProductName:
        model = i.ProductName
    else:
        model = 'N/A'

    if i.Manufacturer:
        model = '%s %s' % (i.Manufacturer, model)

    virt = getattr(i, 'VirtualMachine', None)
    if virt is None:
        virt = 'N/A. You are probably using old openlmi-hardware package on the server.'
    elif not virt:
        virt = 'N/A'

    result += [
          ('Chassis Type:', ns.LMI_Chassis.ChassisPackageTypeValues.value_name(
               i.ChassisPackageType)),
          ('Model:', model),
          ('Serial Number:', i.SerialNumber),
          ('Asset Tag:', i.Tag),
          ('Virtual Machine:', virt)]

    if not STANDALONE:
        result += [EMPTY_LINE]

    tf.produce_output(result)
    return []

def get_motherboard_info(ns):
    """
    Prints tabular data of motherboard info.
    """
    result = []

    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})
    if STANDALONE:
        tf.print_host(get_hostname(ns))

    try:
        i = get_single_instance(ns, 'LMI_Baseboard')

        if i:
            model = ''
            if i.Manufacturer:
                model += i.Manufacturer
            if i.Model:
                if model:
                    model += ' '
                model += i.Model
            result += [('Motherboard:', model)]
        else:
            if STANDALONE:
                result += [(get_colored_string('warning:', YELLOW_COLOR),
                            'LMI_Baseboard instance is missing. This usually means that the server is virtual machine.')]
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing class LMI_Baseboard. Is openlmi-hardware package installed on the server?')]

    tf.produce_output(result)
    result = []

    try:
        i = get_single_instance(ns, 'LMI_BIOSElement')

        if i and i.Name:
            result += [('BIOS:', i.Name)]
        else:
            result += [('BIOS:', 'N/A')]
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing LMI_BIOSElement class. Openlmi-hardware package is probably out-dated.')]

    if not STANDALONE:
        result += [EMPTY_LINE]

    tf.produce_output(result)
    return []

def get_cpu_info(ns):
    """
    Prints tabular data of processor info.
    """
    result = []

    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})
    if STANDALONE:
        tf.print_host(get_hostname(ns))

    try:
        cpus = get_all_instances(ns, 'LMI_Processor')
        cpu_caps = get_all_instances(ns, 'LMI_ProcessorCapabilities')
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing CPU related classes. Is openlmi-hardware package installed on the server?')]
        tf.produce_output(result)
        return []

    cores = 0
    threads = 0
    for i in cpu_caps:
        cores += i.NumberOfProcessorCores
        threads += i.NumberOfHardwareThreads

    result += [
          ('CPU:', cpus[0].Name),
          ('Topology:', '%d cpu(s), %d core(s), %d thread(s)' % \
                (len(cpus), cores, threads)),
          ('Max Freq:', '%d MHz' % cpus[0].MaxClockSpeed),
          ('Arch:', cpus[0].Architecture)]

    if not STANDALONE:
        result += [EMPTY_LINE]

    tf.produce_output(result)
    return []

def get_memory_info(ns):
    """
    Prints tabular data of memory info.
    """
    result = []

    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})
    if STANDALONE:
        tf.print_host(get_hostname(ns))

    try:
        memory = get_single_instance(ns, 'LMI_Memory')
        phys_memory = get_all_instances(ns, 'LMI_PhysicalMemory')
        memory_slots = get_all_instances(ns, 'LMI_MemorySlot')
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing memory related classes. Is openlmi-hardware package installed on the server?')]
        tf.produce_output(result)
        return []

    size = format_memory_size(memory.NumberOfBlocks)

    slots = ''
    if phys_memory:
        slots += '%d' % len(phys_memory)
    else:
        slots += 'N/A'
    slots += ' used, '
    if memory_slots:
        slots += '%d' % len(memory_slots)
    else:
        slots += 'N/A'
    slots += ' total'

    modules = []
    if phys_memory:
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

    result += [('Memory:', size)]
    result += modules
    result += [('Slots:', slots)]

    if not STANDALONE:
        result += [EMPTY_LINE]

    tf.produce_output(result)
    return []

def get_pci_list(ns, pcis, bus=0, level=0):
    """
    Recursive function, returns list of PCI devices ready for TableFormatter.

    :param ns: LMI Namespace.
    :type ns: :py:class:`lmi.shell.LMINamespace.LMINamespace`
    :param pcis: Sorted list of PCI devices and bridges.
    :type pcis: List
    :param bus: ID of PCI bus for this level.
    :type bus: Integer
    :param level: Level of recursion.
    :type level: Integer
    :returns: Formatted list of tuples of PCI devices.
    :rtype: List of tuples
    """
    if level > 99:
        return []
    result = []
    # For deeper levels, count items on the bus
    count = 0
    if level > 0:
        for p in pcis:
            if p.BusNumber == bus:
                count += 1
    # Print PCI devices
    i = 1
    for p in pcis:
        if p.BusNumber == bus:
            if level > 0:
                if i == count:
                    sign = u'└─ '
                else:
                    sign = u'├─ '
                i += 1
            else:
                sign = ''
            dsc_line = '  ' + ' ' * level + sign + p.DeviceID
            if p.CreationClassName == 'LMI_PCIBridge':
                dsc_line += ' %s bridge: ' % \
                    ns.LMI_PCIBridge.BridgeTypeValues.value_name(p.BridgeType)
            else:
                dsc_line += ' %s: ' % \
                    ns.LMI_PCIDevice.ClassCodeValues.value_name(p.ClassCode)
            dsc_line += p.Name
            result += [(dsc_line, '')]
            if p.CreationClassName == 'LMI_PCIBridge' and p.SecondayBusNumber:
                result += get_pci_list(ns, pcis, p.SecondayBusNumber, level + 1)
    return result

def get_pci_info(ns):
    """
    Prints tabular data of PCI devices info.
    """
    result = [('PCI Devices:', '')]

    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})
    if STANDALONE:
        tf.print_host(get_hostname(ns))

    try:
        pci_dev = get_all_instances(ns, 'LMI_PCIDevice')
        pci_br = get_all_instances(ns, 'LMI_PCIBridge')
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing PCI related classes. Is openlmi-hardware package installed on the server?')]
        tf.produce_output(result)
        return []

    pci = pci_dev + pci_br
    pci.sort(key=lambda x: x.DeviceID)

    if not pci:
        result += [(' N/A', 'No PCI Device was detected on the system.')]
        tf.produce_output(result)
        return []

    result += get_pci_list(ns, pci)

    if not STANDALONE:
        result += [EMPTY_LINE]

    tf.produce_output(result)
    return []

def get_disks_info(ns):
    """
    Prints tabular data of disk info.
    """
    result = [('Disks:', '')]

    tf = TableFormatter(stdout, 0, True, {0: FIRST_COLUMN_MIN_SIZE})
    if STANDALONE:
        tf.print_host(get_hostname(ns))

    try:
        hdds = get_all_instances(ns, 'LMI_DiskDrive')
    except Exception:
        result += [(get_colored_string('error:', RED_COLOR),
                    'Missing LMI_DiskDrive class. Openlmi-hardware package is probably out-dated.')]
        tf.produce_output(result)
        return []

    if not hdds:
        result += [(' N/A', 'No disk was detected on the system.')]
        tf.produce_output(result)
        return []

    for hdd in hdds:
        phys_hdds = hdd.associators(
                AssocClass='LMI_DiskDriveRealizes',
                ResultClass='LMI_DiskPhysicalPackage')
        fws = hdd.associators(
                AssocClass='LMI_DiskDriveElementSoftwareIdentity',
                ResultClass='LMI_DiskDriveSoftwareIdentity')

        if phys_hdds and phys_hdds[0].Model:
            model = phys_hdds[0].Model
        else:
            model = 'N/A'
        if phys_hdds[0].Manufacturer \
                and not model.startswith(phys_hdds[0].Manufacturer):
            man_model = '%s %s' % (phys_hdds[0].Manufacturer, model)
        else:
            man_model = model

        if fws[0].VersionString:
            fw = fws[0].VersionString
        else:
            fw = 'N/A'

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

        temp = getattr(hdd, 'Temperature', None)
        if temp:
            temp_str = '%d' % temp
        else:
            temp_str = 'N/A'
        temp_str += u' °C'

        if hdd.Name != hdd.DeviceID and hdd.Name != model:
            result += [('  %s' % hdd.DeviceID, hdd.Name)]
        else:
            result += [('  %s' % hdd.DeviceID, '')]

        result += [('    Model:', man_model),
            ('    Firmware:', fw),
            ('    Capacity:', format_memory_size(hdd.Capacity)),
            ('    Form Factor:', form_factor),
            ('    HDD/SSD:', disk_type),
            ('    RPM:', rpm),
            ('    SMART Status:', smart),
            ('    Temperature:', temp_str)]

        tf.produce_output(result)
        result = [EMPTY_LINE]

    tf.produce_output(result)
    return []
