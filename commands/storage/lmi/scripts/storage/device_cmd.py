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

def list(ns, devices=None):
    devices = get_devices(ns, devices)
    for dev in devices:
        yield (dev.DeviceID,
                dev.Name,
                dev.ElementName,
                size2str(dev.NumberOfBlocks * dev.BlockSize),
                fs.get_device_format_label(ns, dev))

def cmd_show(ns, devices=None):
    if not devices:
        devices = get_devices(ns)
    for dev in devices:
        show.device_show(ns, dev)
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
