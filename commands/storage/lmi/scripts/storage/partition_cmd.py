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
Partition management.

Usage:
    %(cmd)s list [<devices>]...
    %(cmd)s create [ --logical | --extended ] <device> [<size>]
    %(cmd)s delete <partitions>...

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
                at most two primary partitions on the device, primary partition
                is created.

                * If there is no extended partition and three primary partitions
                already exist, new extended partition with all remaining space
                is created and a logical partition with requested size is
                created.

    delete      Delete given partitions.

Options:
    size        Size of the partition in sectors.
    --logical   Override the automatic behavior and request logical partition.
    --extended  Override the automatic behavior and request extended partition.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import partition
from lmi.scripts.storage.common import str2size, str2device, size2str

def list(c, devices=None):
    """
    This is tiny wrapper around get_partitions to list only interesting fields.
    """
    for part in partition.get_partitions(c, devices):
        type = ""
        if "PartitionType" in part.properties():
            if part.PartitionType == 1:  # TODO: use enumeration
                type = "primary"
            elif part.PartitionType == 2:
                type = "extended"
            elif part.PartitionType == 3:
                type = "logical"
            else:
                type = "unknown"
        yield (part.DeviceID,
                part.Name,
                part.ElementName,
                type,
                size2str(part.NumberOfBlocks * part.BlockSize))

def create(c, device, size=None, __extended=None, __logical=None):
    device = str2device(c, device)
    size = str2size(size)
    ptype = None
    print device, size
    if __extended:
        ptype = partition.PARTITION_TYPE_EXTENDED
    elif __logical:
        ptype = partition.PARTITION_TYPE_LOGICAL
    p = partition.create_partition(c, device, size, ptype)
    print "Partition %s, with DeviceID %s created." % (p.Name, p.DeviceID)

def delete(c, partitions):
    for part in partitions:
        partition.delete_partition(c, part)

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:list'
    COLUMNS = ('DeviceID', "Name", "ElementName", "Type", "Size")

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:create'
    EXPECT = 0

class Delete(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:delete'
    EXPECT = 0

Partition = command.register_subcommands(
        'Partition', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
        },
    )
