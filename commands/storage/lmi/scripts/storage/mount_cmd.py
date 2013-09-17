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
# Authors: Jan Synacek <jsynacek@redhat.com>
#

"""
Mounting management functions.

Usage:
    %(cmd)s list [ --all ]
    %(cmd)s create <device> <mountpoint> [ (-t <fs_type>) (-o <options>) (-p <other_options>) ]
    %(cmd)s delete <target>
    %(cmd)s show [ --all ]

Commands:
    list     List mounted filesystems with a device attached to them.
             Optionally, show all mounted filesystems.

    create   Mount a specified device on the path given by mountpoint.
             Optionally, filesystem type, common options (filesystem
             independent) and filesystem specific options can be provided. If no
             filesystem type is specified, it is automatically detected.

             Common options can be provided as a comma-separated string of
             'option_name:value' items.  Possible option names are:

             AllowExecution AllowMandatoryLock AllowSUID AllowUserMount
             AllowWrite Auto Dump FileSystemCheckOrder InterpretDevices
             OtherOptions Silent SynchronousDirectoryUpdates SynchronousIO
             UpdateAccessTimes UpdateDirectoryAccessTimes UpdateFullAccessTimes
             UpdateRelativeAccessTimes

             Possible option values for all of the options except for
             FileSystemCheckOrder are 't', 'true', 'f', 'false'. All of them are
             case insensitive.
             The FileSystemCheckOrder option's value is a number.

             Other options can be specified as a string.

             Examples:

             create /dev/vda1 /mnt -t ext4 -o 'AllowWrite:F,InterpretDevices:false'

             create /dev/vda2 /mnt -o 'FileSystemCheckOrder:2'

             create /dev/vda3 /mnt -p 'user_xattr,barrier=0'

             create /dev/vda4 /mnt -o 'Dump:t, AllowMandatoryLock:t' -p 'acl'

    delete   Unmount a mounted filesystem. Can be specified either as a device
             path or a mountpoint.

    show     Show detailed information about mounted filesystems with a device
             attached to them. Optionally, show all mounted filesystems.
"""

from lmi.scripts.common import command, get_logger
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import mount


class Lister(command.LmiLister):
    COLUMNS = ('FileSystemSpec', 'FileSystemType', 'MountPointPath', 'Options', 'OtherOptions')
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, all=None):
        """
        Implementation of 'mount list' command.
        """
        if all is False:
            transients = [mnt.Name for mnt in ns.LMI_TransientFileSystem.instances()]

        for mnt in mount.get_mounts(ns):
            # treat root specially (can be mounted twice - as a rootfs and with
            # a device)
            if mnt.FileSystemSpec == 'rootfs':
                continue

            if all is False and mnt.MountPointPath != '/':
                # do not list nodevice filesystems
                name = 'PATH=' + mnt.MountPointPath
                if name in transients:
                    continue

            opts_str = mount.build_opts_str(mnt)

            yield(mnt.FileSystemSpec,
                  mnt.FileSystemType,
                  mnt.MountPointPath,
                  opts_str[0],
                  opts_str[1])

class Show(command.LmiLister):
    COLUMNS = ('Name', 'Value')
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, all=None):
        """
        Implementation of 'mount show' command.
        """
        if all is False:
            transients = [mnt.Name for mnt in ns.LMI_TransientFileSystem.instances()]

        yield fcmd.NewTableCommand('Mounted filesystems')
        for mnt in mount.get_mounts(ns):
            # treat root specially (can be mounted twice - as a rootfs and with
            # a device)
            if mnt.FileSystemSpec == 'rootfs':
                continue

            if all is False and mnt.MountPointPath != '/':
                # do not list nodevice filesystems
                name = 'PATH=' + mnt.MountPointPath
                if name in transients:
                    continue

            opts_str = mount.build_opts_str(mnt)

            yield('Filesystem', '%s (%s)' % (mnt.FileSystemSpec, mnt.FileSystemType))
            yield('Mountpoint', mnt.MountPointPath)
            yield('Options', opts_str[0])
            yield('OtherOptions', opts_str[1])
            yield ''

class Create(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, device, mountpoint, fs_type=None, options=None, other_options=None):
        """
        Implementation of 'mount create' command.
        """
        return mount.mount_create(ns, device, mountpoint, fs_type, options, other_options)

class Delete(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, target):
        """
        Implementation of 'mount delete' command.
        """
        return mount.mount_delete(ns, target)

Mount = command.register_subcommands(
        'Mount', __doc__,
        { 'list'    : Lister,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
