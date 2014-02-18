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
Partition table management.

Usage:
    %(cmd)s list [ <device> ...]
    %(cmd)s create [ --gpt | --msdos ] <device> ...
    %(cmd)s show  [ <device> ...]

Commands:
    list        List partition tables on given device.
                If no devices are provided, all partition tables are listed.

    create      Create a partition table on given devices. The devices must be
                empty, i.e. must not have any partitions on them. GPT partition
                table is created by default.

    show        Show detailed information about partition table on given
                devices. If no devices are provided, all of them are displayed.

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

    --gpt       Create GPT partition table (default).
    --msdos     Create MS-DOS partition table.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)

LOG = get_logger(__name__)

class PartitionTableList(command.LmiLister):
    COLUMNS = ('Name', 'Type', 'Largest free region')

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'partition-table list' command.
        """
        cls = ns.LMI_DiskPartitionConfigurationCapabilities
        for (device, table) in partition.get_partition_tables(ns, devices):
            LOG().debug("Examining %s", device.Name)
            largest_size = partition.get_largest_partition_size(ns, device)
            largest_size = size2str(largest_size,
                    self.app.config.human_friendly)

            if table.PartitionStyle == cls.PartitionStyleValues.MBR:
                table_type = "MS-DOS"
            else:
                table_type = cls.PartitionStyleValues.value_name(
                        table.PartitionStyle)

            yield (device.Name, table_type, largest_size)


class PartitionTableCreate(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices, _gpt, _msdos):
        """
        Implementation of 'partition-table create' command.
        """
        if _msdos:
            ptype = partition.PARTITION_TABLE_TYPE_MSDOS
        else:
            ptype = partition.PARTITION_TABLE_TYPE_GPT
        for device in devices:
            partition.create_partition_table(ns, device, ptype)


class PartitionTableShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'partition-table show' command.
        """
        if not devices:
            ret = partition.get_partition_tables(ns)
            devices = [i[0] for i in ret]
        for device in devices:
            device = str2device(ns, device)
            cmd = fcmd.NewTableCommand(title=device.DeviceID)
            yield cmd
            for line in show.partition_table_show(
                    ns, device, self.app.config.human_friendly):
                yield line

class PartitionTable(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : PartitionTableList,
            'create'  : PartitionTableCreate,
            'show'    : PartitionTableShow,
    }

