# coding=utf-8
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
Basic storage device information.

Usage:
    %(cmd)s list [ <device> ...]
    %(cmd)s depends [ --deep ] [ <device> ...]
    %(cmd)s provides [ --deep ] [ <device> ...]
    %(cmd)s show [ <device> ...]
    %(cmd)s tree [ <device> ]

Commands:
    list        List short information about given device. If no devices
                are given, all devices are listed.

    show        Show detailed information about given devices. If no devices
                are provided, all of them are displayed.

    provides    Show devices, which are created from given devices
                (= show children of the devices).

                For example, if disk is provided, all partitions on it are
                returned. If 'deep' is used, all RAIDs, Volume Groups and
                Logical Volumes indirectly allocated from it are returned too.

    depends     Show devices, which are required by given devices to operate
                correctly (= show parents of the devices).

                For example, if a Logical Volume is provided, its Volume Group
                is returned. If 'deep' is used, also all Physical Volumes and
                disk are returned.

    tree        Show tree of devices, similar to lsblk.
                (Note that the output is really crude and needs to be worked
                on).

                If no device is provided, all devices are shown, starting
                with physical disks.

                If a device is provided, tree starts with the device
                and all dependent devices are shown.
"""

from lmi.shell.LMIUtil import lmi_isinstance
from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.storage import show, fs
from lmi.scripts.storage.common import (size2str, get_devices, get_children,
        get_parents, str2device)
from lmi.scripts.storage.lvm import get_vgs
LOG = get_logger(__name__)

def get_device_info(ns, device, human_friendly):
    """
    Return detailed information of the device to show.
    """
    if device.NumberOfBlocks and device.BlockSize:
        size = size2str(device.NumberOfBlocks * device.BlockSize, human_friendly)
    else:
        size = 'N/A'

    fslabel = fs.get_device_format_label(ns, device)
    return (device.DeviceID,
            device.Name,
            device.ElementName,
            size,
            fslabel)

def get_pool_info(_ns, pool, human_friendly):
    """
    Return detailed information of the Volume Group to show.
    """
    size = size2str(pool.TotalManagedSpace, human_friendly)
    return (pool.InstanceID,
            pool.ElementName,
            pool.ElementName,
            size,
            "volume group (LVM)")

def get_obj_info(ns, obj, human_friendly):
    """
    Return detailed information of the device or VG to show.
    """
    if lmi_isinstance(obj, ns.CIM_StorageExtent):
        return get_device_info(ns, obj, human_friendly)
    else:
        return get_pool_info(ns, obj, human_friendly)


class Lister(command.LmiLister):
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size", "Format")

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'device list' command.
        """
        devices = get_devices(ns, devices)
        for dev in devices:
            yield get_device_info(ns, dev, self.app.config.human_friendly)

    def execute(self, ns, devices=None):
        """
        Implementation of 'device list' command.
        """
        devices = get_devices(ns, devices)
        for dev in devices:
            yield get_device_info(ns, dev, self.app.config.human_friendly)


class Show(command.LmiLister):
    COLUMNS = ('Name', 'Value')
    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'device show' command.
        """
        if not devices:
            devices = get_devices(ns)
        for dev in devices:
            dev = str2device(ns, dev)
            cmd = fcmd.NewTableCommand(title=dev.DeviceID)
            yield cmd
            for line in show.device_show(ns, dev,
                    self.app.config.human_friendly):
                yield line



class Depends(command.LmiLister):
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size", "Format")

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None, _deep=None):
        """
        Implementation of 'device depends' command.
        """
        for device in devices:
            yield fcmd.NewTableCommand(title=device)
            for parent in  get_parents(ns, device, _deep):
                yield get_obj_info(ns, parent, self.app.config.human_friendly)


class Provides(command.LmiLister):
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size", "Format")

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None, _deep=None):
        """
        Implementation of 'device provides' command.
        """
        for device in devices:
            yield fcmd.NewTableCommand(title=device)
            for child in  get_children(ns, device, _deep):
                yield get_obj_info(ns, child, self.app.config.human_friendly)


class Tree(command.LmiLister):
    COLUMNS = ('DeviceID', "Name", "ElementName", "Size", "Format")

    def prepare_tree_line(self, level, name, subsequent):
        """
        Draw one line of device tree into string and return it.
        """
        if level == 0:
            return u'' + name

        line = [ u" " for i in xrange((level) * 2) ]
        # Prepare '|' where appropriate
        for (devid, l) in subsequent:
            if l > 0:
                line[(l - 1) * 2] = u"│"

        l = level - 1
        # add "├"
        if line[l * 2] == u"│":
            line[l * 2] = u"├"
        else:
            line[l * 2] = u"└"
        # add "-"
        line[l * 2 + 1] = u"─"

        return u''.join(line) + name

    def execute(self, ns, device=None):
        """
        Implementation of 'device tree' command.
        """
        # Note, this is high-speed version of the device tree.
        # Walking through associations using get_children() functions
        # was kind of slow, even for small number of devices (~5).

        # devices = dict devid -> LMIInstance
        devices = {}
        # Load *all* CIM_StorageExtents to speed things up.
        for dev in get_devices(ns):
            devices[self.get_obj_id(ns, dev)] = dev
        # Add *all* LMI_VGStoragePools.
        for vg in get_vgs(ns):
            devices[self.get_obj_id(ns, vg)] = vg

        # deps = array of tuples (parent devid, child devid)
        # Load all dependencies, calling get_children iteratively is slow
        # Add CIM_BasedOn dependencies (and omit LMI_LVBasedOn, we need
        # LMI_LVAllocatedFromStoragePool instead)
        LOG().debug("Loading list of CIM_BasedOn associations.")
        deps = [(self.get_obj_id(ns, i.Antecedent),
                 self.get_obj_id(ns, i.Dependent))
                        for i in ns.CIM_BasedOn.instances()
                            if not lmi_isinstance(i, ns.LMI_LVBasedOn)]

        # Be careful with logical partitions - they are BasedOn on appropriate
        # extended partition, but we want to draw them as children of
        # appropriate disk.
        LOG().debug("Reworking BasedOn associations for logical partitions.")
        logical = ns.LMI_DiskPartition.PartitionTypeValues.Logical
        extended = ns.LMI_DiskPartition.PartitionTypeValues.Extended
        for i in xrange(len(deps)):
            dev = devices[deps[i][0]]
            child = devices[deps[i][1]]
            LOG().debug("Inspecting %s - %s" % deps[i])
            if ("PartitionType" in dev.properties()
                    and "PartitionType" in child.properties()
                    and dev.PartitionType == extended
                    and child.PartitionType == logical):
                # We found ext. partition - logical partition dependency
                # Find the disk
                disk_id = None
                for (d, c) in deps:
                    if c == deps[i][0]:
                        disk_id = d
                # Replace the extended->logical dependency with disk->logical
                deps[i] = (disk_id, deps[i][1])
                LOG().debug("--- Replaced with %s - %s" % deps[i])

        # Add VG-LV dependencies from LMI_LVAllocatedFromStoragePool association
        LOG().debug("Loading LVAllocatedFromStoragePool associations.")
        deps += [(self.get_obj_id(ns, i.Antecedent),
                  self.get_obj_id(ns, i.Dependent))
                        for i in ns.LMI_LVAllocatedFromStoragePool.instances()]

        # Add PV-VG dependencies from LMI_VGAssociatedComponentExtent
        LOG().debug("Loading VGAssociatedComponentExtent associations.")
        deps += [
                (self.get_obj_id(ns, i.PartComponent),
                 self.get_obj_id(ns, i.GroupComponent))
                        for i in ns.LMI_VGAssociatedComponentExtent.instances()]

        # queue = array of tuples (devid, level), queue of items to inspect
        # and display
        queue = []
        if device:
            device = str2device(ns, device[0])
            queue = [(self.get_obj_id(ns, device), 0), ]
        else:
            for (devid, device) in devices.iteritems():
                if device.Primordial:
                    queue.append((devid, 0))
        shown = set()

        while queue:
            (devid, level) = queue.pop()

            device = devices[devid]
            info = get_obj_info(ns, device, self.app.config.human_friendly)
            if devid in shown:
                # If the device was already displayed, just show reference to it
                yield (self.prepare_tree_line(level, info[0], queue), "***")
                # Don't show children of already displayed elements
                continue

            # Display the device
            yield (self.prepare_tree_line(level, info[0], queue),) + info[1:]
            shown.add(devid)
            # And inspect all children
            children = [ dep[1] for dep in deps if dep[0] == devid ]
            for child in reversed(children):
                queue.append((child, level + 1))

    def get_obj_id(self, ns, obj):
        """
        Return unique ID of a device or a Volume group.
        """
        if lmi_isinstance(obj, ns.CIM_StorageExtent):
            return obj.DeviceID
        else:
            return obj.InstanceID


Storage = command.register_subcommands(
        'storage', __doc__,
        { 'list'    : Lister,
          'show'    : Show,
          'tree'    : Tree,
          'provides': Provides,
          'depends' : Depends,
        },
    )
