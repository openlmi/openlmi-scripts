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
# Authors: Jan Synacek  <jsynacek@redhat.com>
#
"""
Thin Logical Volume management.

Usage:
    %(cmd)s list [ <tp> ...]
    %(cmd)s create <tp> <name> <size>
    %(cmd)s delete <tlv> ...
    %(cmd)s show [ <tlv> ...]

Commands:
    list        List available thin logical volumes on given thin pools.
                If no thin pools are provided, all thin logical volumes are
                listed.

    create      Create a thin logical volume on given thin pool.

    delete      Delete given thin logical volume.

    show        Show detailed information about given Thin Logical Volumes. If no
                Thin Logical Volumes are provided, all of them are displayed.

Options:
    tp          Name of the thin pool, with or without `/dev/` prefix.

    size        Size of the new logical volume, by default in bytes.
                'T', 'G', 'M' or 'K' suffix can be used to specify other
                units (TiB, GiB, MiB and KiB) - '1K' specifies 1 KiB
                (= 1024 bytes).
                The suffix is case insensitive, i.e. 1g = 1G = 1073741824
                bytes.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, lvm
from lmi.scripts.storage.common import size2str, str2device, str2size, str2vg

class ThinLVList(command.LmiLister):
    COLUMNS = ("Name", "Thin Pool", "Size")
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, tps=None):
        """
        Implementation of 'thinlv list' command.
        """
        for tlv in lvm.get_tlvs(ns, tps):
            size = size2str(tlv.NumberOfBlocks * tlv.BlockSize,
                    self.app.config.human_friendly)
            tp = lvm.get_lv_vg(ns, tlv)
            yield (tlv.ElementName, tp.ElementName, size)


class ThinLVCreate(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, tp, name, size):
        """
        Implementation of 'thinlv create' command.
        """
        tp = str2vg(ns, tp[0])
        lvm.create_tlv(ns, tp, name, str2size(size))

class ThinLVDelete(command.LmiCheckResult):
    EXPECT = None
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, tlvs):
        """
        Implementation of 'thinlv delete' command.
        """
        for tlv in tlvs:
            lvm.delete_lv(ns, tlv)


class ThinLVShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')
    ARG_ARRAY_SUFFIX = 's'

    def execute(self, ns, tlvs=None):
        """
        Implementation of 'thinlv show' command.
        """
        if not tlvs:
            tlvs = lvm.get_tlvs(ns)

        for tlv in tlvs:
            tlv = str2device(ns, tlv)
            cmd = fcmd.NewTableCommand(title=tlv.DeviceID)
            yield cmd
            for line in show.tlv_show(ns, tlv, self.app.config.human_friendly):
                yield line

class ThinLV(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : ThinLVList,
            'create'  : ThinLVCreate,
            'delete'  : ThinLVDelete,
            'show'    : ThinLVShow,
    }

