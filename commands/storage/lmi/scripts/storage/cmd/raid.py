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
MD RAID management.

Usage:
    %(cmd)s list
    %(cmd)s create [ --name=<name> ] <level> <device> ...
    %(cmd)s delete <device> ...
    %(cmd)s show [ <device> ...]

Commands:
    list        List all MD RAID devices on the system.

    create      Create MD RAID array with given RAID level from list of devices.

    delete      Delete given MD RAID devices.

    show        Show detailed information about given MD RAID devices. If no
                devices are provided, all MD RAID devices are displayed.

Options:
    device      Identifier of the device. Either one of:

                * DeviceID of appropriate CIM_StorageExtent object. This is
                  internal OpenLMI ID of the device and it should be stable
                  across system reboots.

                * Device name directly in /dev directory, such as '/dev/sda'.
                  This device name is available as Name property of
                  CIM_StorageExtent object.

                * Name of MD RAID or logical volume. This method cannot be used
                  when the name is not unique, for example when there are two
                  logical volumes with the same name, allocated from different
                  volume groups. This name is available as ElementName
                  property of CIM_StorageExtent object.

    level       RAID level. Supported levels are: 0, 1, 4, 5, 6, 10.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)

LOG = get_logger(__name__)

class RaidList(command.LmiLister):
    COLUMNS = ('Name', "Level", "Nr. of members")

    def execute(self, ns):
        """
        Implementation of 'raid list' command.
        """
        for r in raid.get_raids(ns):
            members = raid.get_raid_members(ns, r)
            yield (r.ElementName, r.Level, len(members))


class RaidCreate(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices, level, _name=None):
        """
        Implementation of 'raid create' command.
        """
        raid.create_raid(ns, devices, int(level), _name)


class RaidDelete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices):
        """
        Implementation of 'raid delete' command.
        """
        for dev in devices:
            raid.delete_raid(ns, dev)


class RaidShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'raid show' command.
        """
        if not devices:
            devices = raid.get_raids(ns)
        for r in devices:
            r = str2device(ns, r)
            cmd = fcmd.NewTableCommand(title=r.DeviceID)
            yield cmd
            for line in show.raid_show(ns, r, self.app.config.human_friendly):
                yield line

class Raid(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : RaidList,
            'create'  : RaidCreate,
            'delete'  : RaidDelete,
            'show'    : RaidShow,
    }

