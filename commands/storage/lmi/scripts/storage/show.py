# Storage Management Providers
#
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#

"""
Functions to display information about block devices.
"""

from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common, partition, raid, lvm, fs
from lmi.scripts.common import formatter

def device_show(ns, device, human_friendly):
    """
    Print extended information about the device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param part: Device to show.
    :type human_friendly: bool
    :param human_friendly: If True, the device sizes are shown in human-friendly
        units (KB, MB, ...).
    """
    device = common.str2device(ns, device)
    if device.classname == "LMI_MDRAIDStorageExtent":
        for line in raid_show(ns, device, human_friendly):
            yield line
    elif device.classname == "LMI_LVStorageExtent":
        for line in lv_show(ns, device, human_friendly):
            yield line
    elif device.classname == "LMI_GenericDiskPartition":
        for line in partition_show(ns, device, human_friendly):
            yield line
    elif device.classname == "LMI_DiskPartition":
        for line in partition_show(ns, device, human_friendly):
            yield line
    else:
        yield("Type", "Generic block device")
        for line in device_show_device(ns, device, human_friendly):
            yield line
        for line in device_show_data(ns, device, human_friendly):
            yield line

def partition_show(ns, part, human_friendly):
    """
    Print extended information about the partition.

    :type part: LMIInstance/CIM_GenericDiskPartition or string
    :param part: Partition to show.
    """
    part = common.str2device(ns, part)
    yield("Type", "Partition")
    for line in device_show_device(ns, part, human_friendly):
        yield line

    if "PartitionType" in part.properties():
        cls = ns.LMI_DiskPartition
        if part.PartitionType == cls.PartitionTypeValues.Primary:
            ptype = "primary"
        elif part.PartitionType == cls.PartitionTypeValues.Extended:
            ptype = "extended"
        elif part.PartitionType == cls.PartitionTypeValues.Logical:
            ptype = "logical"
        else:
            ptype = "unknown"
    else:
        ptype = "N/A"
    yield("Partition Type", ptype)

    basedon = part.first_reference(ResultClass="CIM_BasedOn", Role="Dependent")
    yield("Starting sector", basedon.StartingAddress)
    yield("Ending sector", basedon.EndingAddress)

    disk = partition.get_partition_disk(ns, part)
    yield("Sector Size", common.size2str(disk.BlockSize, human_friendly))
    yield("Disk", disk.Name)
    for line in device_show_data(ns, part, human_friendly):
        yield line

def partition_table_show(ns, disk, human_friendly):
    """
    Print extended information about the partition table on given disk.

    :type disk: LMIInstance/CIM_StorageExtent or string
    :param disk: Device with partition table to show.
    """
    disk = common.str2device(ns, disk)
    yield("Data Type", "Partition Table")

    table = disk.first_associator(AssocClass="CIM_InstalledPartitionTable")
    cls = ns.LMI_DiskPartitionConfigurationCapabilities
    if table.PartitionStyle == cls.PartitionStyleValues.MBR:
        yield("Partition Table Type", "MS-DOS")
    else:
       yield("Partition Table Type", cls.PartitionStyleValues.value_name(
                table.PartitionStyle))
    yield("Partition Table Size (in blocks)", table.PartitionTableSize)
    yield("Largest Free Space", common.size2str(
            partition.get_largest_partition_size(ns, disk), human_friendly))

    parts = partition.get_disk_partitions(ns, disk)
    partnames = [part.Name for part in parts]
    yield("Partitions", " ".join(partnames))

def raid_show(ns, r, human_friendly):
    """
    Print extended information about the RAID.

    :type r: LMIInstance/LMI_MDRAIDStorageExtent or string
    :param r: RAID to show.
    """
    r = common.str2device(ns, r)
    yield("Type", "MD RAID")
    for line in device_show_device(ns, r, human_friendly):
        yield line

    yield("RAID Level", r.Level)
    members = raid.get_raid_members(ns, r)
    mnames = [r.Name for r in members]
    yield("RAID Members", " ".join(mnames))

    for line in device_show_data(ns, r, human_friendly):
        yield line

def vg_show(ns, vg, human_friendly):
    """
    Print extended information about the Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to show.
    """
    yield("Type", "Volume Group")
    vg = common.str2vg(ns, vg)
    yield("InstanceID", vg.InstanceID)
    yield("ElementName", vg.ElementName)
    yield("Extent Size", common.size2str(vg.ExtentSize, human_friendly))
    yield("Total Size", common.size2str(vg.TotalManagedSpace, human_friendly))
    yield("Total Extents", vg.TotalExtents)
    yield("Free Space", common.size2str(vg.RemainingManagedSpace,
            human_friendly))
    yield("Free Extents", vg.RemainingExtents)

    pvs = lvm.get_vg_pvs(ns, vg)
    pvnames = [pv.Name for pv in pvs]
    yield("Physical Volumes", " ".join(pvnames))

    lvs = lvm.get_vg_lvs(ns, vg)
    lvnames = [lv.Name for lv in lvs]
    yield("Logical Volumes", " ".join(lvnames))

def lv_show(ns, lv, human_friendly):
    """
    Print extended information about the Logical Volume.

    :type lv: LMIInstance/LMI_LVStorageExtent or string
    :param lv: Logical Volume to show.
    """
    lv = common.str2device(ns, lv)
    yield("Type", "Logical Volume")
    for line in device_show_device(ns, lv, human_friendly):
        yield line

    vg = lvm.get_lv_vg(ns, lv)
    yield("Volume Group", vg.ElementName)
    yield("Extent Size", common.size2str(vg.ExtentSize, human_friendly))
    yield("Number of Occupied Extents", \
            lv.BlockSize * lv.NumberOfBlocks / vg.ExtentSize)

    for line in device_show_data(ns, lv, human_friendly):
        yield line

def device_show_device(ns, device, human_friendly):
    """
    Print basic information about storage device, common to all device types.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to show.
    """
    device = common.str2device(ns, device)

    yield("DeviceID", device.DeviceID)
    yield("Name", device.Name)
    yield("ElementName", device.ElementName)
    yield("Total Size", common.size2str(
            device.NumberOfBlocks * device.BlockSize, human_friendly))
    yield("Block Size", common.size2str(device.BlockSize, human_friendly))

def device_show_data(ns, device, human_friendly):
    """
    Display description of data on the device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to show.
    """
    device = common.str2device(ns, device)
    fmt = fs.get_format_on_device(ns, device)
    if fmt:
        if "FormatType" in fmt.properties():
            for line in format_show(ns, fmt, human_friendly):
                yield line
        elif "FileSystemType" in fmt.properties():
            for line in fs_show(ns, fmt, human_friendly):
                yield line
        else:
            yield("Data Format", "Unknown")
    else:
        part_table = partition.get_disk_partition_table(ns, device)
        if part_table:
            for line in partition_table_show(ns, device, human_friendly):
                yield line
        else:
            yield("Data Format", "Unknown")

def format_show(ns, fmt, human_friendly):
    """
    Display description of data on the device.

    :type fmt: LMIInstance/LMI_DataFormat or string
    :param fmt: Format to show.
    """
    fmt = fs.str2format(ns, fmt)
    yield("Data Format", fmt.FormatTypeDescription)
    if "UUID" in fmt.properties() and fmt.UUID:
        yield("UUID", fmt.UUID)

def fs_show(ns, fmt, human_friendly):
    """
    Display description of filesystem on the device.

    :type fmt: LMIInstance/CIM_LocalFileSystem or string
    :param fmt: Filesystem to show.
    """
    yield("Filesystem", fmt.FileSystemType)
    if "UUID" in fmt.properties() and fmt.UUID:
        yield("UUID", fmt.UUID)
    cls = ns.LMI_LocalFileSystem
    yield("Persistence", cls.PersistenceTypeValues.value_name(
            fmt.PersistenceType))

    # TODO: add mount points
