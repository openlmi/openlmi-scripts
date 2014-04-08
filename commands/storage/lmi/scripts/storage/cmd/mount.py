# coding=utf-8
# Storage Management Providers
#
# Copyright (C) 2014 Red Hat, Inc. All rights reserved.
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
#          Jan Safranek <jsafrane@redhat.com>
#
"""
Mount management.

Usage:
    %(cmd)s list [ --all ] [ <target> ... ]
    %(cmd)s create <device> <mountpoint> [ (-t <fs_type>) (-o <options>) ]
    %(cmd)s delete <target>
    %(cmd)s show [ --all ] [ <target> ... ]

Commands:
    list     List mounted filesystems with a device attached to them.
             <target> can be specified either as device names
             or mountpoints.

    create   Mount a specified device on the path given by mountpoint.
             Optionally, filesystem type, common options (filesystem
             independent) and filesystem specific options can be provided. If no
             filesystem type is specified, it is automatically detected.

             Options can be provided as a comma-separated string of
             'option_name:value' items.  Possible option names are:

             AllowExecution AllowMandatoryLock AllowSUID AllowUserMount
             AllowWrite Auto Dump FileSystemCheckOrder InterpretDevices
             Silent SynchronousDirectoryUpdates SynchronousIO
             UpdateAccessTimes UpdateDirectoryAccessTimes UpdateFullAccessTimes
             UpdateRelativeAccessTimes

             Possible option values for all of the options except for
             FileSystemCheckOrder are 't', 'true', 'f', 'false'. All of them are
             case insensitive.
             The FileSystemCheckOrder option's value is a number.

             In case an option is not recognized as being one of the possible
             options listed above, it's used as a filesystem dependent option.

             Examples:

             create /dev/vda1 /mnt -t ext4 -o 'AllowWrite:F,InterpretDevices:false'

             create /dev/vda2 /mnt -o 'FileSystemCheckOrder:2'

             create /dev/vda3 /mnt -o 'user_xattr,barrier=0'

             create /dev/vda4 /mnt -o 'Dump:t, AllowMandatoryLock:t, acl'

    delete   Unmount a mounted filesystem. Can be specified either as a device
             path or a mountpoint.

    show     Show detailed information about mounted filesystems with a device
             attached to them. <target> can be specified either as device names
             or mountpoints.
             <spec>. Optionally, show all mounted filesystems.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)
from lmi.scripts.common.errors import LmiFailed

LOG = get_logger(__name__)

def get_mounts_for_targets(ns, targets):
    """
    Return list of LMI_MountedFilesystem instances for given devices or
    directories.
    :type mntspec: List of strings or LMIInstance/CIM_StorageExtents.
    :param mntspec: Mount specifications. If a string is provided as a mount
                    specification, it can be either device name or mount
                    directory.
    """
    mounts = []
    for target in targets:
        try:
            device = str2device(ns, target)
            if device:
                target = device.Name
        except LmiFailed:
            # we did not find CIM_StorageExtent for the device, it must be non
            # device filesystem specification
            pass

        mnts = ns.LMI_MountedFileSystem.instances({'FileSystemSpec':target}) + \
            ns.LMI_MountedFileSystem.instances({'MountPointPath':target})
        mounts += mnts
    return mounts

class MountList(command.LmiLister):
    COLUMNS = ('FileSystemSpec', 'FileSystemType', 'MountPointPath', 'Options')
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, targets=None, _all=None):
        """
        Implementation of 'mount list' command.
        """
        if targets:
            mounts = get_mounts_for_targets(ns, targets)
        else:
            mounts = mount.get_mounts(ns)

        if _all is False:
            transients = [mnt.Name for mnt in ns.LMI_TransientFileSystem.instances()]

        for mnt in mounts:
            # treat root specially (can be mounted twice - as a rootfs and with
            # a device)
            if mnt.FileSystemSpec == 'rootfs':
                continue

            if _all is False and mnt.MountPointPath != '/':
                # do not list nodevice filesystems
                name = 'PATH=' + mnt.MountPointPath
                if name in transients:
                    continue

            yield(mnt.FileSystemSpec,
                  mnt.FileSystemType,
                  mnt.MountPointPath,
                  mount.build_opts_str(mnt))

class MountShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, _all=None, targets=None):
        """
        Implementation of 'mount show' command.
        """
        if targets:
            mounts = get_mounts_for_targets(ns, targets)
        else:
            mounts = mount.get_mounts(ns)

        if _all is False:
            transients = [mnt.Name for mnt in ns.LMI_TransientFileSystem.instances()]

        yield fcmd.NewTableCommand('Mounted filesystems')
        for mnt in mounts:
            # treat root specially (can be mounted twice - as a rootfs and with
            # a device)
            if mnt.FileSystemSpec == 'rootfs':
                continue

            if _all is False and mnt.MountPointPath != '/':
                # do not list nodevice filesystems
                name = 'PATH=' + mnt.MountPointPath
                if name in transients:
                    continue

            yield('Filesystem', '%s (%s)' % (mnt.FileSystemSpec, mnt.FileSystemType))
            yield('Mountpoint', mnt.MountPointPath)
            yield('Options', mount.build_opts_str(mnt))
            yield ''

class MountCreate(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, device, mountpoint, fs_type=None, options=None):
        """
        Implementation of 'mount create' command.
        """
        return mount.mount_create(ns, device, mountpoint, fs_type, options)

class MountDelete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        There is only one <target> option, but docopt passes it as array
        (because in other commands it is used with '...'). So let's
        transform it to scalar.
        """
        options['<target>'] = options.pop('<target>')[0]


    def execute(self, ns, target):
        """
        Implementation of 'mount delete' command.
        """
        return mount.mount_delete(ns, target)

class Mount(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : MountList,
            'create'  : MountCreate,
            'delete'  : MountDelete,
            'show'    : MountShow,
    }

