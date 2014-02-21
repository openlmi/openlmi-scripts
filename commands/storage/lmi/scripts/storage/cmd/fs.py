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
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
Filesystem and other data format management.

Usage:
    %(cmd)s list [--all] [ <device> ...]
    %(cmd)s create [ --label=<label> ] <fstype>  <device> ...
    %(cmd)s delete <device> ...
    %(cmd)s list-supported

Commands:
    list        List filesystems and other data formats (RAID metadata,
                ...)  on given devices.
                If no devices are provided, all filesystems are listed.
                If --all option is set, all filesystem, including system
                ones like tmpfs, cgroups, procfs, sysfs etc are listed.

    create      Format device(s) with given filesystem.
                If more devices are given, the filesystem will span
                over these devices (currently supported only by btrfs).

                For list of available filesystem types, see output of
                %(cmd)s list-supported.

    delete      Delete given filesystem or data format (like partition
                table, RAID metadata, LUKS, physical volume metadata etc)
                on given devices.

    list-supported
                List supported filesystems, which can be used as
                %(cmd)s create <fstype> option.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)

LOG = get_logger(__name__)

class FSList(command.LmiLister):
    COLUMNS = ("Name", "ElementName", "Type")

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None, _all=False):
        """
        Implementation of 'fs list' command.
        """
        for fmt in fs.get_formats(ns, devices, fs.FORMAT_ALL, _all):
            name = fmt.Name
            label = fmt.ElementName
            if "FileSystemType" in fmt.properties():
                # it's CIM_LocalFileSystem
                # TODO: add filesystem size and free space
                fstype = fmt.FileSystemType
            else:
                # it must be LMI_DataFormat
                fstype = fmt.FormatTypeDescription
            # TODO: add free space when OpenLMI provides it
            yield (name, label, fstype)


class FSListSupported(command.LmiLister):
    COLUMNS = ('Filesystem',)

    def execute(self, ns):
        """
        Implementation of 'fs list-supported' command.
        """
        caps = ns.LMI_FileSystemConfigurationCapabilities.first_instance()
        cls = ns.LMI_FileSystemConfigurationCapabilities
        for fstype in caps.SupportedActualFileSystemTypes:
            fsname = cls.SupportedActualFileSystemTypesValues.value_name(fstype)
            yield [fsname.lower()]


class FSCreate(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices, fstype, _label=None):
        """
        Implementation of 'fs create' command.
        """
        fs.create_fs(ns, devices, fstype, _label)


class FSDelete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices):
        """
        Implementation of 'fs delete' command.
        """
        for dev in devices:
            fs.delete_format(ns, dev)

class FS(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list' : FSList,
            'create' : FSCreate,
            'delete' : FSDelete,
            'list-supported': FSListSupported,
    }
