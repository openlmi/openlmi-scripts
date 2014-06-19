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
Volume Group management.

Usage:
    %(cmd)s list
    %(cmd)s create [ --extent-size=<size> ] <name> <device> ...
    %(cmd)s delete <vg> ...
    %(cmd)s show [ <vg> ...]
    %(cmd)s modify <vg> [ --add=<device> ] ... [ --remove=<device> ] ...

Commands:
    list        List all volume groups on the system.

    create      Create Volume Group with given name from list of devices.

    delete      Delete given Volume Groups.

    show        Show detailed information about given Volume Groups. If no
                Volume Groups are provided, all of them are displayed.

    modify      Add or remove Physical Volumes to/from given Volume Group.
                This command requires OpenLMI-Storage 0.8 or newer.

Options:

    device      Identifier of the device. Either one of:

                * DeviceID of appropriate CIM_StorageExtent object. This is
                  internal OpenLMI ID of the device and it should be stable
                  across system reboots.

                * Device name directly in /dev directory, such as '/dev/sda'.
                  This device name is available as Name property of
                  CIM_StorageExtent object.

                * Name of MD RAID or logical volume. This method cannot be used
                  when the name is not unique, for example when there are two
                  logical volumes with the same name, allocated from different
                  volume groups. This name is available as ElementName
                  property of CIM_StorageExtent object.

    vg          Name of the volume group, with or without `/dev/` prefix.

    size        Requested extent size of the new volume group, by default in
                bytes. 'T', 'G', 'M' or 'K' suffix can be used to specify
                other units (TiB, GiB, MiB and KiB) - '1K' specifies 1 KiB
                (=1024 bytes).
                The suffix is case insensitive, i.e. 1g = 1G = 1073741824 bytes.

    -a <device> , --add=<device>        Device to add to a Volume Group.

    -r <device> , --remove=<device>     Device to remove from a Volume Group.

"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs, lvm, mount, raid, partition
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device, str2size, str2vg)

LOG = get_logger(__name__)

class VGList(command.LmiLister):
    COLUMNS = ('ElementName', "ExtentSize", "Total space", "Free space")

    def execute(self, ns):
        """
        Implementation of 'vg list' command.
        """
        for vg in lvm.get_vgs(ns):
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


class VGCreate(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, name, devices, _extent_size=None):
        """
        Implementation of 'vg create' command.
        """
        if _extent_size:
            _extent_size = str2size(_extent_size)
        lvm.create_vg(ns, devices, name, _extent_size)

class VGModify(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'vg' option to 'vgs' parameter name for better
        readability.
        """
        options['<vgs>'] = options.pop('<vg>')

    def execute(self, ns, vgs, _add, _remove):
        """
        Implementation of 'vg modify' command.
        """
        if len(vgs) != 1:
            raise LmiFailed("One vgolume group must be specified.")
        lvm.modify_vg(ns, vgs[0], add_pvs=_add, remove_pvs=_remove)

class VGModifyNotSupported(VGModify):
    def execute(self, ns, vgs, _add, _remove):
        raise errors.LmiFailed("OpenLMI-Storage 0.8 is required on the remote machine")

class VGDelete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'vg' option to 'vgs' parameter name for better
        readability.
        """
        options['<vgs>'] = options.pop('<vg>')

    def execute(self, ns, vgs):
        """
        Implementation of 'vg delete' command.
        """
        for vg in vgs:
            lvm.delete_vg(ns, vg)


class VGShow(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'vg' option to 'vgs' parameter name for better
        readability.
        """
        options['<vgs>'] = options.pop('<vg>')

    def execute(self, ns, vgs=None):
        """
        Implementation of 'vg show' command.
        """
        if not vgs:
            vgs = lvm.get_vgs(ns)
        for vg in vgs:
            vg = str2vg(ns, vg)
            cmd = fcmd.NewTableCommand(title=vg.InstanceID)
            yield cmd
            for line in show.vg_show(ns, vg, self.app.config.human_friendly):
                yield line

class VG07(command.LmiCommandMultiplexer):
    # VG subscommand for OpenLMI-Storage 0.7.x and older
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : VGList,
            'create'  : VGCreate,
            'delete'  : VGDelete,
            'show'    : VGShow,
            'modify'  : VGModifyNotSupported,
    }

class VG08(command.LmiCommandMultiplexer):
    # VG subscommand for OpenLMI-Storage 0.8.0 and newer
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : VGList,
            'create'  : VGCreate,
            'delete'  : VGDelete,
            'show'    : VGShow,
            'modify'  : VGModify,
    }

class VG(command.LmiSelectCommand):
    """ Select correct multiplexer for remote openlmi-storage version. """
    SELECT = [
            ( 'OpenLMI-Storage >= 0.8.0', VG08),
            ( 'OpenLMI-Storage', VG07)
    ]
