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
Logical Volume management.

Usage:
    %(cmd)s list [<vgs>]...
    %(cmd)s create <vg> <name> <size>
    %(cmd)s delete <lvs>...

Commands:
    list        List available logical volumes on given volume groups.
                If no volume groups are provided, all logical volumes are
                listed.

    create      Create a logical volume on given volume group.

                Size can be specified as number of extents using 'e' suffix,
                e.g. '100e' is 100 extents.

    delete      Delete given logical volume.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import lvm
from lmi.scripts.storage.common import str2size, str2device, size2str

def list(c, vgs=None):
    for lv in lvm.get_lvs(c, vgs):
        yield (lv.DeviceID,
                lv.Name,
                lv.ElementName,
                size2str(lv.NumberOfBlocks * lv.BlockSize))

def create(c, vg, name, size):
    vg = lvm.str2vg(c, vg)
    lv = lvm.create_lv(c, vg, name, str2size(size, vg.ExtentSize, 'E'))
    return 0

def delete(c, lvs):
    for lv in lvs:
        lvm.delete_lv(c, lv)
    return 0

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.lv_cmd:list'
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size")

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.lv_cmd:create'
    EXPECT = 0

class Delete(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.lv_cmd:delete'
    EXPECT = 0

Lv = command.register_subcommands(
        'Lv', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
        },
    )
