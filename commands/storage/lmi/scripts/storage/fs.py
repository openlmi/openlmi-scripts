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
Filesystem management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.storage import partition
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common
import pywbem
from lmi.shell import LMIInstance

FORMAT_DATA = 1
FORMAT_FS = 2
FORMAT_ALL = FORMAT_FS | FORMAT_DATA

def str2format(c, fmt):
    """
    Convert string with name of device to LMIInstance of the format on the
    device.

    If LMIInstance is provided, nothing is done and the instance is just
    returned. If a string is given, appropriate LMIInstance is looked up and
    returned.

    This functions throws an error when the device cannot be found.

    :type fmt: LMIInstance/CIM_LocalFileSystem or LMIInstance/LMI_DataFormat or
        string
    :param fmt: The format.

    :retval: LMIInstance/CIM_LocalFileSystem or LMIInstance/LMI_DataFormat
    """
    if isinstance(fmt, LMIInstance):
        return fmt
    if not isinstance(fmt, str):
        raise TypeError("string or _LMIInstance expected")
    device = common.str2device(fmt)
    return get_format_on_device(c, device)

def _get_fs_id(c, fsname):
    """
    Return integer value for given filesystem name in
    LMI_FileSystemConfigurationService.LMI_CreateFileSystem.FileSystemType

    :type fsname: string
    :param fsname: Name of the filesystem.
    :rtype: int
    """
    service = c.root.cimv2.LMI_FileSystemConfigurationService.first_instance()
    service.LMI_CreateFileSystem.XXX

def get_format_on_device(c, device, format_type=FORMAT_ALL):
    """
    Return filesystem or data format, which is on given device.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to to examine.
    :type format_type: int
    :param format_type: Type of format to find.

        * FORMAT_ALL - return either CIM_LocalFileSystem or LMI_DataFormat.
        * FORMAT_FS - return only CIM_LocalFileSystem or None, if there is no
            filesystem on the device.
        * FORMAT_DATA - return only LMI_DataFormat or None, if there is no
            data format on the device.

    :rtype: LMIInstance/CIM_LocalFileSystem or LMIInstance/LMI_DataFormat
    """
    device = common.str2device(c, device)
    if format_type == FORMAT_ALL:
        fmt = device.first_associator(
                AssocClass="CIM_ResidesOnExtent",
                Role="Antecedent")
    elif format_type == FORMAT_FS:
        fmt = device.first_associator(
                AssocClass="CIM_ResidesOnExtent",
                Role="Antecedent",
                ResultClass="CIM_LocalFileSystem")
    elif format_type == FORMAT_DATA:
        fmt = device.first_associator(
                AssocClass="CIM_ResidesOnExtent",
                Role="Antecedent",
                ResultClass="LMI_DataFormat")

    if fmt:
        return fmt
    return None

def get_formats(c, devices=None, format_type=FORMAT_ALL, nodevfs=False):
    """
    Retrieve list of filesystems on given devices.
    If no devices are given, all formats on all devices are returned.

    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param devices: Devices to list formats on.
    :type format_type: int
    :param format_type: Type of formats to find.

        * FORMAT_ALL - return either CIM_LocalFileSystem or LMI_DataFormat.
        * FORMAT_FS - return only CIM_LocalFileSystem or None, if there is no
            filesystem on the device.
        * FORMAT_DATA - return only LMI_DataFormat or None, if there is no
            data format on the device.

    :type nodevfs: bool
    :param nodevfs: Whether non-device filesystems like tmpfs, cgroup, procfs
        etc. should be returned.

    :rtype: list of LMIInstance/CIM_LocalFileSystem or
        LMIInstance/LMI_DataFormat
    """
    if devices:
        for device in devices:
            LOG().debug("Getting filesystem on %s", device.Name)
            yield get_format_on_device(device, format_type)
    else:
        # No devices supplied, list all formats
        if format_type & FORMAT_FS:
            cls = c.root.cimv2.CIM_LocalFileSystem
            for fs in c.root.cimv2.CIM_LocalFileSystem.instances():
                if fs.PersistenceType == cls.PersistenceTypeValues.Persistent \
                        or nodevfs:
                    yield fs
        if format_type & FORMAT_DATA:
            for fmt in c.root.cimv2.LMI_DataFormat.instances():
                yield fmt

def create_fs(c, devices, fs, label=None):
    """
    Format given devices with a filesystem.
    If multiple devices are provided, the format will span over all these
    devices (currently supported only for btrfs).

    
    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param devices: Devices to format.
    :type fs: string
    :param fs: Requested filesystem type (case-insensitive).
    :type label: string
    :param label: The filesystem label.
    :rtype: LMIInstance/CIM_LocalFileSystem
    """
    devs = []
    for device in devices:
        devs.append(common.str2device(device))

    fsid = _get_fs_id(c, fs)
    service = c.root.cimv2.LMI_FileSystemConfigurationService.first_instance()
    args = {
        'FyleSystemType': fsid,
        'InExtents': devs,
    }
    if label:
        args['ElementName'] = label
    (ret, outparams, err) = service.LMI_CreateFileSystem(**args)
    if ret != 0:
        raise LmiFailed("Cannot format the device %s: %s."
                % (devs[0].Name, service.LMI_CreateFileSystem.LMI_CreateFileSystemValues.value_name(ret)))
    return outparams['TheElement']

def delete_format(c, fmt):
    """
    Remove given filesystem or data format from all devices, where it resides.

    :type fmt: LMIInstance/CIM_LocalFileSystem or LMIInstance/LMI_DataFormat
    :param fmt: Format to delete.
    """
    fmt = str2format(c, fmt)
    if not fmt:
        LOG().info("Nothing to delete.")
        return

    service = c.root.cimv2.LMI_FileSystemConfigurationService.first_instance()
    (ret, outparams, err) = service.DeleteFileSystem(TheFileSystem=fmt)
    if ret != 0:
        raise LmiFailed("Cannot delete the format: %s."
                % (service.DeleteFileSystem.DeleteFileSystemValues.value_name(ret)))

def get_format_label(c, fmt):
    """
    Return short text description of the format, ready for printing.

    :type fmt: LMIInstance/CIM_LocalFileSystem or LMIInstance/LMI_DataFormat
    :param fmt: Format to describe.

    :rtype: string
    """
    if "FormatType" in fmt.properties():
        return fmt.FormatTypeDescription
    elif "FileSystemType" in fmt.properties():
        return fmt.FileSystemType
    else:
        return "Unknown"

def get_device_format_label(c, device):
    """
    Return short text description of the format, ready for printing.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to describe.

    :rtype: string
    """
    fmt = get_format_on_device(c, device)
    if fmt:
        return get_format_label(c, fmt)
    else:
        # check if there is partition table on the device
        table = partition.get_disk_partition_table(c, device)
        if table:
            cls = c.root.cimv2.LMI_DiskPartitionConfigurationCapabilities
            if table.PartitionStyle == cls.PartitionStyleValues.MBR:
                return "MS-DOS partition table"
            else:
                return cls.PartitionStyleValues.value_name(
                        table.PartitionStyle) + " partition table"
    return "Unknown"
