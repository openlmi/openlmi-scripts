# Software Management Providers
#
# Copyright (C) 2012-2013 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
MD RAID management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common
import pywbem

def get_raids(c):
    """
    Retrieve list of all MD RAIDs on the system.

    :rtype: list of LMIInstance/LMI_MDRAIDStorageExtent.
    """
    for raid in c.root.cimv2.LMI_MDRAIDStorageExtent.instances():
        yield raid

def create_raid(c, devices, level, name=None):
    """
    Create new MD RAID device.

    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param device: Devices to add to the RAID.
    :type level: int
    :param level: RAID level.
    :type name: string
    :param name: RAID name.
    :rtype: LMIInstance/LMI_MDRAIDStorageExtent
    """
    devs = [common.str2device(c, device) for device in devices]
    args = { 'InExtents': devs,
            'Level': level}
    if name:
        args['ElementName'] = name
    service = c.root.cimv2.LMI_StorageConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCreateOrModifyMDRAID(**args)
    if ret != 0:
        raise LmiFailed("Cannot create the partition: %s."
                % (service.CreateOrModifyMDRAID.CreateOrModifyMDRAIDValues.value_name(ret),))
    return outparams['TheElement']


def delete_raid(c, raid):
    """
    Destroy given RAID device

    :type raid: LMIInstance/LMI_MDRAIDStorageExtent
    :param raid: MD RAID to destroy.
    """
    raid = common.str2device(c, raid)
    service = c.root.cimv2.LMI_StorageConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncDeleteMDRAID(TheElement=raid)
    if ret != 0:
        raise LmiFailed("Cannot delete the raid: %s."
                % (service.DeleteMDRAID.DeleteMDRAIDValues.value_name(ret),))

def get_raid_members(c, raid):
    """
    Return member devices of the RAID.

    :type raid: LMIInstance/LMI_MDRAIDStorageExtent
    :param raid: MD RAID to examine.
    :rtype: List of LMIInstance/CIM_StorageExtent
    """
    raid = common.str2device(c, raid)
    members = raid.associators(AssocClass="LMI_MDRAIDBasedOn",
            Role="Dependent")
    return members
