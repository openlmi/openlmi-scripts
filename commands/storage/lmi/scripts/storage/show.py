# Software Management Providers
#
# Copyright (C) 2012-2013 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
Functions to display information about block devices.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common, partition, raid, lvm, fs

def device_show(c, device):
    """
    Print extended information about the device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param part: Device to show.
    """
    device = common.str2device(c, device)
    if device.classname == "LMI_MDRAIDStorageExtent":
        raid_show(c, device)
    elif device.classname == "LMI_LVStorageExtent":
        lv_show(c, device)
    elif device.classname == "LMI_GenericDiskPartition":
        partition_show(c, device)
    elif device.classname == "LMI_DiskPartition":
        partition_show(c, device)
    else:
        print "Generic Device", device.DeviceID
        device_show_device(c, device)
        device_show_data(c, device)

def partition_show(c, part):
    """
    Print extended information about the partition.

    :type part: LMIInstance/CIM_GenericDiskPartition or string
    :param part: Partition to show.
    """
    part = common.str2device(c, part)
    print "Partition", part.DeviceID
    device_show_device(c, part)

    if "PartitionType" in part.properties():
        cls = c.root.cimv2.LMI_DiskPartition
        if part.PartitionType == cls.PartitionTypeValues.Primary:
            type = "primary"
        elif part.PartitionType == cls.PartitionTypeValues.Extended:
            type = "extended"
        elif part.PartitionType == cls.PartitionTypeValues.Logical:
            type = "logical"
        else:
            type = "unknown"
    else:
        type = "N/A"
    print "Partition Type:", type

    basedon = part.first_reference(ResultClass="CIM_BasedOn", Role="Dependent")
    print "Starting sector:", basedon.StartingAddress
    print "Ending sector:", basedon.EndingAddress

    disk = partition.get_partition_disk(c, part)
    print "Sector Size:", disk.BlockSize
    print "Disk:", disk.Name
    device_show_data(c, part)

def partition_table_show(c, disk):
    """
    Print extended information about the partition table on given disk.

    :type disk: LMIInstance/CIM_StorageExtent or string
    :param disk: Device with partition table to show.
    """
    disk = common.str2device(c, disk)
    print "Partition Table", disk.DeviceID

    table = disk.first_associator(AssocClass="CIM_InstalledPartitionTable")
    cls = c.root.cimv2.LMI_DiskPartitionConfigurationCapabilities
    if table.PartitionStyle == cls.PartitionStyleValues.MBR:
        print "Partition Table Type:", "MS-DOS"
    else:
        print "Partition Table Type:", cls.PartitionStyleValues.value_name(
                table.PartitionStyle)
    print "Partition Table Size:", table.PartitionTableSize
    print "Largest Free Space:", common.size2str(
            partition.get_largest_partition_size(c, disk))

    parts = partition.get_disk_partitions(c, disk)
    partnames = [part.Name for part in parts]
    print "Partitions:", " ".join(partnames)

def raid_show(c, r):
    """
    Print extended information about the RAID.

    :type r: LMIInstance/LMI_MDRAIDStorageExtent or string
    :param r: RAID to show.
    """
    r = common.str2device(c, r)
    print "MD RAID Array", r.DeviceID
    device_show_device(c, r)

    print "RAID Level:", r.Level
    members = raid.get_raid_members(c, r)
    mnames = [r.Name for r in members]
    print "RAID Members:", " ".join(mnames)
    device_show_data(c, r)

def vg_show(c, vg):
    """
    Print extended information about the Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to show.
    """
    vg = lvm.str2vg(c, vg)
    print "InstanceID:", vg.InstanceID
    print "ElementName", vg.ElementName
    print "Extent Size:", common.size2str(vg.ExtentSize)
    print "Total Size:", common.size2str(vg.TotalManagedSpace)
    print "Total Extents:", vg.TotalExtents
    print "Free Space:", vg.RemainingManagedSpace
    print "Free Extents:", vg.RemainingExtents

    pvs = lvm.get_vg_pvs(c, vg)
    pvnames = [pv.Name for pv in pvs]
    print "Physical Volumes:", " ".join(pvnames)

    lvs = lvm.get_vg_lvs(c, vg)
    lvnames = [lv.Name for lv in lvs]
    print "Logical Volumes:", " ".join(lvnames)

def lv_show(c, lv):
    """
    Print extended information about the Logical Volume.

    :type lv: LMIInstance/LMI_LVStorageExtent or string
    :param lv: Logical Volume to show.
    """
    lv = common.str2device(c, lv)
    print "Logical Volume", lv.DeviceID
    device_show_device(c, lv)

    vg = lvm.get_lv_vg(c, lv)
    print "Volume Group:", vg.ElementName
    print "Extent Size:", common.size2str(vg.ExtentSize)
    print "Number of Occupied Extents:", lv.BlockSize * lv.NumberOfBlocks / vg.ExtentSize
    device_show_data(c, lv)

def device_show_device(c, device):
    """
    Print basic information about storage device, common to all device types.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to show.
    """
    device = common.str2device(c, device)

    print "Name:", device.Name
    print "ElementName:", device.ElementName
    print "Total Size:", common.size2str(
            device.NumberOfBlocks * device.BlockSize)
    print "Block Size:", device.BlockSize

def device_show_data(c, device):
    """
    Display description of data on the device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to show.
    """
    device = common.str2device(c, device)
    fmt = fs.get_format_on_device(c, device)
    if fmt:
        if "FormatType" in fmt.properties():
            format_show(c, fmt)
        elif "FileSystemType" in fmt.properties():
            fs_show(c, fmt)
        else:
            print "Data Format:", "Unknown"
    else:
        part_table = partition.get_disk_partition_table(c, device)
        if part_table:
            partition_table_show(c, device)

def format_show(c, fmt):
    """
    Display description of data on the device.

    :type fmt: LMIInstance/LMI_DataFormat or string
    :param fmt: Format to show.
    """
    fmt = fs.str2format(c, fmt)
    print "Data Format:", fmt.FormatTypeDescription
    if "UUID" in fmt.properties() and fmt.UUID:
        print "UUID:", fmt.UUID

def fs_show(c, fmt):
    """
    Display description of filesystem on the device.

    :type fmt: LMIInstance/CIM_LocalFileSystem or string
    :param fmt: Filesystem to show.
    """
    print "Filesystem:", fmt.FileSystemType
    if "UUID" in fmt.properties() and fmt.UUID:
        print "UUID:", fmt.UUID
    cls = c.root.cimv2.LMI_LocalFileSystem
    print "Persistence:", cls.PersistenceTypeValues.value_name(
            fmt.PersistenceType)

    # TODO: add mount points
