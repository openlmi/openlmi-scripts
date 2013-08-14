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

def list(ns):
    for vg in lvm.get_vgs(ns):
        yield (vg.InstanceID,
                vg.ElementName,
                size2str(vg.ExtentSize),
                size2str(vg.RemainingManagedSpace))

def cmd_show(ns, vgs=None):
    if not vgs:
        vgs = lvm.get_vgs(ns)
    for vg in vgs:
        show.vg_show(ns, vg)
        print ""
    return 0

def create(ns, name, devices, __extent_size=None):
    if __extent_size:
        __extent_size = str2size(__extent_size)
    lvm.create_vg(ns, devices, name, __extent_size)
    return 0

def delete(ns, vgs):
    for vg in vgs:
        lvm.delete_vg(ns, vg)
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
