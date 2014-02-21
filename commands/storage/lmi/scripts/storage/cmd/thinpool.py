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
# Authors: Jan Synacek  <jsynacek@redhat.com>
#
"""
Thin Pool management.

Usage:
    %(cmd)s list
    %(cmd)s create <name> <vg> <size>
    %(cmd)s delete <tp> ...
    %(cmd)s show [ <tp> ...]

Commands:
    list        List all thin pools on the system.

    create      Create Thin Pool with given name and size from a Volume Group.

    delete      Delete given Thin Pools.

    show        Show detailed information about given Thin Pools. If no
                Thin Pools are provided, all of them are displayed.

Options:
    vg          Name of the volume group, with or without `/dev/` prefix.

    tp          Name of the thin pool, with or without `/dev/` prefix.

    size        Requested extent size of the new volume group, by default in
                bytes. 'T', 'G', 'M' or 'K' suffix can be used to specify
                other units (TiB, GiB, MiB and KiB) - '1K' specifies 1 KiB
                (=1024 bytes).
                The suffix is case insensitive, i.e. 1g = 1G = 1073741824 bytes.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, lvm
from lmi.scripts.storage.common import size2str, str2size, str2vg

class ThinPoolList(command.LmiLister):
    COLUMNS = ('ElementName', "ExtentSize", "Total space", "Free space")

    def execute(self, ns):
        """
        Implementation of 'thinpool list' command.
        """
        for vg in lvm.get_tps(ns):
            extent_size = size2str(vg.ExtentSize,
                    self.app.config.human_friendly)
            total_space = size2str(vg.TotalManagedSpace,
                    self.app.config.human_friendly)
            remaining_space = size2str(vg.RemainingManagedSpace,
                    self.app.config.human_friendly)
            yield (vg.ElementName,
                    extent_size,
                    total_space,
                    remaining_space)


class ThinPoolCreate(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, name, vg, size):
        """
        Implementation of 'thinpool create' command.
        """
        lvm.create_tp(ns, name, vg, str2size(size))

class ThinPoolDelete(command.LmiCheckResult):
    EXPECT = None
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, tps):
        """
        Implementation of 'thinpool delete' command.
        """
        for tp in tps:
            lvm.delete_vg(ns, tp)


class ThinPoolShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, tps=None):
        """
        Implementation of 'thinpool show' command.
        """
        if not tps:
            tps = lvm.get_tps(ns)
        for tp in tps:
            tp = str2vg(ns, tp)
            cmd = fcmd.NewTableCommand(title=tp.InstanceID)
            yield cmd
            for line in show.tp_show(ns, tp, self.app.config.human_friendly):
                yield line

class ThinPool(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : ThinPoolList,
            'create'  : ThinPoolCreate,
            'delete'  : ThinPoolDelete,
            'show'    : ThinPoolShow,
    }


