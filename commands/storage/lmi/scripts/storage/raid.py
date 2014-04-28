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
MD RAID management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common

def get_raids(ns):
    """
    Retrieve list of all MD RAIDs on the system.

    :rtype: list of LMIInstance/LMI_MDRAIDStorageExtent.
    """
    for raid in ns.LMI_MDRAIDStorageExtent.instances():
        yield raid

def create_raid(ns, devices, level, name=None):
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
    devs = [common.str2device(ns, device) for device in devices]
    args = { 'InExtents': devs,
            'Level': level}
    if name:
        args['ElementName'] = name
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCreateOrModifyMDRAID(**args)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot create the MD RAID: %s." % err)
        values = service.CreateOrModifyMDRAID.CreateOrModifyMDRAIDValues
        raise LmiFailed("Cannot create the MD RAID: %s."
                % (values.value_name(ret),))

    raid = outparams['TheElement'].to_instance()
    LOG().info("Created MD RAID %s", raid.Name)
    return raid


def delete_raid(ns, raid):
    """
    Destroy given RAID device

    :type raid: LMIInstance/LMI_MDRAIDStorageExtent
    :param raid: MD RAID to destroy.
    """
    raid = common.str2device(ns, raid)
    service = ns.LMI_StorageConfigurationService.first_instance()
    (ret, _outparams, err) = service.SyncDeleteMDRAID(TheElement=raid)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot delete the MD RAID: %s." % err)
        raise LmiFailed("Cannot delete the raid: %s."
                % (service.DeleteMDRAID.DeleteMDRAIDValues.value_name(ret),))
    LOG().info("Deleted MD RAID %s", raid.Name)

def get_raid_members(ns, raid):
    """
    Return member devices of the RAID.

    :type raid: LMIInstance/LMI_MDRAIDStorageExtent
    :param raid: MD RAID to examine.
    :rtype: List of LMIInstance/CIM_StorageExtent
    """
    raid = common.str2device(ns, raid)
    members = raid.associators(AssocClass="LMI_MDRAIDBasedOn",
            Role="Dependent")
    return members
