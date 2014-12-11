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
# Authors: Radek Novacek <rnovacek@redhat.com>
#
"""
LMI networking provider client library.
"""
import time

from lmi.scripts.common.errors import LmiFailed, LmiInvalidOptions
from lmi.scripts.common import get_logger, versioncheck

import util

LOG = get_logger(__name__)

def _gateway_check(gateway, version):
    if gateway is None:
        return None
    try:
        gw, gateway_version = util.address_check(gateway)
    except util.IPCheckFailed:
        raise LmiInvalidOptions("Invalid gateway: %s" % gateway)
    if gateway_version != version:
        raise LmiInvalidOptions("Invalid gateway, should be IPv%d: %s" % (version, gateway))
    return gw

def get_device_by_name(ns, device_name):
    '''
    Get instance of LMI_IPNetworkConnection class by the device name.

    :param str device_name: Name of the device.
    :return: LMI_IPNetworkConnection representing the device.
    :rtype: ``LMI_IPNetworkConnection`` or ``None`` if not found
    '''
    return ns.LMI_IPNetworkConnection.first_instance({ 'ElementName': device_name })

def get_setting_by_caption(ns, caption):
    '''
    Get instance of LMI_IPAssignmentSettingData class by the caption.

    :param str caption: Caption of the setting.
    :return: LMI_IPAssignmentSettingData representing the setting.
    :rtype: ``LMI_IPAssignmentSettingData`` or ``None`` if not found
    '''
    return ns.LMI_IPAssignmentSettingData.first_instance({ 'Caption': caption })

def list_devices(ns, device_names=None):
    '''
    Get a list of network devices.

    :param device_name: List of device names that will be used as filter for devices.
    :type device_name: list of str
    :return: List of instances of LMI_IPNetworkConnection
    :rtype: list of LMI_IPNetworkConnection
    '''
    for s in sorted(ns.LMI_IPNetworkConnection.instances(),
                    key=lambda i: i.ElementName):
        if device_names:
            if s.ElementName in device_names:
                yield s
        else:
            yield s

def list_settings(ns, captions=None):
    '''
    Get a list of network settings.

    :param captions: List of setting captions that will be used as filter for settings.
    :type captions: list of str
    :return: Settings that matches given captions
    :rtype: list of LMI_IPAssignmentSettingData
    '''
    for s in sorted(ns.LMI_IPAssignmentSettingData.instances(),
                    key=lambda i: i.Caption):
        if s.AddressOrigin == ns.LMI_IPAssignmentSettingData.AddressOriginValues.cumulativeconfiguration:
            if captions:
                if s.Caption in captions:
                    yield s
            else:
                yield s

def get_mac(ns, device):
    '''
    Get a MAC address for given device.

    :param LMI_IPNetworkConnection device: network device
    :return: MAC address of given device or 00:00:00:00:00:00 when no MAC is found.
    :rtype: str
    '''
    lan = device.first_associator(AssocClass="LMI_EndpointForIPNetworkConnection", ResultClass="LMI_LANEndpoint")
    return lan.MACAddress if lan.MACAddress is not None else "00:00:00:00:00:00"

def get_ip_addresses(ns, device):
    '''
    Get a list of IP addresses assigned to given device

    :param LMI_IPNetworkConnection device: network device
    :return: IP addresses with subnet masks (IPv4) or prefixes (IPv6) that is assigned to the device.
    :rtype: list of tuple (IPAddress, SubnetMask/Prefix)
    '''
    for endpoint in device.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_IPProtocolEndpoint"):
        if endpoint.ProtocolIFType == ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv4:
            yield (endpoint.IPv4Address, endpoint.SubnetMask)
        elif endpoint.ProtocolIFType == ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv6:
            yield (endpoint.IPv6Address, endpoint.IPv6SubnetPrefixLength)

def get_ipv4_addresses(ns, device):
    '''
    Get a list of IPv4 addresses assigned to given device

    :param LMI_IPNetworkConnection device: network device
    :return: IPv4 addresses with subnet masks that is assigned to the device.
    :rtype: list of tuple (IPAddress, SubnetMask)
    '''
    for endpoint in device.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_IPProtocolEndpoint"):
        if endpoint.ProtocolIFType == ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv4:
            yield (endpoint.IPv4Address, endpoint.SubnetMask)

def get_ipv6_addresses(ns, device):
    '''
    Get a list of IPv6 addresses assigned to given device

    :param LMI_IPNetworkConnection device: network device
    :return: IPv6 addresses with prefixes that is assigned to the device.
    :rtype: list of tuple (IPAddress, Prefix)
    '''
    for endpoint in device.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_IPProtocolEndpoint"):
        if endpoint.ProtocolIFType == ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv6:
            yield (endpoint.IPv6Address, endpoint.IPv6SubnetPrefixLength)


def get_default_gateways(ns, device):
    '''
    Get a list of default gateways assigned to given device

    :param LMI_IPNetworkConnection device: network device
    :return: Default gateways assigned to the device
    :rtype: list of str
    '''
    for rsap in device.associators(AssocClass="LMI_NetworkRemoteAccessAvailableToElement", ResultClass="LMI_NetworkRemoteServiceAccessPoint"):
        if rsap.AccessContext == ns.LMI_NetworkRemoteServiceAccessPoint.AccessContextValues.DefaultGateway:
            yield rsap.AccessInfo

def get_dns_servers(ns, device):
    '''
    Get a list of DNS servers assigned to given device

    :param LMI_IPNetworkConnection device: network device
    :return: DNS servers assigned to the device
    :rtype: list of str
    '''
    # There might be more links to RemoteServiceAccessPoint, filter them
    d = {}
    for ipendpoint in device.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_IPProtocolEndpoint"):
        for dnsendpoint in ipendpoint.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_DNSProtocolEndpoint"):
            for rsap in dnsendpoint.associators(AssocClass="LMI_NetworkRemoteAccessAvailableToElement", ResultClass="LMI_NetworkRemoteServiceAccessPoint"):
                if rsap.AccessContext == ns.LMI_NetworkRemoteServiceAccessPoint.AccessContextValues.DNSServer:
                    d[rsap.Name] = rsap.AccessInfo
    return d.values()

def get_available_settings(ns, device):
    '''
    Get a list of settings that can be applied to given device

    :param LMI_IPNetworkConnection device: network device
    :return: Settings applicable to the device
    :rtype: list of LMI_IPAssignmentSettingData
    '''
    for setting in device.associators(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPAssignmentSettingData"):
        yield setting

def get_active_settings(ns, device):
    '''
    Get a list of settings that are currently active on the device

    :param LMI_IPNetworkConnection device: network device
    :return: Settings that are active on the device
    :rtype: list of LMI_IPAssignmentSettingData
    '''
    for elementsettingdata in device.references(ResultClass="LMI_IPElementSettingData"):
        if elementsettingdata.IsCurrent == ns.LMI_IPElementSettingData.IsCurrentValues.IsCurrent:
            yield elementsettingdata.SettingData.to_instance()

SETTING_IP_METHOD_DISABLED = 0
''' Disabled IP configuration '''

SETTING_IP_METHOD_STATIC = 3
''' Static IP address configuration '''

SETTING_IP_METHOD_DHCP = 4
''' IP configuration obtained from DHCP server '''

SETTING_IP_METHOD_DHCPv6 = 7
''' IP configuration obtained from DHCPv6 server '''

SETTING_IP_METHOD_STATELESS = 9
''' Stateless IPv6 configuration '''


SETTING_TYPE_UNKNOWN = 0
''' Unknown type of setting '''

SETTING_TYPE_ETHERNET = 1
''' Configuration for ethernet '''

SETTING_TYPE_BOND_MASTER = 4
''' Configuration for bond master '''

SETTING_TYPE_BOND_SLAVE = 40
''' Configuration for bond slave '''

SETTING_TYPE_BRIDGE_MASTER = 5
''' Configuration for bridge master '''

SETTING_TYPE_BRIDGE_SLAVE = 50
''' Configuration for bridge slave'''

def get_setting_type(ns, setting):
    '''
    Get type of the setting

    :param LMI_IPAssignmentSettingData setting: network setting
    :return: type of setting
    :rtype: SETTING_TYPE_* constant
    '''
    if setting.classname == "LMI_BondingSlaveSettingData":
        return SETTING_TYPE_BOND_SLAVE
    elif setting.classname == "LMI_BondingMasterSettingData":
        return SETTING_TYPE_BOND_MASTER
    elif setting.classname == "LMI_BridgingSlaveSettingData":
        return SETTING_TYPE_BRIDGE_SLAVE
    elif setting.classname == "LMI_BridgingMasterSettingData":
        return SETTING_TYPE_BRIDGE_MASTER
    else:
        return SETTING_TYPE_ETHERNET

def get_setting_ip4_method(ns, setting):
    '''
    Get method of obtaining IPv4 configuration on given setting

    :param LMI_IPAssignmentSettingData setting: network setting
    :return: IPv4 method
    :rtype: SETTING_IP_METHOD_* constant
    '''
    if setting.IPv4Type == ns.LMI_IPAssignmentSettingData.IPv4TypeValues.DHCP:
        return SETTING_IP_METHOD_DHCP
    elif setting.IPv4Type == ns.LMI_IPAssignmentSettingData.IPv4TypeValues.Static:
        return SETTING_IP_METHOD_STATIC
    else:
        return SETTING_IP_METHOD_DISABLED

def get_setting_ip6_method(ns, setting):
    '''
    Get method of obtaining IPv6 configuration on given setting

    :param LMI_IPAssignmentSettingData setting: network setting
    :return: IPv6 method
    :rtype: SETTING_IP_METHOD_* constant
    '''
    if setting.IPv6Type == ns.LMI_IPAssignmentSettingData.IPv6TypeValues.Static:
        return SETTING_IP_METHOD_STATIC
    elif setting.IPv6Type == ns.LMI_IPAssignmentSettingData.IPv6TypeValues.DHCPv6:
        return SETTING_IP_METHOD_DHCPv6
    elif setting.IPv6Type == ns.LMI_IPAssignmentSettingData.IPv6TypeValues.Stateless:
        return SETTING_IP_METHOD_STATELESS
    else:
        return SETTING_IP_METHOD_DISABLED

def get_sub_setting(ns, setting):
    '''
    Get list of detailed configuration setting for each part of the setting.

    :param LMI_IPAssignmentSettingData setting: network setting
    :return: detailed setting
    :rtype: list of LMI_IPAssignmentSettingData subclasses
    '''
    return setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent")

def get_applicable_devices(ns, setting):
    '''
    Get list of network devices that this setting can be applied to.

    :param LMI_IPAssignmentSettingData setting: network setting
    :return: devices that the setting can be applied to
    :rtype: list of LMI_IPNetworkConnection
    '''

    # Handle bridging/bonding master differently
    if setting.classname in ('LMI_BridgingMasterSettingData', 'LMI_BondingMasterSettingData'):
        # return bond/bridge device in the bond/bridge setting is active
        interface_name = setting.InterfaceName
        device = ns.LMI_IPNetworkConnection.first_instance({'ElementName': interface_name})
        if device:
            return [device]
        # return all devices associated with slave settings for bridge/bond if not active
        slave_class = None
        if setting.classname == 'LMI_BridgingMasterSettingData':
            slave_class = 'LMI_BridgingSlaveSettingData'
        elif setting.classname == 'LMI_BondingMasterSettingData':
            slave_class = 'LMI_BondingSlaveSettingData'
        if slave_class is not None:
            devices = []
        for slave_setting in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent", ResultClass=slave_class):
            devices += slave_setting.associators(AssocClass="LMI_IPElementSettingData")
        return devices

    return setting.associators(AssocClass="LMI_IPElementSettingData")

def is_setting_active(ns, setting):
    '''
    Return true if the setting is currently active

    :param LMI_IPAssignmentSettingData setting: network setting
    :retval True: setting is currently active
    :retval False: setting is not currently active
    :rtype: bool
    '''
    for esd in setting.references(ResultClass="LMI_IPElementSettingData"):
        if esd.IsCurrent == ns.LMI_IPElementSettingData.IsCurrentValues.IsCurrent:
            return True
    return False

def get_static_routes(ns, setting):
    '''
    Return list of static routes for given setting

    :param LMI_IPAssignmentSettingData setting: network setting
    :return: list of static routes
    :rtype: list of LMI_IPRouteSettingData
    '''
    return setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent", ResultClass="LMI_IPRouteSettingData")

def _provider_check_required_device(ns):
    '''
    Check if provider requires device to be used in ApplySettingToIPNetworkConnection
    '''
    # Do a full fetch to obtain qualifiers
    if hasattr(ns.LMI_IPConfigurationService, "is_fetched"):
        if not ns.LMI_IPConfigurationService.is_fetched(True):
            ns.LMI_IPConfigurationService.fetch(True)
    else:
        ns.LMI_IPConfigurationService.fetch()

    version = versioncheck.get_class_version(ns.connection, 'LMI_IPConfigurationService', ns.name)
    return versioncheck.parser.cmp_version(version, '0.2.3')

def activate(ns, setting, device=None):
    '''
    Activate network setting on given device

    :param LMI_IPAssignmentSettingData setting: Setting to be activated.
    :param device: Device to activate the setting on or None for autodetection
    :type device: LMI_IPNetworkConnection or None
    '''
    service = ns.LMI_IPConfigurationService.first_instance()
    if (setting.classname in ('LMI_BridgingMasterSettingData', 'LMI_BondingMasterSettingData')
            and device is None):

        if setting.classname == 'LMI_BridgingMasterSettingData':
            slave_class = 'LMI_BridgingSlaveSettingData'
        elif setting.classname == 'LMI_BondingMasterSettingData':
            slave_class = 'LMI_BondingSlaveSettingData'

        # Autodetect and activate slaves
        for slave_setting in setting.associators(AssocClass='LMI_OrderedIPAssignmentComponent', ResultClass=slave_class):
            device = slave_setting.first_associator(AssocClass="LMI_IPElementSettingData")
            LOG().debug('Activating setting %s on device %s', setting.Caption, device.ElementName)
            result = service.SyncApplySettingToIPNetworkConnection(SettingData=slave_setting,
                    IPNetworkConnection=device,
                    Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32768)
            if result.errorstr:
                raise LmiFailed("Unable to activate setting: %s" % result.errorstr)
        # TODO: rework using indications
        isCurrent = False
        while not isCurrent:
            for esd in setting.references(ResultClass="LMI_IPElementSettingData"):
                if esd.IsCurrent == ns.LMI_IPElementSettingData.IsCurrentValues.IsCurrent:
                    isCurrent = True
                    break
            time.sleep(1)
        LOG().info("Setting %s activated", setting.Caption)
        return 0

    devices = []
    if device is not None:
        devices.append(device)
    else:
        devices = get_applicable_devices(ns, setting)

    if len(devices) == 0:
        raise LmiFailed("No device is associated with given connection.")

    for device in devices:
        LOG().debug('Activating setting %s on device %s', setting.Caption, device.ElementName)
        result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
                IPNetworkConnection=device,
                Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32768)
        if result.errorstr:
            raise LmiFailed("Unable to activate setting: %s" % result.errorstr)
    LOG().info("Setting %s activated", setting.Caption)
    return 0

def deactivate(ns, setting, device=None):
    '''
    Deactivate network setting.

    :param LMI_IPAssignmentSettingData setting: Setting to deactivate.
    :param device: Device to deactivate the setting on
    :type device: LMI_IPNetworkConnection or None
    '''
    service = ns.LMI_IPConfigurationService.first_instance()

    if _provider_check_required_device(ns):
        # old version of provider that doesn't support activation of setting without device
        if device is None:
            if setting.classname == 'LMI_BridgingMasterSettingData':
                slave_class = 'LMI_BridgingSlaveSettingData'
            elif setting.classname == 'LMI_BondingMasterSettingData':
                slave_class = 'LMI_BondingSlaveSettingData'
            else:
                slave_class = None

            # Autodetect and deactivate slaves
            if slave_class:
                affected_settings = setting.associators(AssocClass='LMI_OrderedIPAssignmentComponent', ResultClass=slave_class)
            else:
                affected_settings = [setting]

            for slave_setting in affected_settings:
                device = slave_setting.first_associator(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPNetworkConnection")
                result = service.SyncApplySettingToIPNetworkConnection(SettingData=slave_setting,
                        IPNetworkConnection=device,
                        Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32769)
                if result.errorstr:
                    raise LmiFailed("Unable to deactivate setting: %s" % result.errorstr)
                # TODO: rework using indications
                isCurrent = True
                while isCurrent:
                    for esd in slave_setting.references(ResultClass="LMI_IPElementSettingData"):
                        if esd.IsCurrent == ns.LMI_IPElementSettingData.IsCurrentValues.IsNotCurrent:
                            isCurrent = False
                            break
                    time.sleep(1)
            LOG().info("Setting %s deactivated", setting.Caption)
            return 0

    if device is not None:
        LOG().debug('Deactivating setting %s on device %s', setting.Caption, device.ElementName)
        result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
                IPNetworkConnection=device,
                Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32769)
        if result.errorstr:
            raise LmiFailed("Unable to deactivate setting: %s" % result.errorstr)
    else:
        result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
                Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32769)
        if result.errorstr:
            raise LmiFailed("Unable to deactivate setting: %s" % result.errorstr)
    LOG().info("Setting %s deactivated", setting.Caption)
    return 0

def set_autoconnect(ns, setting, device=None, state=True):
    '''
    Enable/disable automatical activation of the setting.

    :param LMI_IPAssignmentSettingData setting: Setting that will be affected
    :param bool state: `True` for autoconnection activation, `False` for deactivation
    '''
    if device is None:
        LOG().info("%s autoconnect on setting %s",
                   "Enabling" if state else "Disabling",
                   setting.Caption)
    else:
        LOG().info("%s autoconnect on setting %s on device %s",
                   "Enabling" if state else "Disabling",
                   setting.Caption,
                   device.ElementName)

    service = ns.LMI_IPConfigurationService.first_instance()
    if state:
        # Set IsNext = 1 (Is Next), don't change IsCurrent
        mode = service.ApplySettingToIPNetworkConnection.ModeValues.Mode2
    else:
        # Set IsNext = 2 (Is Not Next), don't change IsCurrent
        mode = service.ApplySettingToIPNetworkConnection.ModeValues.Mode5

    if device is None:
        result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting, Mode=mode)
    else:
        result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting, IPNetworkConnection=device, Mode=mode)
    if result.errorstr:
        raise LmiFailed("Unable to change setting autoconnect: %s" % result.errorstr)
    return result.rval

def get_autoconnect(ns, setting, device=None):
    '''
    Return True if device is activated automatically.

    :param LMI_IPAssignmentSettingData setting: Setting whose autoconnection status will be read
    '''
    for esd in setting.references(ResultClass="LMI_IPElementSettingData"):
        if device is None or esd.ManagedElement.to_instance() == device:
            break
    else:
        if device is not None:
            raise LmiFailed("No such setting %s with device %s" % (setting.Caption, device.ElementName))
        else:
            return False

    return esd.IsNext == ns.LMI_IPElementSettingData.IsNextValues.IsNext

def enslave(ns, master_setting, device):
    '''
    Create slave setting of the master_setting with given device.

    :param LMI_IPAssignmentSettingData master_setting: Master setting to use
    :param LMI_IPNetworkConnection device: Device to enslave
    '''
    capability = device.first_associator(ResultClass="LMI_IPNetworkConnectionCapabilities",
                                         AssocClass="LMI_IPNetworkConnectionElementCapabilities")
    result = capability.LMI_CreateSlaveSetting(MasterSettingData=master_setting)
    if result.rval != 0:
        raise LmiFailed("Unable to create setting: %s" % result.errorstr)
    LOG().info("Device %s enslaved to setting %s", device.ElementName, master_setting.Caption)
    return 0

def create_setting(ns, caption, device, type, ipv4method, ipv6method):
    '''
    Create new network setting.

    :param str caption: Caption for the new setting.
    :param LMI_IPNetworkConnection device: Device for which the setting will be.
    :param type: Type of the setting.
    :type type: SETTING_TYPE_* constant
    :param ipv4method: Method for obtaining IPv4 address.
    :type ipv4method: SETTING_IP_METHOD_* constant
    :param ipv4method: Method for obtaining IPv6 address.
    :type ipv6method: SETTING_IP_METHOD_* constant
    '''
    capability = device.first_associator(ResultClass="LMI_IPNetworkConnectionCapabilities",
                                         AssocClass="LMI_IPNetworkConnectionElementCapabilities")
    result = capability.LMI_CreateIPSetting(Caption=caption,
                                            Type=type,
                                            IPv4Type=ipv4method,
                                            IPv6Type=ipv6method)
    if result.rval != 0:
        raise LmiFailed("Unable to create setting: %s" % result.errorstr)
    LOG().info("Setting %s created", caption)
    return 0

def delete_setting(ns, setting):
    '''
    Delete existing network setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    '''
    caption = setting.Caption
    setting.delete()
    LOG().info("Setting %s deleted", caption)
    return 0

def add_ip_address(ns, setting, address, prefix, gateway=None):
    '''
    Add an IP address to the given static setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    :param int prefix: network prefix.
    :param gateway: default gateway or None
    :type gateway: str or None
    '''
    address, version = util.address_check(address)
    prefix = util.prefix_check(prefix, version)
    gateway = _gateway_check(gateway, version)

    protocol = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.values_dict()["IPv%s" % version]
    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if (settingData.ProtocolIFType is not None and
                int(settingData.ProtocolIFType) == protocol and
                hasattr(settingData, "IPAddresses")):

            # lmishell doesn't handle in-place editing of array parameters properly,
            # we need to create new arrays and then copy them back
            settingData.IPAddresses = settingData.IPAddresses + [address]
            if version == 4:
                settingData.SubnetMasks = settingData.SubnetMasks + [util.netmask_from_prefix(prefix)]
            else:
                settingData.IPv6SubnetPrefixLengths = settingData.IPv6SubnetPrefixLengths + [str(prefix)]
            if gateway:
                settingData.GatewayAddresses = settingData.GatewayAddresses + [gateway]
            else:
                settingData.GatewayAddresses = settingData.GatewayAddresses + [""]
            found = True
            settingData.push()
    if not found:
        raise LmiInvalidOptions("Can't add IP address to setting: invalid setting type.")
    LOG().info("IP address %s/%d added to setting %s", address, prefix, setting.Caption)
    return 0

def remove_ip_address(ns, setting, address):
    '''
    Remove the IP address from given static setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    '''
    address, version = util.address_check(address)

    protocol = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.values_dict()["IPv%s" % version]
    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if (settingData.ProtocolIFType is not None and
                int(settingData.ProtocolIFType) == protocol and
                hasattr(settingData, "IPAddresses")):

            i = 0
            # lmishell doesn't handle in-place editing of array parameters properly,
            # we need to create new arrays and then copy them back
            addresses = []
            masks = []
            gateways = []
            while i < len(settingData.IPAddresses):
                if not util.compare_address(settingData.IPAddresses[i], address):
                    addresses.append(settingData.IPAddresses[i])
                    if version == 4:
                        masks.append(settingData.SubnetMasks[i])
                    else:
                        masks.append(settingData.IPv6SubnetPrefixLengths[i])
                    gateways.append(settingData.GatewayAddresses[i])
                else:
                    found = True
                i += 1
            settingData.IPAddresses = addresses
            if version == 4:
                settingData.SubnetMasks = masks
            else:
                settingData.IPv6SubnetPrefixLengths = masks
            settingData.GatewayAddresses = gateways
            settingData.push()
    if not found:
        raise LmiInvalidOptions("Can't remove IP address from setting: invalid setting type or address doesn't exist.")
    LOG().info("IP address %s removed from setting %s", address, setting.Caption)
    return 0

def replace_ip_address(ns, setting, address, prefix, gateway=None):
    '''
    Remove all IP addresses from given static setting and add new IP address.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    :param int prefix: network prefix.
    :param gateway: default gateway or None
    :type gateway: str or None
    '''
    address, version = util.address_check(address)
    prefix = util.prefix_check(prefix, version)
    gateway = _gateway_check(gateway, version)

    protocol = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.values_dict()["IPv%s" % version]
    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if (settingData.ProtocolIFType is not None and
                int(settingData.ProtocolIFType) == protocol and
                hasattr(settingData, "IPAddresses")):

            settingData.IPAddresses = [address]
            if version == 4:
                settingData.SubnetMasks = [util.netmask_from_prefix(prefix)]
            else:
                settingData.IPv6SubnetPrefixLengths = [prefix]
            if gateway:
                settingData.GatewayAddresses = [gateway]
            else:
                settingData.GatewayAddresses = [""]
            found = True
            settingData.push()
    if not found:
        raise LmiInvalidOptions("Can't add IP address to setting: invalid setting type.")
    LOG().info("Existing addresses replaced with IP address %s/%d in setting %s", address, prefix, setting.Caption)
    return 0


def add_static_route(ns, setting, address, prefix, metric=None, next_hop=None):
    '''
    Add a static route to the given setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    :param int prefix: network prefix.
    :param metric: metric for the route or None
    :type gateway: int or None
    :param next_hop: IPv4 or IPv6 address for the next hop of the route or None
    :type next_hop: str or None
    '''
    # Check the IP address
    address, version = util.address_check(address)
    prefix = util.prefix_check(prefix, version)

    if version == 4:
        result = setting.LMI_AddStaticIPRoute(
                AddressType=setting.LMI_AddStaticIPRoute.AddressTypeValues.IPv4,
                DestinationAddress=address,
                DestinationMask=util.netmask_from_prefix(prefix))
    elif version == 6:
        result = setting.LMI_AddStaticIPRoute(
                AddressType=setting.LMI_AddStaticIPRoute.AddressTypeValues.IPv6,
                DestinationAddress=address,
                PrefixLength=prefix)
    else:
        raise LmiInvalidOptions("Invalid IP address: %s" % address)
    if result.rval != 0:
        raise LmiFailed("Unable to add static route: %s" % (result.errorstr or "unknown error"))
    route = result.rparams["Route"].to_instance()
    if metric is not None or next_hop is not None:
        if metric is not None:
            route.RouteMetric = metric
        if next_hop is not None:
            route.NextHop = next_hop
        route.push()
    LOG().info("Static route to %s/%d added to setting %s", address, prefix, setting.Caption)
    return 0

def remove_static_route(ns, setting, address):
    '''
    Remove static route to the given setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    '''
    # Check the IP address
    address, version = util.address_check(address)

    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent", ResultClass="LMI_IPRouteSettingData"):
        if util.compare_address(settingData.DestinationAddress, address):
            found = True
            settingData.delete()
    if not found:
        raise LmiInvalidOptions("No such route: %s" % address)
    LOG().info("Static route to %s removed from setting %s", address, setting.Caption)
    return 0

def replace_static_route(ns, setting, address, prefix, metric=None, next_hop=None):
    '''
    Remove all static routes and add given static route to the given setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    :param int prefix: network prefix.
    :param metric: metric for the route or None
    :type gateway: int or None
    :param next_hop: IPv4 or IPv6 address for the next hop of the route or None
    :type next_hop: str or None
    '''
    # Check the IP address
    address, version = util.address_check(address)

    # this is workaround for crashing provider, see:
    # https://bugzilla.redhat.com/show_bug.cgi?id=1067487
    while 1:
        settingData = setting.first_associator(AssocClass="LMI_OrderedIPAssignmentComponent", ResultClass="LMI_IPRouteSettingData")
        if settingData is None:
            break
        settingData.delete()
    LOG().info("Static routes replaced with route to %s/%d in setting %s", address, prefix, setting.Caption)
    return add_static_route(ns, setting, address, prefix, metric, next_hop)

def add_dns_server(ns, setting, address):
    '''
    Add a dns server to the given setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    '''
    # Check the IP address
    address, version = util.address_check(address)

    protocolIFType = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.value("IPv%d" % version)
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if (settingData.classname == "LMI_DNSSettingData" and settingData.ProtocolIFType == protocolIFType):
            settingData.DNSServerAddresses = settingData.DNSServerAddresses + [address]
            settingData.push()
            break
    else:
        raise LmiInvalidOptions("Can't assign DNS address to setting %s, invalid setting type" % setting.Caption)
    LOG().info("DNS server %s added to setting %s", address, setting.Caption)
    return 0

def remove_dns_server(ns, setting, address):
    '''
    Remove dns server from given setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    '''
    # Check the IP address
    address, version = util.address_check(address)

    protocolIFType = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.value("IPv%d" % version)
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if (settingData.classname == "LMI_DNSSettingData" and settingData.ProtocolIFType == protocolIFType):
            dns = []
            for addr in settingData.DNSServerAddresses:
                if not util.compare_address(addr, address):
                    dns.append(addr)
            if len(dns) == len(settingData.DNSServerAddresses):
                raise LmiInvalidOptions("No DNS with address %s found for setting %s" % (address, setting.Caption))
            settingData.DNSServerAddresses = dns
            settingData.push()
            return 0
    else:
        raise LmiInvalidOptions("Can't remove DNS address to setting %s, invalid setting type" % setting.Caption)
    LOG().info("DNS server %s removed from setting %s", address, setting.Caption)
    return 0

def replace_dns_server(ns, setting, address):
    '''
    Remove all dns servers and add given dns server to the given setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    '''
    # Check the IP address
    address, version = util.address_check(address)

    protocolIFType = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.value("IPv%d" % version)
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if (settingData.classname == "LMI_DNSSettingData" and settingData.ProtocolIFType == protocolIFType):
            settingData.DNSServerAddresses = [address]
            settingData.push()
            return 0
    else:
        raise LmiInvalidOptions("Can't remove DNS address to setting %s, invalid setting type" % setting.Caption)
    LOG().info("Existing DNS servers replaced with %s in setting %s", address, setting.Caption)
    return 0
