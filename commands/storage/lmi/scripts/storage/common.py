# Storage Management Providers
#
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
Common storage functionality.
"""

from lmi.scripts.common import get_logger
import re
from lmi.shell import LMIInstance
from lmi.scripts.common.errors import LmiFailed
from lmi.shell.LMIUtil import lmi_isinstance

LOG = get_logger(__name__)

ESCAPE_RE = re.compile(r'(["\\])')

def escape_cql(s):
    """
    Escape potentially unsafe string for CQL.

    It is generally not possible to do anything really harmful in CQL
    (there is no DELETE nor DROP TABLE), but just to be nice,
    all strings passed to CQL should escape backslash '\' and double quote
    '"'.

    :type s: string
    :param s: String to escape.
    :rtype: string
    """
    return ESCAPE_RE.sub(r'\\\1', s)

def str2device(ns, device):
    """
    Convert string with name of device to LMIInstance of the device.
    If LMIInstance is provided, nothing is done and the instance is just
    returned. If string is given, appropriate LMIInstance is looked up and
    returned.
    This functions throws an error when the device cannot be found.

    The main purpose of this function is to convert parameters in functions,
    where both string and LMIInstance is allowed.

    :type device: LMIInstance/CIM_StorageExtent or string with name of device
    :param device: Device to convert.
    :rtype: LMIInstance/CIM_StorageExtent
    """
    if isinstance(device, LMIInstance):
        return device
    if not isinstance(device, str):
        raise TypeError("string or LMIInstance expected, got %s"
                % device.__class__.__name__)
    query = 'SELECT * FROM CIM_StorageExtent WHERE ' \
                'DeviceID="%(device)s" ' \
                'OR Name="%(device)s" ' \
                'OR ElementName="%(device)s"' % {'device': escape_cql(device)}
    devices = ns.wql(query)
    if not devices:
        raise LmiFailed("Device '%s' not found" % (device,))
    if len(devices) > 1:
        raise LmiFailed("Too many devices with name '%s' found" % (device,))

    LOG().debug("String %s translated to device '%s'.",
            device, devices[0].DeviceID)
    return devices[0]

def str2vg(ns, vg):
    """
    Convert string with name of volume group to LMIInstance of the
    LMI_VGStoragePool.

    If LMIInstance is provided, nothing is done and the instance is just
    returned. If string is provided, appropriate LMIInstance is looked up and
    returned.

    This functions throws an error when the device cannot be found.

    The main purpose of this function is to convert parameters in functions,
    where both string and LMIInstance is allowed.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: VG to retrieve.
    :rtype: LMIInstance/LMI_VGStoragePool

    """
    if isinstance(vg, LMIInstance):
        return vg
    if not isinstance(vg, str):
        raise TypeError("string or LMIInstance expected, got %s"
                % vg.__class__.__name__)
    query = 'SELECT * FROM LMI_VGStoragePool WHERE ElementName="%(vg)s"' \
            % {'vg': escape_cql(vg)}
    vgs = ns.wql(query)
    if not vgs:
        raise LmiFailed("Volume Group '%s' not found." % (vg,))
    if len(vgs) > 1:
        raise LmiFailed("Too many volume groups with name '%s' found." % (vg,))

    LOG().debug("String %s translated to Volume Group '%s'.",
            vg, vgs[0].InstanceID)
    return vgs[0]


def str2obj(ns, obj):
    """
    Convert string with name of device or volume group to LMIInstance of the
    device or the volume group.

    If LMIInstance is provided, nothing is done and the instance is just
    returned. If string is given, appropriate LMIInstance is looked up and
    returned.
    This functions throws an error when the device or volume group
    cannot be found.

    The main purpose of this function is to convert parameters in functions,
    where both string and LMIInstance is allowed.

    :type obj: LMIInstance/CIM_StorageExtent or LMIInstance/LMI_VGStoragePool
        or string with name of device or pool
    :param obj: Object to convert.
    :rtype: LMIInstance/CIM_StorageExtent or LMIInstance/LMI_VGStoragePool
    """
    if isinstance(obj, LMIInstance):
        return obj
    if not isinstance(obj, str):
        raise TypeError("string or LMIInstance expected, got %s"
                % obj.__class__.__name__)

    # try VG first
    try:
        vg = str2vg(ns, obj)
        return vg
    except LmiFailed:
        pass

    # try device now
    return str2device(ns, obj)


multipliers = {
    'B': 1,
    'K': 1024,
    'M': 1024 * 1024,
    'G': 1024 * 1024 * 1024,
    'T': 1024 * 1024 * 1024 * 1024
}

def str2size(size, additional_unit_size=None, additional_unit_suffix=None):
    """
    Convert string from human-friendly size to bytes.
    The string is expected to be integer number, optionally with on of these
    suffixes:

      * k, K - kilobytes, 1024 bytes,
      * m, M - megabytes, 1024 * 1024 bytes,
      * g, G - gigabytes, 1024 * 1024 * 1024 bytes,
      * t, T - terabytes, 1024 * 1024 * 1024 * 1024 bytes,

    :type size: string
    :param size: The size to convert.
    :type additional_unit_size: int
    :param additional_unit_size: Additional unit size for
        additional_unit_suffix, e.g. 4 * 1024*1024 for extent size.
    :type additional_unit_suffix: string
    :param additional_unit_suffix: Additional suffix, e.g. 'E' for extents.
    :rtype: int
    """
    if size.isdigit():
        return int(size)
    suffix = size[-1:]
    s = size[:-1]

    if not s.isdigit():
        raise LmiFailed("'%s' is not valid size." % size)

    m = multipliers.get(suffix.upper(), None)
    if not m:
        if (additional_unit_suffix and suffix.upper()
                == additional_unit_suffix.upper()):
            m = int(additional_unit_size)
        else:
            # Sort the units by their size
            units = multipliers.items()
            if additional_unit_suffix:
                units.append((additional_unit_suffix, additional_unit_size))
            units = sorted(units, key=lambda x: x[1])
            raise LmiFailed("'%s' has invalid unit. Known units: %s."
                    % (size, ",".join([unit[0] for unit in units])))
    return int(s) * m

def size2str(size, human_friendly):
    """
    Convert size (in bytes) to string.

    :type size: int
    :param size: Size of something in bytes.
    :type human_friendly: bool
    :param human_friendly: If True, the returned string is returned in
        human-friendly units (KB, MB, ...).
    :rtype: string
    """
    if not human_friendly:
        return str(size)

    # find the highest multiplier, where the size/multiplier > 1
    mul = 1
    suffix = ''
    for (s, m) in multipliers.iteritems():
        if size / m > 1 and m > mul:
            mul = m
            suffix = s

    # integer numbers with 3- or 4- characters are fine, just round them and
    # add suffix
    if size / mul >= 100:
        size = int(round(size / float(mul)))
        return str(size) + suffix

    # 2- or less character numbers - add floating point and make the output
    # rounded to 4 characters (incl. '.')
    size = size / float(mul)
    decimals = len(str(int(size)))  # nr. of characters before '.'
    size = round(size, 3 - decimals)
    ret = str(size)

    # cut trailing zeroes
    while ret.endswith('0'):
        ret = ret[:-1]
    # cut trailing '.'
    if ret.endswith('.'):
        ret = ret[:-1]

    return ret + suffix

def get_devices(ns, devices=None):
    """
    Returns list of block devices.
    If no devices are given, all block devices on the system are returned.

    This functions just converts list of strings to list of appropriate
    LMIInstances.

    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param devices: Devices to list.

    :rtype: list of LMIInstance/CIM_StorageExtent.
    """
    if devices:
        LOG().debug("get_devices: Loading list of selected devices.")
        for dev in devices:
            yield str2device(ns, dev)
    else:
        LOG().debug("get_devices: Loading list of all devices.")
        for dev in ns.CIM_StorageExtent.instances():
            if lmi_isinstance(dev, ns.CIM_Memory):
                # Skip memory devices, they inherit from CIM_StorageExtent too
                LOG().debug("get_devices: Skipping memory device %s"
                        % dev.DeviceID)
                continue
            yield dev

def get_parents(ns, obj, deep=False):
    """
    Return list of all parents of given LMIInstance.

    For example:

      * If ``obj`` is LMIInstance/LMI_LVStorageExtent (=Logical Volume), it
        returns LMIInstance/LMI_VGStoragePool (=Volume Group).
      * If ``obj`` is LMIInstance/LMI_VGStoragePool (=Volume Group), it returns
        all its Physical Volumes (=LMIInstance/CIM_StorageExtent).

    :type obj: LMIInstance/CIM_StorageExtent or LMIInstance/LMI_VGStoragePool
        or string
    :param obj: Object to find parents of.
    :type deep: Boolean
    :param deep: Whether all parents of the object should be returned or only
        immediate ones.
    """
    obj = str2obj(ns, obj)
    if deep:
        # use loop of get_parents(ns, xxx, deep=False)
        known_parents = set()
        todo = [obj, ]  # a TO-DO list
        while todo:
            obj = todo.pop()
            new_parents = get_parents(ns, obj, False)
            for parent in new_parents:
                if "DeviceID" in parent.properties():
                    devid = parent.DeviceID
                else:
                    devid = parent.InstanceID
                if devid not in known_parents:
                    known_parents.add(devid)
                    todo.append(parent)
                    yield parent
        return

    # only direct parents requested
    if lmi_isinstance(obj, ns.CIM_StorageExtent):
        # Try to get parent VG first
        parents = obj.associators(
                AssocClass="LMI_LVAllocatedFromStoragePool",
                Role="Dependent")
        if parents:
            for parent in parents:
                yield parent
            return
        # Try usual BasedOn next
        parents = obj.associators(AssocClass="CIM_BasedOn", Role="Dependent")
        for parent in parents:
            # Be careful with logical partitions - they are BasedOn extended
            # partition, but we want to return appropriate disk instead.
            logical = ns.LMI_DiskPartition.PartitionTypeValues.Logical
            extended = ns.LMI_DiskPartition.PartitionTypeValues.Extended
            if (lmi_isinstance(parent, ns.CIM_DiskPartition)
                    and lmi_isinstance(obj, ns.CIM_DiskPartition)
                    and obj.PartitionType == logical
                    and parent.PartitionType == extended):
                LOG().debug("Looking for disk instead of extended partition %s"
                        % (parent.DeviceID))
                for p in get_parents(ns, parent, False):
                    yield p
            else:
                # It is not logical partition
                yield parent

    elif lmi_isinstance(obj, ns.CIM_StoragePool):
        # find VGs of the thin pool
        assoc_class = "LMI_VGAllocatedFromStoragePool"
        if assoc_class in ns.classes():
            parents = obj.associators(
                    AssocClass=assoc_class,
                    Role="Dependent")
            for parent in parents:
                yield parent

        # find physical volumes of the VG
        parents = obj.associators(
                AssocClass="LMI_VGAssociatedComponentExtent",
                Role="GroupComponent")
        for parent in parents:
            yield parent

    else:
        raise LmiFailed("CIM_StorageExtent or LMI_VGStragePool expected: %s",
            obj.classname)

def get_children(ns, obj, deep=False):
    """
    Return list of all children of given LMIInstance.

    For example:

      * If ``obj`` is LMIInstance/LMI_VGStoragePool (=Volume Group), it returns
        all its Logical Volumes (=LMIInstance/LMI_LVStorageExtent).
      * If ``obj`` is LMIInstance/LMI_StorageExtent of a disk, it returns
        all its partitions (=LMIInstance/CIM_GenericDiskPartition).
      * If ``obj`` is LMIInstance/LMI_DiskPartition and the partition is
        Physical Volume of a Volume Group,, it returns the pool
        (LMIInstance/LMI_VGStoragePool).

    :type obj: LMIInstance/CIM_StorageExtent or LMIInstance/LMI_VGStoragePool
        or string
    :param obj: Object to find children of.
    :type deep: Boolean
    :param deep: Whether all children of the object should be returned or only
        immediate ones.
    """
    obj = str2obj(ns, obj)
    if deep:
        # use loop of get_children(ns, xxx, deep=False)
        known_children = set()
        todo = [obj, ]  # a TO-DO list
        while todo:
            obj = todo.pop()
            new_children = get_children(ns, obj, False)
            for child in new_children:
                if "DeviceID" in child.properties():
                    devid = child.DeviceID
                else:
                    devid = child.InstanceID
                if devid not in known_children:
                    known_children.add(devid)
                    todo.append(child)
                    yield child
        return

    # only direct children requested
    if lmi_isinstance(obj, ns.CIM_StorageExtent):
        # try to find children VG first
        children = obj.associators(
                AssocClass="LMI_VGAssociatedComponentExtent",
                Role="PartComponent")
        if children:
            for child in children:
                yield child
            return

        # Extended partition don't have children
        extended = ns.LMI_DiskPartition.PartitionTypeValues.Extended
        if (lmi_isinstance(obj, ns.CIM_DiskPartition)
                    and obj.PartitionType == extended):
            return

        # try usual BasedOn next
        children = obj.associators(AssocClass="CIM_BasedOn", Role="Antecedent")
        for child in children:
            yield child
            # Be careful with logical partitions - they are BasedOn extended
            # partition, but we want to have them as children of appropriate
            # disk instead.
            if (lmi_isinstance(child, ns.CIM_DiskPartition)
                    and child.PartitionType == extended):
                LOG().debug("Looking for logical partitions on  %s"
                        % (child.DeviceID))
                for c in child.associators(AssocClass="CIM_BasedOn",
                        Role="Antecedent"):
                    yield c

    elif lmi_isinstance(obj, ns.CIM_StoragePool):
        # find thin pools from the VG
        assoc_class = "LMI_VGAllocatedFromStoragePool"
        if assoc_class in ns.classes():
            children = obj.associators(
                    AssocClass=assoc_class,
                    Role="Antecedent")
            for child in children:
                yield child

        # find LVs allocated from the VG
        children = obj.associators(
                AssocClass="LMI_LVAllocatedFromStoragePool",
                Role="Antecedent")
        for child in children:
            yield child
    else:
        raise LmiFailed("CIM_StorageExtent or LMI_VGStragePool expected: %s"
            % obj.classname)

