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
    %(cmd)s create [ --gpt | --msdos ] <devices>...
    %(cmd)s show  [<devices>]...

Commands:
    list        List partition tables on given device.
                If no devices are provided, all partition tables are listed.

    create      Create a partition table on given devices. The devices must be
                empty, i.e. must not have any partitions on them. GPT partition
                table is created by default.

    show        Show detailed information about partition table on given
                devices. If no devices are provided, all of them are displayed.

Remarks:
    Use 'lmi fs delete' to remove a partition table from a device.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import partition, show
from lmi.scripts.storage.common import str2size, str2device

def list(c, devices=None):
    """
    This is tiny wrapper around get_partition_tables to list only interesting
    fields.
    """
    for (device, table) in partition.get_partition_tables(c, devices):
        yield (device.DeviceID,
                device.Name,
                device.ElementName,
                partition.get_largest_partition_size(c, device))

def cmd_show(c, devices=None):
    if not devices:
        devices = partition.get_partition_tables(c)
    for device in devices:
        show.partition_table_show(c, device)
        print ""
    return 0

def create(c, devices, __gpt, __msdos):
    if __msdos:
        ptype = partition.PARTITION_TABLE_TYPE_MSDOS
    else:
        ptype = partition.PARTITION_TABLE_TYPE_GPT
    for device in devices:
        partition.create_partition_table(c, device, ptype)

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.partitiontable_cmd:list'
    COLUMNS = ('DeviceID', 'Name', 'ElementName', 'Largest free region')

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partitiontable_cmd:create'
    EXPECT = None

class Show(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partitiontable_cmd:cmd_show'
    EXPECT = None

PartitionTable = command.register_subcommands(
        'PartitionTable', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'show'    : Show,
        },
    )
