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
from lmi.scripts.common.errors import LmiFailed

"""
Filesystem management functions.
"""

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
    Convert string with name of device to LMIInstance of the format on the device.

    :param c: (``LmiConnection``)
    :param device: (Either ``LMIInstance`` of ``CIM_LocalFileSystem`` or
    ``LMI_DataFormat`` or ``string`` with name of device) If ``LMIInstance`` is
    given, nothing is done and the instance is just returned. If string is
    given, appropriate ``LMIInstance`` is looked up and returned.

    :retval: ``LMIInstance`` of appropriate LMI_DataFormat or
    CIM_LocalFileSystem.

    This functions throws an error when the device cannot be found.
    """
    if isinstance(fmt, LMIInstance):
        return fmt
    if not isinstance(fmt, str):
        raise TypeError("string or _LMIInstance expected")
    device = common.str2device(fmt)
    return get_format_on_device(c, device)

def get_fs_id(c, fsname):
    """
    Return integer value of given filesystem name in
    LMI_FileSystemConfigurationService.LMI_CreateFileSystem.FileSystemType

    :param fsname: (``string``) Name of the filesystem.
    """
    service = c.root.cimv2.LMI_FileSystemConfigurationService.first_instance()
    service.LMI_CreateFileSystem.XXX

def get_format_on_device(c, device, format_type=FORMAT_ALL):
    """
    Return filesystem or data format, which is on given device.

    :param device: (Either ``LMIInstance``s of ``CIM_StorageExtent``
    or ``string`` with name of the device.) Device to to query.
    :param format_type: (``int``) Type of formats to find.
    FORMAT_ALL - return either CIM_LocalFileSystem or LMI_DataFormat.
    FORMAT_FS - return only CIM_LocalFileSystem or None, if there is no
    filesystem on the device.
    FORMAT_DATA - return only LMI_DataFormat or None, if there is no
    data format on the device.

    :retval: (``LMIInstance`` of ``CIM_LocalFileSystem`` or ``LMI_DataFormat``)
    or None, if there is no recognizable format on the device.
    """
    if format_type == FORMAT_ALL:
        result = "CIM_ManagedElement"
    elif format_type == FORMAT_FS:
        result = "CIM_LocalFileSystem"
    elif format_type == FORMAT_DATA:
        result = "LMI_DataFormat"

    device = common.str2device(c, device)
    fmt = device.first_associator(
                AssocClass="CIM_ResidesOnExtent",
                Role="Antecedent",
                ResultClass=result)
    if fmt:
        return fmt
    return None

def get_formats(c, devices=None, format_type=FORMAT_ALL, nodevfs=False):
    """
    Retrieve list of filesystems on given devices.

    :param c:
    :param devices: (Either list of ``LMIInstance``s of ``CIM_StorageExtent``
    or list of ``string``s with name of the devices.) Devices to list formats
    on.
    FORMAT_ALL - return either CIM_LocalFileSystem or LMI_DataFormat.
    FORMAT_FS - return only CIM_LocalFileSystem or None, if there is no
    filesystem on the device.
    FORMAT_DATA - return only LMI_DataFormat or None, if there is no
    data format on the device.
    :param nodevfs: Whether non-device filesystems like tmpfs, cgroup, procfs
    etc.

    If no devices are given, all formats on all devices are returned.

    :retval: list of ``LMIInstance``s of ``CIM_LocalFileSystem`` or
    ``LMI_DataFormat``
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

    :param c:
    :param devices: (Either list of ``LMIInstance``s of ``CIM_StorageExtent``
    or list of ``string``s with name of the devices.) Devices to list formats
    on.
    :param fs: (``string``) Requested filesystem type.
    :param label: (``string``) The filesystem label.
    :retval: (``LMIInstance``) of the CIM_LocalFileSystem.
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

    :param c:
    :param fmt: (Either ``LMIInstance``s of ``LMI_DataFormat`` or
    ``CIM_LocalFileSystem`` or ``string`` with name of the device.)
    Format to delete.
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
