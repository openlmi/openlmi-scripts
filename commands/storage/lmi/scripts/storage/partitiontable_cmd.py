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
"""

from lmi.scripts.common import command
from lmi.scripts.storage import partition, show
from lmi.scripts.storage.common import size2str, str2device
from lmi.scripts.common import formatter
from lmi.scripts.common.formatter import command as fcmd

class Lister(command.LmiLister):
    COLUMNS = ('DeviceID', 'Name', 'ElementName', 'Largest free region')

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
        for (device, _table) in partition.get_partition_tables(ns, devices):
            largest_size = partition.get_largest_partition_size(ns, device)
            largest_size = size2str(largest_size,
                    self.app.config.human_friendly)

            yield (device.DeviceID,
                    device.Name,
                    device.ElementName,
                    largest_size
                    )


class Create(command.LmiCheckResult):
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


class Show(command.LmiLister):
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

PartitionTable = command.register_subcommands(
        'PartitionTable', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'show'    : Show,
        },
    )
