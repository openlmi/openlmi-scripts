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
"""
LMI hardware provider client library.
"""

def get_single_instance(ns, instance_name):
    """
    Returns single instance of instance_name.

    :param instance_name: Instance name
    :type instance_name: String
    :returns: Instance of instance_name
    """
    if not hasattr(get_single_instance, 'instances'):
        get_single_instance.instances = {}
    if not instance_name in get_single_instance.instances:
        i = getattr(ns, instance_name)
        get_single_instance.instances[instance_name] = i.first_instance()
    return get_single_instance.instances[instance_name]

def get_all_instances(ns, instance_name):
    """
    Returns all instances of instance_name.

    :param instance_name: Instance name
    :type instance_name: String
    :returns: List of instances of instance_name
    """
    if not hasattr(get_all_instances, 'instances'):
        get_all_instances.instances = {}
    if not instance_name in get_all_instances.instances:
        i = getattr(ns, instance_name)
        get_all_instances.instances[instance_name] = i.instances()
    return get_all_instances.instances[instance_name]

def get_all_info(ns):
    """
    :returns: Tabular data of all available info.
    """
    empty_line = ("", "")
    result = get_system_info(ns)
    result.append(empty_line)
    result += get_chassis_info(ns)
    result.append(empty_line)
    result += get_cpu_info(ns)
    return result

def get_system_info(ns):
    """
    :returns: Tabular data from ``CIM_ComputerSystem`` instance.
    """
    i = get_single_instance(ns, 'CIM_ComputerSystem')
    return [('Hostname:', i.Name)]

def get_chassis_info(ns):
    """
    :returns: Tabular data from ``LMI_Chassis`` instance.
    """
    i = get_single_instance(ns, 'LMI_Chassis')
    result = [
          ('Chassis Type:', ns.LMI_Chassis.ChassisPackageTypeValues.value_name(
               i.ChassisPackageType)),
          ('Manufacturer:', i.Manufacturer),
          ('Model:', '%s (%s)' % (i.Model, i.ProductName)),
          ('Serial Number:', i.SerialNumber),
          ('Asset Tag:', i.Tag)]
    return result

def get_cpu_info(ns):
    """
    :returns: Tabular data from ``LMI_Chassis`` instance.
    """
    cpus = get_all_instances(ns, 'LMI_Processor')
    cpu_caps = get_all_instances(ns, 'LMI_ProcessorCapabilities')
    cores = 0
    threads = 0
    for i in cpu_caps:
        cores += i.NumberOfProcessorCores
        threads += i.NumberOfHardwareThreads
    result = [
          ('CPU:', cpus[0].Name),
          ('Topology:', "%d cpu(s), %d core(s), %d thread(s)" % \
                (len(cpus), cores, threads)),
          ('Max Freq:', "%d MHz" % cpus[0].MaxClockSpeed),
          ('Arch:', cpus[0].Architecture),
          ]
    return result
