# Storage Management Providers
#
# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
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
LVM management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common

def get_lvs(ns, vgs=None):
    """
    Retrieve list of all logical volumes allocated from given volume groups.

    If no volume groups are provided, all logical volumes on the system
    are returned.

    :type vgs: list of LMIInstance/LMI_VGStoragePool or list of strings
    :param vgs: Volume Groups to examine.
    :rtype: list of LMIInstance/LMI_LVStorageExtent.
    """
    if vgs:
        for vg in vgs:
            vg = common.str2vg(ns, vg)
            LOG().debug("Getting LVs on %s", vg.ElementName)
            for lv in get_vg_lvs(ns, vg):
                yield lv
    else:
        # No vgs supplied, list all LVs
        for lv in ns.LMI_LVStorageExtent.instances():
            # XXX workaround for https://fedorahosted.org/openlmi/ticket/277
            supports_thin = 'ThinlyProvisioned' in lv.properties()
            if not supports_thin:
                yield lv
            elif supports_thin and not lv.ThinlyProvisioned:
                yield lv

def get_tlvs(ns, tps=None):
    if tps:
        for tp in tps:
            tp = common.str2vg(ns, tp)
            for tlv in get_vg_lvs(ns, tp):
                yield tlv
    else:
        for tlv in ns.LMI_LVStorageExtent.instances():
            if tlv.ThinlyProvisioned:
                yield tlv

def create_lv(ns, vg, name, size):
    """
    Create new Logical Volume on given Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to allocate the volume from.
    :type name: string
    :param name: Name of the logical volume.
    :type size: int
    :param size: Size of the logical volume in bytes.
    :rtype: LMIInstance/LMI_LVStorageExtent
    """
    vg = common.str2vg(ns, vg)
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCreateOrModifyLV(
            ElementName=name,
            Size=size,
            InPool=vg)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot create the logical volume: %s." % err)
        values = service.CreateOrModifyLV.CreateOrModifyLVValues
        raise LmiFailed("Cannot create the logical volume: %s."
                % (values.value_name(ret),))

    lv = outparams['TheElement'].to_instance()
    LOG().info("Created logical volume %s", lv.Name)
    return lv

def create_tlv(ns, tp, name, size):
    tp = common.str2vg(ns, tp)
    args = {'ElementName':name,
            'ThinPool':tp,
            'Size':size}
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCreateOrModifyThinLV(**args)
    if ret != 0:
        raise LmiFailed("Cannot create thin LV: %s." % (err if err else ret))

    tlv = outparams['TheElement'].to_instance()
    LOG().info("Created thin logical volume %s", tlv.Name)
    return tlv

def delete_lv(ns, lv):
    """
    Destroy given Logical Volume.

    :type lv: LMIInstance/LMI_LVStorageExtent or string
    :param lv: Logical Volume to destroy.
    """
    lv = common.str2device(ns, lv)
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, _outparams, err) = service.SyncDeleteLV(TheElement=lv)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot delete the LV: %s." % err)
        raise LmiFailed("Cannot delete the LV: %s."
                % (service.DeleteLV.DeleteLVValues.value_name(ret),))

    LOG().info("Deleted logical volume %s", lv.Name)

def get_vgs(ns):
    """
    Retrieve list of all volume groups on the system.

    :rtype: list of LMIInstance/LMI_VGStoragePool
    """
    LOG().debug("get_vgs: Loading list of all volume groups.")
    for vg in ns.LMI_VGStoragePool.instances():
        if vg.SpaceLimitDetermination:
            # skip thin pools
            continue
        yield vg

def create_vg(ns, devices, name, extent_size=None):
    """
    Create new Volume Group from given devices.

    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param device: Devices to add to the Volume Group.
    :type name: string
    :param name: Name of the Volume gGoup.
    :type extent_size: int
    :param extent_size: Extent size in bytes.
    :rtype: LMIInstance/LMI_VGStoragePool
    """
    devs = [common.str2device(ns, device) for device in devices]
    args = { 'InExtents': devs,
            'ElementName': name}
    goal = None

    try:
        if extent_size:
            # create (and use) VGStorageSetting
            caps = ns.LMI_VGStorageCapabilities.first_instance()
            (ret, outparams, err) = caps.CreateVGStorageSetting(
                    InExtents=devs)
            if ret != 0:
                if err:
                    raise LmiFailed("Cannot create setting for the volume " \
                            "group: %s." % err)
                vals = caps.CreateVGStorageSetting.CreateVGStorageSettingValues
                raise LmiFailed("Cannot create setting for the volume group:" \
                        " %s." % (vals.value_name(ret),))
            goal = outparams['Setting']
            goal = goal.to_instance()
            goal.ExtentSize = extent_size
            (ret, outparams, err) = goal.push()
            if ret != 0:
                if err:
                    raise LmiFailed("Cannot modify setting for the volume " \
                            "group: %s." % err)
                raise LmiFailed("Cannot modify setting for the volume group:" \
                        " %d." % ret)
            args['Goal'] = goal

        service = ns.LMI_StorageConfigurationService.first_instance()
        (ret, outparams, err) = service.SyncCreateOrModifyVG(**args)
        if ret != 0:
            if err:
                raise LmiFailed("Cannot create the volume group: %s." % err)
            values = service.CreateOrModifyVG.CreateOrModifyVGValues
            raise LmiFailed("Cannot create the volume group: %s."
                    % (values.value_name(ret),))
    finally:
        if goal:
            goal.delete()

    pool = outparams['Pool'].to_instance()
    LOG().info("Created volume group %s", pool.Name)
    return pool

def create_tp(ns, name, vg, size):
    vg = common.str2vg(ns, vg)
    args = {'InPool':vg,
            'ElementName':name,
            'Size':size}
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCreateOrModifyThinPool(**args)
    if ret != 0:
        raise LmiFailed("Cannot create thin pool: %s." % (err if err else ret))

    pool = outparams['Pool'].to_instance()
    LOG().info("Created thin volume group %s", pool.Name)
    return pool

def modify_vg(ns, vg, add_pvs=None, remove_pvs=None):
    """
    Modify given Volume Group.

    Add 'add_pvs' devices as Physical Volumes of the group.
    Remove 'remove_pvs' devices from the Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to delete.
    :type add_pvs: List of LMIInstances/LMI_VGStoragePools or strings
    :param add_pvs: List of new devices to be added as Physical Volumes of the
                    VG.
    :type remove_pvs: List of LMIInstances/LMI_VGStoragePools or strings
    :param remove_pvs: List of Physical Volume to be removed from the VG.
    """
    vg = common.str2vg(ns, vg)
    service = ns.LMI_StorageConfigurationService.first_instance()

    # get list of current PVs
    pvs = get_vg_pvs(ns, vg)

    for device in add_pvs:
        device = common.str2device(ns, device)
        if device not in pvs:
            pvs.append(device)

    for device in remove_pvs:
        device = common.str2device(ns, device)
        # don't report error when removing device that is not a PV
        if device in pvs:
            pvs.remove(device)

    (ret, _outparams, err) = service.SyncCreateOrModifyVG(Pool=vg, InExtents = list(pvs))
    if ret != 0:
        if err:
            raise LmiFailed("Cannot modify the VG: %s." % err)
        raise LmiFailed("Cannot modify the VG: %s."
                % (service.CreateOrModifyVG.CreateOrModifyVG.value_name(ret),))
    LOG().info("Modified volume group %s", vg.Name)

def delete_vg(ns, vg):
    """
    Destroy given Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to delete.
    """
    vg = common.str2vg(ns, vg)
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, _outparams, err) = service.SyncDeleteVG(Pool=vg)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot delete the VG: %s." % err)
        raise LmiFailed("Cannot delete the VG: %s."
                % (service.DeleteVG.DeleteVGValues.value_name(ret),))
    LOG().info("Deleted volume group %s", vg.Name)

def get_vg_lvs(ns, vg):
    """
    Return list of Logical Volumes on given Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to examine.
    :rtype: list of LMIInstance/LMI_LVStorageExtent
    """
    vg = common.str2vg(ns, vg)
    return vg.associators(AssocClass="LMI_LVAllocatedFromStoragePool")

def get_lv_vg(ns, lv):
    """
    Return Volume Group of given Logical Volume.

    :type lv: LMIInstance/LMI_LVStorageExtent or string
    :param lv: Logical Volume to examine.
    :rtype: LMIInstance/LMI_VGStoragePool
    """
    lv = common.str2device(ns, lv)
    return lv.first_associator(AssocClass="LMI_LVAllocatedFromStoragePool")

def get_vg_pvs(ns, vg):
    """
    Return Physical Volumes of given Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to examine.
    :rtype: list of LMIInstance/CIM_StorageExtent
    """
    vg = common.str2vg(ns, vg)
    return vg.associators(AssocClass="LMI_VGAssociatedComponentExtent")

def get_vg_tps(ns, vg):
    """
    Return Thin Pools of given Volume Group.

    :type vg: LMIInstance/LMI_VGStoragePool or string
    :param vg: Volume Group to examine.
    :rtype: list of LMIInstance/CIM_StoragePool
    """
    # XXX workaround for https://fedorahosted.org/openlmi/ticket/276
    assoc_class = "LMI_VGAllocatedFromStoragePool"
    if not assoc_class in ns.classes():
        return []

    vg = common.str2vg(ns, vg)
    return vg.associators(AssocClass=assoc_class)

def get_tps(ns):
    """
    Retrieve list of all thin pools on the system.

    :rtype: list of LMIInstance/LMI_VGStoragePool
    """
    if "LMI_VGAllocatedFromStoragePool" in ns.classes():
        LOG().debug("get_tps: Loading list of all thin pools.")
        for vg in ns.LMI_VGStoragePool.instances():
            if vg.SpaceLimitDetermination:
                yield vg

def get_tp_vgs(ns, tp):
    """
    Return Volume Groups of given Thin Pool.

    Alias for get_vg_tps.
    """
    return get_vg_tps(ns, tp)
