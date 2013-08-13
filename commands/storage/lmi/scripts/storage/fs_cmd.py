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
Filesystem and other data format management.

Usage:
    %(cmd)s list [--all] [<devices>]...
    %(cmd)s create [ --label=<label> ] <type> [<devices>]...
    %(cmd)s delete <devices>...
    %(cmd)s list-supported

Commands:
    list        List filesystems and and other data formats (RAID metadata, ...)
                on given devices.
                If no devices are provided, all filesystems are listed.
                If --all option is set, all filesystem, including system ones
                like tmpfs, cgroups, procfs, sysfs etc are listed.

    create      Format device(s) with given filesystem.
                If more devices are given, the filesystem will span
                over these devices (currently supported only by btrfs).

                For list of available filesystem types, see output of
                %(cmd)s list-supported.

    delete      Delete given filesystem or data format (like partition table,
                RAID metadata, LUKS, physical volume metadata etc)
                on given devices.

    list-supported
                List supported filesystems, which can be used as
                %(cmd)s create <type> option.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import fs
from lmi.scripts.storage.common import str2device

def list(c, devices=None, __all=False):
    """
    This is tiny wrapper around get_fs to list only interesting fields.
    """
    for fmt in fs.get_formats(c, devices, fs.FORMAT_ALL, __all):
        device = fmt.first_associator(AssocClass="CIM_ResidesOnExtent")
        if device:
            devname = device.DeviceID
        else:
            devname = "(none)"
        name = fmt.Name
        label = fmt.ElementName
        if "FileSystemType" in fmt.properties():
            # it's CIM_LocalFileSystem
            # TODO: add filesystem size and free space
            type = fmt.FileSystemType
        else:
            # it must be LMI_DataFormat
            type = fmt.FormatTypeDescription
        yield (devname, name, label, type)

def list_supported(c):
    caps = c.root.cimv2.LMI_FileSystemConfigurationCapabilities.first_instance()
    cls = c.root.cimv2.LMI_FileSystemConfigurationCapabilities
    for fstype in caps.SupportedActualFileSystemTypes:
        yield [cls.SupportedActualFileSystemTypesValues.value_name(fstype)]

def create(c, devices, type, __label=None):
    fs.create_fs(c, devices, type, __label)

def delete(c, devices):
    for dev in devices:
        fs.delete_format(c, dev)

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.fs_cmd:list'
    COLUMNS = ('Device', 'Name', "ElementName", "Type")

class ListSupported(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.fs_cmd:list_supported'
    COLUMNS = ('Filesystem',)

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.fs_cmd:create'
    EXPECT = 0

class Delete(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.fs_cmd:delete'
    EXPECT = 0

Fs = command.register_subcommands(
        'fs', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'list-supported': ListSupported,
        },
    )
