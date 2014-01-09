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
Filesystem management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.storage import partition
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common
from lmi.shell import LMIInstance

FORMAT_DATA = 1
FORMAT_FS = 2
FORMAT_ALL = FORMAT_FS | FORMAT_DATA

def str2format(ns, fmt):
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
    device = common.str2device(ns, fmt)
    return get_format_on_device(ns, device)

def _get_fs_id(ns, fsname):
    """
    Return integer value for given filesystem name in
    LMI_FileSystemConfigurationService.LMI_CreateFileSystem.FileSystemType

    :type fsname: string
    :param fsname: Name of the filesystem.
    :rtype: int
    """
    service = ns.LMI_FileSystemConfigurationService.first_instance()
    values = service.LMI_CreateFileSystem.FileSystemTypeValues
    fsid = values.values_dict().get(fsname.upper(), None)
    if not fsid:
        raise LmiFailed("Unsupported filesystem name: %s" % fsname)
    return fsid

def get_format_on_device(ns, device, format_type=FORMAT_ALL):
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
    device = common.str2device(ns, device)
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

def get_formats(ns, devices=None, format_type=FORMAT_ALL, nodevfs=False):
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
            device = common.str2device(ns, device)
            LOG().debug("Getting filesystem on %s", device.Name)
            fs = get_format_on_device(ns, device, format_type)
            if fs:
                yield fs
    else:
        # No devices supplied, list all formats
        if format_type & FORMAT_FS:
            cls = ns.CIM_LocalFileSystem
            for fs in ns.CIM_LocalFileSystem.instances():
                if fs.PersistenceType == cls.PersistenceTypeValues.Persistent \
                        or nodevfs:
                    yield fs
        if format_type & FORMAT_DATA:
            for fmt in ns.LMI_DataFormat.instances():
                yield fmt

def create_fs(ns, devices, fs, label=None):
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
        devs.append(common.str2device(ns, device))

    fsid = _get_fs_id(ns, fs)
    service = ns.LMI_FileSystemConfigurationService.first_instance()
    args = {
        'FileSystemType': fsid,
        'InExtents': devs,
    }
    if label:
        args['ElementName'] = label
    (ret, outparams, err) = service.SyncLMI_CreateFileSystem(**args)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot format the device %s: %s."
                    % (devs[0].Name, err))
        values = service.LMI_CreateFileSystem.LMI_CreateFileSystemValues
        raise LmiFailed("Cannot format the device %s: %s."
                % (devs[0].Name, values.value_name(ret)))
    return outparams['TheElement']

def delete_format(ns, fmt):
    """
    Remove given filesystem or data format from all devices, where it resides.

    :type fmt: LMIInstance/CIM_LocalFileSystem or LMIInstance/LMI_DataFormat
    :param fmt: Format to delete.
    """
    fmt = str2format(ns, fmt)
    if not fmt:
        LOG().info("Nothing to delete.")
        return

    service = ns.LMI_FileSystemConfigurationService.first_instance()
    (ret, _outparams, err) = service.SyncDeleteFileSystem(TheFileSystem=fmt)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot delete the format: %s." % err)
        values = service.DeleteFileSystem.DeleteFileSystemValues
        raise LmiFailed("Cannot delete the format: %s."
                % (values.value_name(ret)))

def get_format_label(_ns, fmt):
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

def get_device_format_label(ns, device):
    """
    Return short text description of the format, ready for printing.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to describe.

    :rtype: string
    """
    LOG().debug("get_device_format_label: Loading filesystem information for %s"
            % (device.DeviceID))
    fmt = get_format_on_device(ns, device)
    if fmt:
        return get_format_label(ns, fmt)
    else:
        # check if there is partition table on the device
        table = partition.get_disk_partition_table(ns, device)
        if table:
            cls = ns.LMI_DiskPartitionConfigurationCapabilities
            if table.PartitionStyle == cls.PartitionStyleValues.MBR:
                return "MS-DOS partition table"
            else:
                return cls.PartitionStyleValues.value_name(
                        table.PartitionStyle) + " partition table"
    return "Unknown"
