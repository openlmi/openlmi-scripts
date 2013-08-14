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

def list(ns, devices=None, __all=False):
    """
    This is tiny wrapper around get_fs to list only interesting fields.
    """
    for fmt in fs.get_formats(ns, devices, fs.FORMAT_ALL, __all):
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

def list_supported(ns):
    caps = ns.LMI_FileSystemConfigurationCapabilities.first_instance()
    cls = ns.LMI_FileSystemConfigurationCapabilities
    for fstype in caps.SupportedActualFileSystemTypes:
        yield [cls.SupportedActualFileSystemTypesValues.value_name(fstype)]

def create(ns, devices, type, __label=None):
    fs.create_fs(ns, devices, type, __label)

def delete(ns, devices):
    for dev in devices:
        fs.delete_format(ns, dev)

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
