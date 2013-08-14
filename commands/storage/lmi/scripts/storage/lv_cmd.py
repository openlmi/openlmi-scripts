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
Logical Volume management.

Usage:
    %(cmd)s list [<vgs>]...
    %(cmd)s create <vg> <name> <size>
    %(cmd)s delete <lvs>...
    %(cmd)s show [<lvs>]...

Commands:
    list        List available logical volumes on given volume groups.
                If no volume groups are provided, all logical volumes are
                listed.

    create      Create a logical volume on given volume group.

                Size can be specified as number of extents using 'e' suffix,
                e.g. '100e' is 100 extents.

    delete      Delete given logical volume.

    show        Show detailed information about given Logical Volumes. If no
                Logical Volumes are provided, all of them are displayed.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import lvm, show
from lmi.scripts.storage.common import str2size, str2device, size2str

def list(c, vgs=None):
    for lv in lvm.get_lvs(c, vgs):
        yield (lv.DeviceID,
                lv.Name,
                lv.ElementName,
                size2str(lv.NumberOfBlocks * lv.BlockSize))

def cmd_show(c, lvs=None):
    if not lvs:
        lvs = lvm.get_lvs(c)
    for lv in lvs:
        show.lv_show(c, lv)
        print ""
    return 0

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

class Show(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.storage.lv_cmd:cmd_show'
    EXPECT = 0

Lv = command.register_subcommands(
        'Lv', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
