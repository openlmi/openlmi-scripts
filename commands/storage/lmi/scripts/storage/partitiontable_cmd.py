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
