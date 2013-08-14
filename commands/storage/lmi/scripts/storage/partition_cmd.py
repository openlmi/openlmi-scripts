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
    %(cmd)s create [ --logical | --extended ] <device> [<size>]
    %(cmd)s delete <partitions>...
    %(cmd)s show [<partitions>]...

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

    show        Show detailed information about given partitions. If no
                partitions are provided, all of them are displayed.

Options:
    size        Size of the partition in sectors.
    --logical   Override the automatic behavior and request logical partition.
    --extended  Override the automatic behavior and request extended partition.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import partition, show
from lmi.scripts.storage.common import str2size, str2device, size2str

def list(ns, devices=None):
    """
    This is tiny wrapper around get_partitions to list only interesting fields.
    """
    for part in partition.get_partitions(ns, devices):
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

def cmd_show(ns, partitions=None):
    if not partitions:
        partitions = partition.get_partitions(ns)
    for part in partitions:
        show.partition_show(ns, part)
        print ""
    return 0

def create(ns, device, size=None, __extended=None, __logical=None):
    device = str2device(ns, device)
    size = str2size(size)
    ptype = None
    if __extended:
        ptype = partition.PARTITION_TYPE_EXTENDED
    elif __logical:
        ptype = partition.PARTITION_TYPE_LOGICAL
    p = partition.create_partition(ns, device, size, ptype)
    print "Partition %s, with DeviceID %s created." % (p.Name, p.DeviceID)

def delete(ns, partitions):
    for part in partitions:
        partition.delete_partition(ns, part)

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:list'
    COLUMNS = ('DeviceID', "Name", "ElementName", "Type", "Size")

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:create'
    EXPECT = 0

class Delete(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:delete'
    EXPECT = 0

class Show(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.partition_cmd:cmd_show'
    EXPECT = 0

Partition = command.register_subcommands(
        'Partition', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
