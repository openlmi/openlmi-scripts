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
LUKS management functions.
"""

from lmi.scripts.common import get_logger
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.storage import common, fs


LOG = get_logger(__name__)

def get_luks_list(ns):
    """
    Retrieve list of all encrypted devices.

    :rtype: list of LMIInstance/LMI_EncryptionFormat.
    """
    # No vgs supplied, list all LVs
    for fmt in ns.LMI_EncryptionFormat.instances():
        yield fmt

def create_luks(ns, device, passphrase):
    """
    Format given device with LUKS encryption format. All data on the device
    will be deleted! Encryption key and algorithm will be chosen automatically.

    :type device: LMIInstance/CIM_StorageExtent or string
    :param device: Device to format with LUKS data
    :type passphrase: string
    :param passphrase: Password to open the encrypted data. This is not the
            encryption key.
    :rtype: LMIInstance/LMI_EncryptionFormat
    """
    device = common.str2device(ns, device)
    service = ns.LMI_ExtentEncryptionConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCreateEncryptionFormat(
            InExtent=device,
            Passphrase=passphrase)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot create LUKS format: %s." % err)
        values = service.CreateEncryptionFormat.CreateEncryptionFormatValues
        raise LmiFailed("Cannot create LUKS format: %s."
                % (values.value_name(ret),))

    LOG().info("Created LUKS on %s", device.Name)
    return outparams['Format']


def open_luks(ns, fmt, name, passphrase):
    """
    Open encrypted LUKS format and expose it as a clear-text block device.

    :type fmt: LMIInstance/LMI_EncryptionFormat or string
    :param fmt: The LUKS format to open.
    :type name: string
    :param name: Requested name of the clear-text block device. It will be
            available as /dev/mapper/<name>.
    :type passphrase: string
    :param passphrase: Password to open the encrypted data.
    :rtype: LMIInstance/LMI_LUKSStorageExtent
    :returns: The block device with clear-text data.
    """
    fmt = fs.str2format(ns, fmt)
    service = ns.LMI_ExtentEncryptionConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncOpenEncryptionFormat(
            Format=fmt,
            ElementName=name,
            Passphrase=passphrase)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot open LUKS format: %s." % err)
        values = service.OpenEncryptionFormat.OpenEncryptionFormatValues
        raise LmiFailed("Cannot open LUKS format: %s."
                % (values.value_name(ret),))

    opened = outparams['Extent'].to_instance()
    LOG().info("Opened LUKS on %s as %s", fmt.ElementName, opened.Name)
    return opened

def close_luks(ns, fmt):
    """
    Closes clear-text block device previously opened by open_luks().

    :type fmt: LMIInstance/LMI_EncryptionFormat or string
    :param fmt: The LUKS format to close.
    """
    fmt = fs.str2format(ns, fmt)
    service = ns.LMI_ExtentEncryptionConfigurationService.first_instance()
    (ret, outparams, err) = service.SyncCloseEncryptionFormat(Format=fmt)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot close LUKS format: %s." % err)
        values = service.CloseEncryptionFormat.CloseEncryptionFormatValues
        raise LmiFailed("Cannot close LUKS format: %s."
                % (values.value_name(ret),))
    LOG().info("Closed LUKS on %s", fmt.ElementName)

def add_luks_passphrase(ns, fmt, passphrase, new_passphrase):
    """
    Adds new password to LUKS format. Each format can have up to 8 separate
    passwords and any of them can be used to open(decrypt) the format.

    Any existing passphrase must be provided to add a new one. This proves
    the caller is authorized to add new passphrase (because it already knows
    one) and also this 'old' passphrase is used to retrieve encryption keys.
    This 'old' passphrase is not removed nor replaced when adding new
    passphrase!

    :type fmt: LMIInstance/LMI_EncryptionFormat or string
    :param fmt: The LUKS format to modify.
    :type passphrase: string
    :param passphrase: Existing LUKS passphrase.
    :type new_passphrase: string
    :param new_passphrase: New passphrase to add to the format.
    """
    fmt = fs.str2format(ns, fmt)
    service = ns.LMI_ExtentEncryptionConfigurationService.first_instance()
    (ret, outparams, err) = service.AddPassphrase(
            Format=fmt,
            Passphrase=passphrase,
            NewPassphrase=new_passphrase)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot add new passphrase: %s." % err)
        values = service.AddPassphrase.AddPassphraseValues
        raise LmiFailed("Cannot add new passphrase: %s."
                % (values.value_name(ret),))
    LOG().info("Added passphrase to %s", fmt.ElementName)

def delete_luks_passphrase(ns, fmt, passphrase):
    """
    Delete passphrase from LUKS format.

    :type fmt: LMIInstance/LMI_EncryptionFormat or string
    :param fmt: The LUKS format to modify.
    :type passphrase: string
    :param passphrase: The passphrase to remove
    """
    fmt = fs.str2format(ns, fmt)
    service = ns.LMI_ExtentEncryptionConfigurationService.first_instance()
    (ret, outparams, err) = service.DeletePassphrase(
            Format=fmt,
            Passphrase=passphrase)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot delete passphrase: %s." % err)
        values = service.DeletePassphrase.DeletePassphraseValues
        raise LmiFailed("Cannot delete passphrase: %s."
                % (values.value_name(ret),))
    LOG().info("Deleted passphrase from %s", fmt.ElementName)

def get_luks_device(ns, fmt):
    """
    Return clear-text device for given LUKS format. The format must be already
    opened by open_luks().

    :type fmt: LMIInstance/LMI_EncryptionFormat or string
    :param fmt: The LUKS format to inspect.
    :rtype: LMIInstance/LMI_LUKSStorageExtent
    :returns: Block device with clear-text data or None, if the LUKS format is
            not open.
    """

    fmt = fs.str2format(ns, fmt)
    crypttext_device = fmt.first_associator(
                AssocClass="LMI_ResidesOnExtent",
                Role="Dependent")
    device = crypttext_device.first_associator(
                AssocClass="LMI_LUKSBasedOn",
                Role="Antecedent")
    return device

def get_passphrase_count(ns, fmt):
    """
    Each LUKS format can have up to 8 passphrases. Any of these passphrases can
    be used to decrypt the format and create clear-text device.

    This function returns number of passphrases in given LUKS format.

    :type fmt: LMIInstance/LMI_EncryptionFormat or string
    :param fmt: The LUKS format to inspect.
    :rtype: int
    :returns: Number of used passphrases.
    """

    fmt = fs.str2format(ns, fmt)
    count = reduce(lambda a, b: a + b, fmt.SlotStatus)
    return count
