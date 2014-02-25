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

import pywbem

from lmi.shell import LMIClassNotFound
from lmi.scripts.common import get_logger
from lmi.scripts.common import get_computer_system

GREEN_COLOR = 1
YELLOW_COLOR = 2
RED_COLOR = 3

EMPTY_LINE = ('', '')
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
    except (LMIClassNotFound, pywbem.CIMError) as err:
        if (   isinstance(err, pywbem.CIMError)
           and err.args[0] != pywbem.CIM_ERR_NOT_SUPPORTED):
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
    STANDALONE = True
    return result

def get_system_info(ns):
    """
    :returns: Tabular data of system info, from the ``LMI_Chassis`` instance.
    :rtype: List of tuples
    """
    result = init_result(ns)
    i = get_single_instance(ns, 'LMI_Chassis')
    if not i:
        result.append(('System info:', 'N/A'))
        return result
    if i.Model and i.ProductName:
        model = '%s (%s)' % (i.Model, i.ProductName)
    elif i.Model:
        model = i.Model
    elif i.ProductName:
        model = i.ProductName
    else:
        model = 'N/A'
    virt = getattr(i, 'VirtualMachine', None)
    if not virt:
        virt = 'N/A'
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
    result = init_result(ns)
    i = get_single_instance(ns, 'LMI_Baseboard')
    if not i:
        result.append(('Motherboard info:', 'N/A'))
        return result
    model = i.Model
    manufacturer = i.Manufacturer
    if not model:
        model = 'N/A'
    if not manufacturer:
        manufacturer = 'N/A'
    result += [
          ('Motherboard:', model),
          ('Manufacturer:', manufacturer)]
    return result

def get_cpu_info(ns):
    """
    :returns: Tabular data of processor info.
    :rtype: List of tuples
    """
    result = init_result(ns)
    cpus = get_all_instances(ns, 'LMI_Processor')
    cpu_caps = get_all_instances(ns, 'LMI_ProcessorCapabilities')
    if not cpus or not cpu_caps:
        result.append(('Processor info:', 'N/A'))
        return result
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
    return result

def get_memory_info(ns):
    """
    :returns: Tabular data of memory info.
    :rtype: List of tuples
    """
    result = init_result(ns)
    memory = get_single_instance(ns, 'LMI_Memory')
    phys_memory = get_all_instances(ns, 'LMI_PhysicalMemory')
    memory_slots = get_all_instances(ns, 'LMI_MemorySlot')
    if not memory:
        result.append(('Memory info:', 'N/A'))
        return result

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

    result.append(('Memory:', size))
    result += modules
    result.append(('Slots:', slots))
    return result

