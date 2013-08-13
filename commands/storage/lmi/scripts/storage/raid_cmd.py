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
MD RAID management.

Usage:
    %(cmd)s list
    %(cmd)s create [ --name=<name> ] <level> <devices>...
    %(cmd)s delete <devices>...
    %(cmd)s show [<devices>]...

Commands:
    list        List all MD RAID devices on the system.

    create      Create MD RAID array with given RAID level from list of devices.

    delete      Delete given MD RAID devices.

    show        Show detailed information about given MD RAID devices. If no
                devices are provided, all MD RAID devices are displayed.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import raid, show
from lmi.scripts.storage.common import str2device

def list(c):
    for r in raid.get_raids(c):
        members = raid.get_raid_members(c, r)
        yield (r.DeviceID, r.ElementName, r.Level, len(members))

def cmd_show(c, devices=None):
    if not devices:
        devices = raid.get_raids(c)
    for r in devices:
        show.raid_show(c, r)
        print ""
    return 0

def create(c, devices, level, __name=None):
    raid.create_raid(c, devices, level, __name)
    return 0

def delete(c, devices):
    for dev in devices:
        raid.delete_raid(c, dev)
    return 0

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.raid_cmd:list'
    COLUMNS = ('DeviceID', 'Name', "Level", "Nr. of members")

class Create(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.raid_cmd:create'
    EXPECT = 0

class Delete(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.raid_cmd:delete'
    EXPECT = 0

class Show(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.raid_cmd:cmd_show'
    EXPECT = 0

Raid = command.register_subcommands(
        'raid', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
