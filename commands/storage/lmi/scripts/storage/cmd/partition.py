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
Partition management.

Usage:
    %(cmd)s list [ <device> ...]
    %(cmd)s create [ --logical | --extended ] <device> [<size>]
    %(cmd)s delete <partition> ...
    %(cmd)s show [ <partition> ...]

Commands:
    list        List available partitions on given devices.
                If no devices are provided, all partitions are listed.

    create      Create a partition on given device.

                If no size is given, the resulting partition will occupy the
                largest available space on disk.

                The command automatically creates extended and logical
                partitions using these rules:

                * If no partition type (logical or extended) is provided and
                  MS-DOS partition is requested and there is extended partition
                  already on the device, a logical partition is created.

                * If there is no extended partition on the device and there are
                  at most two primary partitions on the device, primary
                  partition is created.

                * If there is no extended partition and three primary partitions
                  already exist, new extended partition with all remaining space
                  is created and a logical partition with requested size is
                  created.

    delete      Delete given partitions.

    show        Show detailed information about given partitions. If no
                partitions are provided, all of them are displayed.

Options:
    size        Size of the new partition volume, by default in sectors.
                'T', 'G', 'M' or 'K' suffix can be used to specify other
                units (TiB, GiB, MiB and KiB) - '1K' specifies 1 KiB
                (= 1024 bytes).
                The suffix is case insensitive, i.e. 1g = 1G = 1073741824 bytes.

    device,
    partition   Identifier of the device/partition. Either one of:

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

    --logical   Override the automatic behavior and request logical partition.
    --extended  Override the automatic behavior and request extended partition.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)

LOG = get_logger(__name__)

class PartitionList(command.LmiLister):
    COLUMNS = ("Name", "Type", "Size")

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'partition list' command.
        """
        for part in partition.get_partitions(ns, devices):
            ptype = ""
            values = ns.LMI_DiskPartition.PartitionTypeValues
            if "PartitionType" in part.properties():
                if part.PartitionType == values.Primary:
                    ptype = "primary"
                elif part.PartitionType == values.Extended:
                    ptype = "extended"
                elif part.PartitionType == values.Logical:
                    ptype = "logical"
                else:
                    ptype = "unknown"
            size = size2str(part.NumberOfBlocks * part.BlockSize,
                    self.app.config.human_friendly)
            yield (part.Name, ptype, size)


class PartitionCreate(command.LmiCheckResult):
    EXPECT = None
    def transform_options(self, options):
        """
        There is only one <device> option, but docopt passes it as array
        (because in other commands it is used with '...'). So let's
        transform it to scalar.
        """
        options['<device>'] = options.pop('<device>')[0]

    def execute(self, ns, device, size=None, _extended=None, _logical=None):
        """
        Implementation of 'partition create' command.
        """
        device = str2device(ns, device)
        if size:
            size = str2size(size)
        ptype = None
        if _extended:
            ptype = partition.PARTITION_TYPE_EXTENDED
        elif _logical:
            ptype = partition.PARTITION_TYPE_LOGICAL
        partition.create_partition(ns, device, size, ptype)


class PartitionDelete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'partitions' option to 'partition' parameter name for better
        readability.
        """
        options['<partitions>'] = options.pop('<partition>')

    def execute(self, ns, partitions):
        """
        Implementation of 'partition delete' command.
        """
        for part in partitions:
            partition.delete_partition(ns, part)


class PartitionShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'partitions' option to 'partition' parameter name for better
        readability.
        """
        options['<partitions>'] = options.pop('<partition>')

    def execute(self, ns, partitions=None):
        """
        Implementation of 'partition show' command.
        """
        if not partitions:
            partitions = partition.get_partitions(ns)
        for part in partitions:
            part = str2device(ns, part)
            cmd = fcmd.NewTableCommand(title=part.DeviceID)
            yield cmd
            for line in show.partition_show(ns, part,
                    self.app.config.human_friendly):
                yield line

class Partition(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : PartitionList,
            'create'  : PartitionCreate,
            'delete'  : PartitionDelete,
            'show'    : PartitionShow,
    }

