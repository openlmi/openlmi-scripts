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
Partition management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common
import pywbem

PARTITION_TYPE_PRIMARY = 1
PARTITION_TYPE_EXTENDED = 2
PARTITION_TYPE_LOGICAL = 3

PARTITION_TABLE_TYPE_GPT = 3  # from CIM_DiskPartitionConfigurationCapabilities
PARTITION_TABLE_TYPE_MSDOS = 2

def get_disk_partitions(ns, disk):
    """
    Return list of partitions on the device (not necessarily disk).

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device which should be partitioned.
    :rtype: List of LMIInstance/CIM_GenericDiskPartition.
    """
    disk = common.str2device(ns, disk)
    parts = disk.associators(
            AssocClass="CIM_BasedOn", Role="Antecedent")
    for part in parts:
        yield part
        # List also logical partitions, which are 'BasedOn'
        # on extended partition.
        if "PartitionType" in part.properties():
            cls = ns.LMI_DiskPartition
            if part.PartitionType == cls.PartitionTypeValues.Extended:
                for logical in part.associators(
                        AssocClass="CIM_BasedOn", Role="Antecedent"):
                    yield logical


def get_partition_disk(ns, partition):
    """
    Return a device on which is located the given partition.

    :type partition: LMIInstance/CIM_GenericDiskPartition or string
    :param partition: Partition to examine.
    :rtype: LMIInstance/CIM_StorageExtent.
    """
    partition = common.str2device(ns, partition)
    device = partition.first_associator(
            AssocClass="CIM_BasedOn", Role="Dependent")
    if "PartitionType" in device.properties():
        # we got extended partition, find the disk
        device = device.first_associator(
            AssocClass="CIM_BasedOn", Role="Dependent")
    return device

def get_partitions(ns, devices=None):
    """
    Retrieve list of partitions on given devices.
    If no devices are given, all partitions on all devices are returned.

    :type devices: List of LMIInstance/CIM_StorageExtent or list of string
    :param devices: Devices to list partitions on.
    :rtype: List of LMIInstance/CIM_GenericPartition.
    """
    if devices:
        for device in devices:
            device = common.str2device(ns, device)
            LOG().debug("Getting list of partitions on %s", device.Name)
            parts = get_disk_partitions(ns, device)
            for part in parts:
                yield part
    else:
        # No devices supplied, list all partitions.
        for part in ns.CIM_GenericDiskPartition.instances():
            yield part

def create_partition(ns, device, size=None, partition_type=None):
    """
    Create new partition on given device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device which should be partitioned.
    :type size: int
    :param size: Size of the device, in blocks. See device's BlockSize
        to get it. If no size is provided, the largest possible partition
        is created.
    :type partition_type: int
    :param partition_type: Requested partition type.
        See PARTITION_TYPE_xxx variables. If no type is given, extended partition
        will be automatically created as 4th partition on MS-DOS style partition
        table with a logical partition with requested size on it.

    :rtype: LMIInstance/CIM_GenericDiskPartition.
    """
    device = common.str2device(ns, device)
    setting = None

    try:
        args = { 'extent': device}
        if size:
            args['Size'] = pywbem.Uint64(size)

        if partition_type:
            # create a setting and modify it
            caps = ns.LMI_DiskPartitionConfigurationCapabilities\
                        .first_instance()
            (ret, outparams, err) = caps.CreateSetting()
            if ret != 0:
                if err:
                    LmiFailed("Cannot create " \
                        "LMI_DiskPartitionConfigurationSetting for the " \
                        "partition: %s." % err)
                raise LmiFailed("Cannot create " \
                        "LMI_DiskPartitionConfigurationSetting for the " \
                        "partition: %d." % ret)
            setting = outparams['setting'].to_instance()
            setting.PartitionType = pywbem.Uint16(partition_type)
            (ret, _outparams, err) = setting.push()
            if ret != 0:
                if err:
                    raise LmiFailed("Cannot change " \
                            "LMI_DiskPartitionConfigurationSetting for the " \
                            "partition: %s." % err)
                raise LmiFailed("Cannot change " \
                        "LMI_DiskPartitionConfigurationSetting for the " \
                        "partition: %d." % ret)
            args['Goal'] = setting

        print args
        service = ns.LMI_DiskPartitionConfigurationService.first_instance()
        (ret, outparams, err) = service.SyncLMI_CreateOrModifyPartition(**args)
        if ret != 0:
            if err:
                raise LmiFailed("Cannot create the partition: %s." % err)
            values = service.LMI_CreateOrModifyPartition\
                    .LMI_CreateOrModifyPartitionValues
            raise LmiFailed("Cannot create the partition: %s."
                    % (values.value_name(ret)))
    finally:
        if setting:
            setting.delete()
    return outparams['Partition']


def delete_partition(ns, partition):
    """
    Remove given partition

    :type partition: LMIInstance/CIM_GenericDiskPartition
    :param partition: Partition to delete.
    """
    partition = common.str2device(ns, partition)
    service = ns.LMI_DiskPartitionConfigurationService.first_instance()
    (ret, _outparams, err) = service.SyncLMI_DeletePartition(
            Partition=partition)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot delete the partition: %s." % err)
        values = service.LMI_DeletePartition.LMI_DeletePartitionValues
        raise LmiFailed("Cannot delete the partition: %s."
                % (values.value_name(ret)))

def create_partition_table(ns, device, table_type):
    """
    Create new partition table on a device. The device must be empty, i.e.
    must not have any partitions on it.

    :type device: LMIInstance/CIM_StorageExtent
    :param device: Device where the partition table should be created.
    :type table_type: int
    :param table_type: Requested partition table type. See
        PARTITION_TABLE_TYPE_xxx variables.
    """
    device = common.str2device(ns, device)
    query = "SELECT * FROM LMI_DiskPartitionConfigurationCapabilities WHERE " \
            "PartitionStyle=%d" % table_type
    caps = ns.wql(query)

    if not caps:
        raise LmiFailed("Unsupported partition table type: %d" % table_type)
    cap = caps[0]
    service = ns.LMI_DiskPartitionConfigurationService.first_instance()
    (ret, _outparams, err) = service.SetPartitionStyle(
            Extent=device,
            PartitionStyle=cap)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot create partition table: %s." % err)
        values = service.SetPartitionStyle.SetPartitionStyleValues
        raise LmiFailed("Cannot create partition table: %s."
                % (values.value_name(ret)))


def get_partition_tables(ns, devices=None):
    """
    Returns list of partition tables on given devices.
    If no devices are given, all partitions on all devices are returned.

    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param devices: Devices to list partition tables on.

    :rtype: List of tuples (LMIInstance/CIM_StorageExtent,
        LMIInstance/LMI_DiskPartitionConfigurationCapabilities).
    """
    if not devices:
        tables = ns.LMI_InstalledPartitionTable.instances()
        for table in tables:
            yield table.Antecedent.to_instance(), table.Dependent.to_instance()
    else:
        for device in devices:
            device = common.str2device(ns, device)
            table = get_disk_partition_table(ns, device)
            if table:
                yield device, table

def get_disk_partition_table(ns, device):
    """
    Returns LMI_DiskPartitionTableCapabilities representing partition table
    on given disk.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device which should be examined.

    :rtype: LMIInstance/LMI_DiskPartitionConfigurationCapabilities.
    """
    device = common.str2device(ns, device)
    table = device.first_associator(
                    AssocClass="LMI_InstalledPartitionTable")
    return table

def get_largest_partition_size(ns, device):
    """
    Returns size of the largest free region (in blocks), which can accommodate
    a partition on given device.
    There must be partition table present on this device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device:  Device which should be examined.
    :rtype: int
    """
    device = common.str2device(ns, device)
    # find the partition table (=LMI_DiskPartitionConfigurationCapabilities)
    cap = device.first_associator(
            ResultClass="LMI_DiskPartitionConfigurationCapabilities")
    if not cap:
        raise LmiFailed("Cannot find partition table on %s" % device.name)
    (ret, outparams, err) = cap.FindPartitionLocation(Extent=device)
    if ret != 0:
        if err:
            LOG().warning("Cannot find largest partition size: %s." % err)
        else:
            LOG().warning("Cannot find largest partition size: %d." % ret)
        return 0
    blocks = outparams['EndingAddress'] - outparams['StartingAddress']
    size = blocks * device.BlockSize
    return size
