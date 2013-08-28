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
        raid_show(ns, device, human_friendly)
    elif device.classname == "LMI_LVStorageExtent":
        lv_show(ns, device, human_friendly)
    elif device.classname == "LMI_GenericDiskPartition":
        partition_show(ns, device, human_friendly)
    elif device.classname == "LMI_DiskPartition":
        partition_show(ns, device, human_friendly)
    else:
        print "Generic Device", device.DeviceID
        device_show_device(ns, device, human_friendly)
        device_show_data(ns, device, human_friendly)

def partition_show(ns, part, human_friendly):
    """
    Print extended information about the partition.

    :type part: LMIInstance/CIM_GenericDiskPartition or string
    :param part: Partition to show.
    """
    part = common.str2device(ns, part)
    print "Partition", part.DeviceID
    device_show_device(ns, part, human_friendly)

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
    print "Partition Type:", ptype

    basedon = part.first_reference(ResultClass="CIM_BasedOn", Role="Dependent")
    print "Starting sector:", basedon.StartingAddress
    print "Ending sector:", basedon.EndingAddress

    disk = partition.get_partition_disk(ns, part)
    print "Sector Size:", common.size2str(disk.BlockSize, human_friendly)
    print "Disk:", disk.Name
    device_show_data(ns, part, human_friendly)

def partition_table_show(ns, disk, human_friendly):
    """
    Print extended information about the partition table on given disk.

    :type disk: LMIInstance/CIM_StorageExtent or string
    :param disk: Device with partition table to show.
    """
    disk = common.str2device(ns, disk)
    print "Partition Table", disk.DeviceID

    table = disk.first_associator(AssocClass="CIM_InstalledPartitionTable")
    cls = ns.LMI_DiskPartitionConfigurationCapabilities
    if table.PartitionStyle == cls.PartitionStyleValues.MBR:
        print "Partition Table Type:", "MS-DOS"
    else:
        print "Partition Table Type:", cls.PartitionStyleValues.value_name(
                table.PartitionStyle)
    print "Partition Table Size (in blocks):", table.PartitionTableSize
    print "Largest Free Space:", common.size2str(
            partition.get_largest_partition_size(ns, disk), human_friendly)

    parts = partition.get_disk_partitions(ns, disk)
    partnames = [part.Name for part in parts]
    print "Partitions:", " ".join(partnames)

def raid_show(ns, r, human_friendly):
    """
    Print extended information about the RAID.

    :type r: LMIInstance/LMI_MDRAIDStorageExtent or string
    :param r: RAID to show.
    """
    r = common.str2device(ns, r)
    print "MD RAID Array", r.DeviceID
    device_show_device(ns, r, human_friendly)

    print "RAID Level:", r.Level
    members = raid.get_raid_members(ns, r)
    mnames = [r.Name for r in members]
    print "RAID Members:", " ".join(mnames)
    device_show_data(ns, r, human_friendly)

def vg_show(ns, vg, human_friendly):
    """
    Print extended information about the Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to show.
    """
    vg = common.str2vg(ns, vg)
    print "InstanceID:", vg.InstanceID
    print "ElementName", vg.ElementName
    print "Extent Size:", common.size2str(vg.ExtentSize, human_friendly)
    print "Total Size:", common.size2str(vg.TotalManagedSpace, human_friendly)
    print "Total Extents:", vg.TotalExtents
    print "Free Space:", common.size2str(vg.RemainingManagedSpace,
            human_friendly)
    print "Free Extents:", vg.RemainingExtents

    pvs = lvm.get_vg_pvs(ns, vg)
    pvnames = [pv.Name for pv in pvs]
    print "Physical Volumes:", " ".join(pvnames)

    lvs = lvm.get_vg_lvs(ns, vg)
    lvnames = [lv.Name for lv in lvs]
    print "Logical Volumes:", " ".join(lvnames)

def lv_show(ns, lv, human_friendly):
    """
    Print extended information about the Logical Volume.

    :type lv: LMIInstance/LMI_LVStorageExtent or string
    :param lv: Logical Volume to show.
    """
    lv = common.str2device(ns, lv)
    print "Logical Volume", lv.DeviceID
    device_show_device(ns, lv, human_friendly)

    vg = lvm.get_lv_vg(ns, lv)
    print "Volume Group:", vg.ElementName
    print "Extent Size:", common.size2str(vg.ExtentSize, human_friendly)
    print "Number of Occupied Extents:", \
            lv.BlockSize * lv.NumberOfBlocks / vg.ExtentSize
    device_show_data(ns, lv, human_friendly)

def device_show_device(ns, device, human_friendly):
    """
    Print basic information about storage device, common to all device types.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to show.
    """
    device = common.str2device(ns, device)

    print "Name:", device.Name
    print "ElementName:", device.ElementName
    print "Total Size:", common.size2str(
            device.NumberOfBlocks * device.BlockSize, human_friendly)
    print "Block Size:", common.size2str(device.BlockSize, human_friendly)

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
            format_show(ns, fmt, human_friendly)
        elif "FileSystemType" in fmt.properties():
            fs_show(ns, fmt, human_friendly)
        else:
            print "Data Format:", "Unknown"
    else:
        part_table = partition.get_disk_partition_table(ns, device)
        if part_table:
            partition_table_show(ns, device, human_friendly)

def format_show(ns, fmt, human_friendly):
    """
    Display description of data on the device.

    :type fmt: LMIInstance/LMI_DataFormat or string
    :param fmt: Format to show.
    """
    fmt = fs.str2format(ns, fmt)
    print "Data Format:", fmt.FormatTypeDescription
    if "UUID" in fmt.properties() and fmt.UUID:
        print "UUID:", fmt.UUID

def fs_show(ns, fmt, human_friendly):
    """
    Display description of filesystem on the device.

    :type fmt: LMIInstance/CIM_LocalFileSystem or string
    :param fmt: Filesystem to show.
    """
    print "Filesystem:", fmt.FileSystemType
    if "UUID" in fmt.properties() and fmt.UUID:
        print "UUID:", fmt.UUID
    cls = ns.LMI_LocalFileSystem
    print "Persistence:", cls.PersistenceTypeValues.value_name(
            fmt.PersistenceType)

    # TODO: add mount points
