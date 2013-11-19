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
    %(cmd)s list [ <vg> ...]
    %(cmd)s create <vg> <name> <size>
    %(cmd)s delete <lv> ...
    %(cmd)s show [ <lv> ...]

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
from lmi.scripts.storage.common import str2size, size2str, str2device, str2vg
from lmi.scripts.common import formatter
from lmi.scripts.common.formatter import command as fcmd

class Lister(command.LmiLister):
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size")

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
            yield (lv.DeviceID,
                    lv.Name,
                    lv.ElementName,
                    size)


class Create(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, vg, name, size):
        """
        Implementation of 'lv create' command.
        """
        vg = str2vg(ns, vg[0])
        lvm.create_lv(ns, vg, name, str2size(size, vg.ExtentSize, 'E'))


class Delete(command.LmiCheckResult):
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


class Show(command.LmiLister):
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


Lv = command.register_subcommands(
        'Lv', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
