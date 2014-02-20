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

"""
LMI networking provider client library.
"""

from lmi.scripts.common.errors import LmiFailed, LmiInvalidOptions
from lmi.scripts.common import get_logger

import IPy

LOG = get_logger(__name__)

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

def activate(ns, setting, device=None):
    '''
    Activate network setting on given device

    :param LMI_IPAssignmentSettingData setting: Setting to be activated.
    :param device: Device to activate the setting on or None for autodetection
    :type device: LMI_IPNetworkConnection or None
    '''
    if device is None:
        device = setting.first_associator(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPNetworkConnection")
        if device is None:
            raise LmiFailed("No device is associated with given connection.")
    service = ns.LMI_IPConfigurationService.first_instance()
    result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
            IPNetworkConnection=device,
            Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32768)
    return 0

def deactivate(ns, setting, device=None):
    '''
    Deactivate network setting.

    :param LMI_IPAssignmentSettingData setting: Setting to deactivate.
    :param device: Device to deactivate the setting on
    :type device: LMI_IPNetworkConnection or None
    '''
    if device is None:
        device = setting.first_associator(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPNetworkConnection")
        if device is None:
            raise LmiFailed("No device is associated with given connection.")
    service = ns.LMI_IPConfigurationService.first_instance()
    return service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
            IPNetworkConnection=device, #ns.LMI_IPNetworkConnection.first_instance(),
            Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32769)

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
    return 0

def delete_setting(ns, setting):
    '''
    Delete existing network setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    '''
    setting.delete()
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
    # Check the IP address
    try:
        address_int, version = IPy.parseAddress(address)
    except ValueError:
        raise LmiInvalidOptions("Invalid IP address: %s" % address)
    address = IPy.intToIp(address_int, version)

    # Check the prefix
    try:
        prefix_int = int(prefix)
    except ValueError:
        raise LmiInvalidOptions("Invalid prefix: %s" % prefix)
    if (version == 4 and prefix_int > 32) or (version == 6 and prefix_int > 128):
        raise LmiInvalidOptions("Invalid prefix: %s" % prefix)
    prefix = str(prefix_int)

    # Check the gateway
    if gateway:
        try:
            gateway_int, gateway_version = IPy.parseAddress(gateway)
        except ValueError:
            raise LmiInvalidOptions("Invalid gateway: %s" % gateway)
        if gateway_version != version:
            raise LmiInvalidOptions("Invalid gateway, should be IPv%d: %s" % (version, gateway))
        gateway = IPy.intToIp(gateway_int, version)

    protocol = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.values_dict()["IPv%s" % version]
    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if int(settingData.ProtocolIFType) == protocol and hasattr(settingData, "IPAddresses"):
            settingData.IPAddresses.append(address)
            if version == 4:
                settingData.SubnetMasks.append(IPy.IP("0.0.0.0/%s" % prefix).netmask().strFullsize())
            else:
                settingData.IPv6SubnetPrefixLengths.append(prefix)
            if gateway:
                settingData.GatewayAddresses.append(gateway)
            else:
                settingData.GatewayAddresses.append("")
            found = True
            settingData.push()
    if not found:
        raise LmiInvalidOptions("Can't add IP address to setting: invalid setting type.")
    return 0

def remove_ip_address(ns, setting, address):
    '''
    Remove the IP address from given static setting.

    :param LMI_IPAssignmentSettingData setting: network setting.
    :param str address: IPv4 or IPv6 address.
    '''
    # Check the IP address
    try:
        address_int, version = IPy.parseAddress(address)
    except ValueError:
        raise LmiInvalidOptions("Invalid IP address: %s" % address)
    address = IPy.intToIp(address_int, version)

    protocol = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.values_dict()["IPv%s" % version]
    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if int(settingData.ProtocolIFType) == protocol and hasattr(settingData, "IPAddresses"):
            i = 0
            while i < len(settingData.IPAddresses):
                if settingData.IPAddresses[i] == address:
                    del settingData.IPAddresses[i]
                    if version == 4:
                        del settingData.SubnetMasks[i]
                    else:
                        del settingData.IPv6SubnetPrefixLengths[i]
                    del settingData.GatewayAddresses[i]
                    found = True
                i += 1
            settingData.push()
    if not found:
        raise LmiInvalidOptions("Can't remove IP address from setting: invalid setting type or address doesn't exist.")
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
    # Check the IP address
    try:
        address_int, version = IPy.parseAddress(address)
    except ValueError:
        raise LmiInvalidOptions("Invalid IP address: %s" % address)
    address = IPy.intToIp(address_int, version)

    # Check the prefix
    try:
        prefix_int = int(prefix)
    except ValueError:
        raise LmiInvalidOptions("Invalid prefix: %s" % prefix)
    if (version == 4 and prefix_int > 32) or (version == 6 and prefix_int > 128):
        raise LmiInvalidOptions("Invalid prefix: %s" % prefix)
    prefix = str(prefix_int)

    # Check the gateway
    if gateway:
        try:
            gateway_int, gateway_version = IPy.parseAddress(gateway)
        except ValueError:
            raise LmiInvalidOptions("Invalid gateway: %s" % gateway)
        if gateway_version != version:
            raise LmiInvalidOptions("Invalid gateway, should be IPv%d: %s" % (version, gateway))
        gateway = IPy.intToIp(gateway_int, version)

    protocol = ns.LMI_IPAssignmentSettingData.ProtocolIFTypeValues.values_dict()["IPv%s" % version]
    found = False
    for settingData in setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent"):
        if int(settingData.ProtocolIFType) == protocol and hasattr(settingData, "IPAddresses"):
            settingData.IPAddresses = [address]
            if version == 4:
                settingData.SubnetMasks = [IPy.IP("0.0.0.0/%s" % prefix).netmask().strFullsize()]
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
    return 0
