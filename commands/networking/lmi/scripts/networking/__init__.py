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

"""
LMI networking provider client library.
"""

from lmi.scripts.common.errors import LmiFailed, LmiInvalidOptions
from lmi.scripts.common import get_logger

import IPy

LOG = get_logger(__name__)

def get_device_by_name(ns, device_name):
    return ns.LMI_IPNetworkConnection.first_instance({ 'ElementName': device_name })

def get_setting_by_caption(ns, caption):
    return ns.LMI_IPAssignmentSettingData.first_instance({ 'Caption': caption })

def list_devices(ns, device_names=None):
    for s in sorted(ns.LMI_IPNetworkConnection.instances(),
                    key=lambda i: i.ElementName):
        if device_names:
            if s.ElementName in device_names:
                yield s
        else:
            yield s

def list_settings(ns, captions=None):
    for s in sorted(ns.LMI_IPAssignmentSettingData.instances(),
                    key=lambda i: i.Caption):
        if s.AddressOrigin == ns.LMI_IPAssignmentSettingData.AddressOriginValues.cumulativeconfiguration:
            if captions:
                if s.Caption in captions:
                    yield s
            else:
                yield s

def get_mac(ns, device):
    lan = device.first_associator(AssocClass="LMI_EndpointForIPNetworkConnection", ResultClass="LMI_LANEndpoint")
    return lan.MACAddress if lan.MACAddress is not None else "00:00:00:00:00:00"

def get_ip_adresses(ns, device):
    for endpoint in device.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_IPProtocolEndpoint"):
        if endpoint.ProtocolIFType == ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv4:
            yield (endpoint.IPv4Address, endpoint.SubnetMask)
        elif endpoint.ProtocolIFType == ns.LMI_IPProtocolEndpoint.ProtocolIFTypeValues.IPv6:
            yield (endpoint.IPv6Address, endpoint.IPv6SubnetPrefixLength)

def get_default_gateways(ns, device):
    for rsap in device.associators(AssocClass="LMI_NetworkRemoteAccessAvailableToElement", ResultClass="LMI_NetworkRemoteServiceAccessPoint"):
        if rsap.AccessContext == ns.LMI_NetworkRemoteServiceAccessPoint.AccessContextValues.DefaultGateway:
            yield rsap.AccessInfo

def get_dns_servers(ns, device):
    # TODO: check if this is not actually a bug
    # There might be more links to RemoteServiceAccessPoint, filter them
    d = {}
    for ipendpoint in device.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_IPProtocolEndpoint"):
        for dnsendpoint in ipendpoint.associators(AssocClass="LMI_NetworkSAPSAPDependency", ResultClass="LMI_DNSProtocolEndpoint"):
            for rsap in dnsendpoint.associators(AssocClass="LMI_NetworkRemoteAccessAvailableToElement", ResultClass="LMI_NetworkRemoteServiceAccessPoint"):
                if rsap.AccessContext == ns.LMI_NetworkRemoteServiceAccessPoint.AccessContextValues.DNSServer:
                    d[rsap.Name] = rsap.AccessInfo
    return d.values()

def get_available_settings(ns, device):
    for setting in device.associators(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPAssignmentSettingData"):
        yield setting

def get_active_settings(ns, device):
    for elementsettingdata in device.references(ResultClass="LMI_IPElementSettingData"):
        if elementsettingdata.IsCurrent == ns.LMI_IPElementSettingData.IsCurrentValues.IsCurrent:
            yield elementsettingdata.SettingData.to_instance()

SETTING_IP_METHOD_DISABLED = 0
SETTING_IP_METHOD_STATIC = 3
SETTING_IP_METHOD_DHCP = 4
SETTING_IP_METHOD_DHCPv6 = 7
SETTING_IP_METHOD_STATELESS = 9

SETTING_TYPE_UNKNOWN = 0
SETTING_TYPE_ETHERNET = 1
SETTING_TYPE_BRIDGE_MASTER = 4
SETTING_TYPE_BRIDGE_SLAVE = 40
SETTING_TYPE_BOND_MASTER = 5
SETTING_TYPE_BOND_SLAVE = 50

def get_setting_type(ns, setting):
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
    if setting.IPv4Type == ns.LMI_IPAssignmentSettingData.IPv4TypeValues.DHCP:
        return SETTING_IP_METHOD_DHCP
    elif setting.IPv4Type == ns.LMI_IPAssignmentSettingData.IPv4TypeValues.Static:
        return SETTING_IP_METHOD_STATIC
    else:
        return SETTING_IP_METHOD_DISABLED

def get_setting_ip6_method(ns, setting):
    if setting.IPv6Type == ns.LMI_IPAssignmentSettingData.IPv6TypeValues.Static:
        return SETTING_IP_METHOD_STATIC
    elif setting.IPv6Type == ns.LMI_IPAssignmentSettingData.IPv6TypeValues.DHCPv6:
        return SETTING_IP_METHOD_DHCPv6
    elif setting.IPv6Type == ns.LMI_IPAssignmentSettingData.IPv6TypeValues.Stateless:
        return SETTING_IP_METHOD_STATELESS
    else:
        return SETTING_IP_METHOD_DISABLED

def get_sub_setting(ns, setting):
    return setting.associators(AssocClass="LMI_OrderedIPAssignmentComponent")

def get_applicable_devices(ns, setting):
    return setting.associators(AssocClass="LMI_IPElementSettingData")


def activate(ns, setting, device):
    """
    Activate network setting on given device

    :param setting: (``LMI_IPAssignmentSettingData``) Setting to be activated.
    :param device: (``LMI_IPNetworkConnection``) Device to activate the setting on.
    """
    if device is None:
        device = setting.first_associator(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPNetworkConnection")
        if device is None:
            raise LmiFailed("No device is associated with given connection")
    service = ns.LMI_IPConfigurationService.first_instance()
    result = service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
            IPNetworkConnection=device,
            Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32768)
    return 0

def deactivate(ns, setting, device):
    """
    Deactivate network setting

    :param setting: (``LMI_IPAssignmentSettingData``) Setting to deactivate.
    :param device: (``LMI_IPNetworkConnection`` or None) Device to deactivate the setting on
    """
    if device is None:
        device = setting.first_associator(AssocClass="LMI_IPElementSettingData", ResultClass="LMI_IPNetworkConnection")
        if device is None:
            raise LmiFailed("No device is associated with given connection")
    service = ns.LMI_IPConfigurationService.first_instance()
    return service.SyncApplySettingToIPNetworkConnection(SettingData=setting,
            IPNetworkConnection=device, #ns.LMI_IPNetworkConnection.first_instance(),
            Mode=service.ApplySettingToIPNetworkConnection.ModeValues.Mode32769)

def create_setting(ns, caption, device, type, ipv4method, ipv6method):
    capability = device.first_associator(ResultClass="LMI_IPNetworkConnectionCapabilities",
                                         AssocClass="LMI_IPNetworkConnectionElementCapabilities")
    result = capability.LMI_CreateIPSetting(Caption=caption,
                                            Type=type,
                                            IPv4Type=ipv4method,
                                            IPv6Type=ipv6method)
    return 0

def delete_setting(ns, setting):
    setting.delete()
    return 0

def add_ip_address(ns, setting, address, prefix, gateway):
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
        raise LmiInvalidOptions("Can't add IP address to setting: invalid setting type")
    return 0

def remove_ip_address(ns, setting, address):
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
        raise LmiInvalidOptions("Can't remove IP address from setting: invalid setting type or address doesn't exist")
    return 0
