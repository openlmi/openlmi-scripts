# coding=utf-8
# Storage Management Providers
#
# Copyright (C) 2014 Red Hat, Inc. All rights reserved.
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
    %(cmd)s list [ <vg> ...]
    %(cmd)s create <vg> <name> <size>
    %(cmd)s delete <lv> ...
    %(cmd)s show [ <lv> ...]

Commands:
    list        List available logical volumes on given volume groups.
                If no volume groups are provided, all logical volumes are
                listed.

    create      Create a logical volume on given volume group.

    delete      Delete given logical volume.

    show        Show detailed information about given Logical Volumes. If no
                Logical Volumes are provided, all of them are displayed.

Options:
    vg          Name of the volume group, with or without `/dev/` prefix.

    size        Size of the new logical volume, by default in bytes.
                'T', 'G', 'M' or 'K' suffix can be used to specify other
                units (TiB, GiB, MiB and KiB) - '1K' specifies 1 KiB
                (= 1024 bytes).
                The suffix is case insensitive, i.e. 1g = 1G = 1073741824
                bytes.

                'E' suffix can be used to specify number of volume group
                extents, '100e' means 100 extents.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)

LOG = get_logger(__name__)

class LVList(command.LmiLister):
    COLUMNS = ("Name", "Size")

    def transform_options(self, options):
        """
        Rename 'vg' option to 'vgs' parameter name for better
        readability.
        """
        options['<vgs>'] = options.pop('<vg>')

    def execute(self, ns, vgs=None):
        """
        Implementation of 'lv list' command.
        """
        for lv in lvm.get_lvs(ns, vgs):
            size = size2str(lv.NumberOfBlocks * lv.BlockSize,
                    self.app.config.human_friendly)
            yield (lv.Name, size)


class LVCreate(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, vg, name, size):
        """
        Implementation of 'lv create' command.
        """
        vg = str2vg(ns, vg[0])
        lvm.create_lv(ns, vg, name, str2size(size, vg.ExtentSize, 'E'))


class LVDelete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'lv' option to 'lvs' parameter name for better
        readability.
        """
        options['<lvs>'] = options.pop('<lv>')

    def execute(self, ns, lvs):
        """
        Implementation of 'lv delete' command.
        """
        for lv in lvs:
            lvm.delete_lv(ns, lv)


class LVShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'lv' option to 'lvs' parameter name for better
        readability.
        """
        options['<lvs>'] = options.pop('<lv>')

    def execute(self, ns, lvs=None):
        """
        Implementation of 'lv show' command.
        """
        if not lvs:
            lvs = lvm.get_lvs(ns)
        for lv in lvs:
            lv = str2device(ns, lv)
            cmd = fcmd.NewTableCommand(title=lv.DeviceID)
            yield cmd
            for line in show.lv_show(ns, lv, self.app.config.human_friendly):
                yield line

class LV(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : LVList,
            'create'  : LVCreate,
            'delete'  : LVDelete,
            'show'    : LVShow,
    }

