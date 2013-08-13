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
Volume Group management.

Usage:
    %(cmd)s list
    %(cmd)s create [ --extent-size=<size> ] <name> <devices>...
    %(cmd)s delete <vgs>...
    %(cmd)s show [<vgs>]...

Commands:
    list        List all volume groups on the system.

    create      Create Volume Group with given name from list of devices.

    delete      Delete given Volume Groups.

    show        Show detailed information about given Volume Groups. If no
                Volume Groups are provided, all of them are displayed.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import lvm, show
from lmi.scripts.storage.common import str2device, str2size, size2str

def list(c):
    for vg in lvm.get_vgs(c):
        yield (vg.InstanceID,
                vg.ElementName,
                size2str(vg.ExtentSize),
                size2str(vg.RemainingManagedSpace))

def cmd_show(c, vgs=None):
    if not vgs:
        vgs = lvm.get_vgs(c)
    for vg in vgs:
        show.vg_show(c, vg)
        print ""
    return 0

def create(c, name, devices, __extent_size=None):
    if __extent_size:
        __extent_size = str2size(__extent_size)
    lvm.create_vg(c, devices, name, __extent_size)
    return 0

def delete(c, vgs):
    for vg in vgs:
        lvm.delete_vg(c, vg)
    return 0

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.vg_cmd:list'
    COLUMNS = ('InstanceID', 'ElementName', "ExtentSize", "Free space")

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.vg_cmd:create'
    EXPECT = 0

class Delete(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.vg_cmd:delete'
    EXPECT = 0

class Show(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.vg_cmd:cmd_show'
    EXPECT = 0

Vg = command.register_subcommands(
        'vg', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
