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
Basic device information.

Usage:
    %(cmd)s list [<devices>]...
    %(cmd)s show [<devices>]...

Commands:
    list        List short information about given device. If no devices
                are given, all devices are listed.

    show        Show detailed information about given devices. If no devices
                are provided, all of them are displayed.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import show, fs
from lmi.scripts.storage.common import str2device, size2str, get_devices

def list(c, devices=None):
    devices = get_devices(c, devices)
    for dev in devices:
        yield (dev.DeviceID,
                dev.Name,
                dev.ElementName,
                size2str(dev.NumberOfBlocks * dev.BlockSize),
                fs.get_device_format_label(c, dev))

def cmd_show(c, devices=None):
    if not devices:
        devices = get_devices(c)
    for dev in devices:
        show.device_show(c, dev)
        print ""
    return 0

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.storage.device_cmd:list'
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size", "Format")

class Show(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.device_cmd:cmd_show'
    EXPECT = 0

Device = command.register_subcommands(
        'device', __doc__,
        { 'list'    : Lister ,
          'show'    : Show,
        },
    )
