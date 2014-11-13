# Networking Providers
#
# Copyright (C) 2012-2014 Red Hat, Inc.  All rights reserved.
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
# Authors: Radek Novacek <rnovacek@redhat.com>
#
"""
Networking service management.

Usage:
    %(cmd)s device (--help | show [<device_name> ...] | list [<device_name> ...])
    %(cmd)s setting (--help | <operation> [<args>...])
    %(cmd)s activate <caption> [<device_name>]
    %(cmd)s deactivate <caption> [<device_name>]
    %(cmd)s autoconnect (--help | <operation> [<args>...])
    %(cmd)s enslave <master_caption> <device_name>
    %(cmd)s address (--help | <operation> [<args>...])
    %(cmd)s route (--help | <operation> [<args>...])
    %(cmd)s dns (--help | <operation> [<args>...])

Commands:
    device           Display information about network devices.
    setting          Manage the network settings.
    activate         Activate setting on given network device.
    deactivate       Deactivate the setting.
    autoconnect      Enable/disable automatic setting activation.
    enslave          Create new slave setting.
    address          Manipulate the list of IP addresses on given setting.
    route            Manipulate the list of static routes on given setting.
    dns              Manipulate the list of DNS servers on given setting.
"""

from lmi.scripts.common import command
from lmi.scripts.common import errors
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.networking import *

## DEVICE

def cmd_list_devices(ns, device_names=None):
    """
    Implementation of 'net list devices' command.
    """
    for d in list_devices(ns, device_names):
        yield (d.ElementName, ns.LMI_IPNetworkConnection.OperatingStatusValues.value_name(d.OperatingStatus), get_mac(ns, d))

def cmd_show_devices(ns, device_names=None):
    """
    Implementation of 'net show devices' command.
    """
    for device in list_devices(ns, device_names):
        yield fcmd.NewTableCommand(title="Device %s" % device.ElementName)
        yield ("Operating Status", ns.LMI_IPNetworkConnection.OperatingStatusValues.value_name(device.OperatingStatus))
        yield ("MAC Address", get_mac(ns, device))
        for ip, prefix in get_ipv4_addresses(ns, device):
            yield ("IPv4 Address", "%s/%s" % (ip, prefix))
        for ip, mask in get_ipv6_addresses(ns, device):
            yield ("IPv6 Address", "%s/%s" % (ip, mask))
        for gw in get_default_gateways(ns, device):
            yield ("Default Gateway", gw)
        for dns in get_dns_servers(ns, device):
            yield ("DNS Server", dns)
        for setting in get_active_settings(ns, device):
            yield ("Active Setting", setting.Caption)
        for setting in get_available_settings(ns, device):
            yield ("Available Setting", setting.Caption)


class ListDevice(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_devices'
    COLUMNS = ('ElementName','OperatingStatus','MAC Address')

    def transform_options(self, options):
        """
        Rename 'device_name' option to 'devices' parameter name for better
        readability.
        """
        options['<device_names>'] = options.pop('<device_name>')

class ShowDevice(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_show_devices'
    COLUMNS = []

    def transform_options(self, options):
        """
        Rename 'device_name' option to 'devices' parameter name for better
        readability.
        """
        options['<device_names>'] = options.pop('<device_name>')

class Device(command.LmiCommandMultiplexer):
    """
    Display the devices present on the system.

    Usage:
        %(cmd)s list [<device_name> ...]
        %(cmd)s show [<device_name> ...]

    Commands:
        list     List basic information about devices.
        show     Show detailed information about devices.
    """
    COMMANDS = { 'list': ListDevice, 'show': ShowDevice }
    OWN_USAGE = True

## SETTING

SETTING_TYPE_DESC = {
    SETTING_TYPE_UNKNOWN: 'Unknown',
    SETTING_TYPE_ETHERNET: 'Ethernet',
    SETTING_TYPE_BRIDGE_MASTER: 'Bridge Master',
    SETTING_TYPE_BRIDGE_SLAVE: 'Bridge Slave',
    SETTING_TYPE_BOND_MASTER: 'Bond Master',
    SETTING_TYPE_BOND_SLAVE: 'Bond Slave',
}

SETTING_IP_METHOD_DESC = {
    SETTING_IP_METHOD_DISABLED: 'Disabled',
    SETTING_IP_METHOD_DHCP: 'DHCP',
    SETTING_IP_METHOD_STATIC: 'Static',
    SETTING_IP_METHOD_STATELESS: 'Stateless',
    SETTING_IP_METHOD_DHCPv6: 'DHCPv6'
}

SETTING_IPv4_METHODS = {
    "disabled": SETTING_IP_METHOD_DISABLED,
    "dhcp": SETTING_IP_METHOD_DHCP,
    "static": SETTING_IP_METHOD_STATIC
}

SETTING_IPv6_METHODS = {
    "disabled": SETTING_IP_METHOD_DISABLED,
    "dhcpv6": SETTING_IP_METHOD_DHCPv6,
    "static": SETTING_IP_METHOD_STATIC,
    "stateless": SETTING_IP_METHOD_STATELESS
}


def cmd_list_settings(ns, captions=None):
    for setting in list_settings(ns, captions):
        yield (setting.Caption, SETTING_TYPE_DESC.get(get_setting_type(ns, setting), 'Unknown'))

def cmd_show_settings(ns, captions=None):
    for setting in list_settings(ns, captions):
        yield fcmd.NewTableCommand(title="Setting %s" % setting.Caption)

        # Type
        if setting.classname == "LMI_BondingSlaveSettingData":
            yield ("Type", "Bond slave")
        elif setting.classname == "LMI_BondingMasterSettingData":
            yield ("Type", "Bond master")
            yield ("Interface", setting.InterfaceName)
            yield ("MIIMon", setting.MIIMon)
            yield ("Mode", ns.LMI_BondingMasterSettingData.ModeValues.value_name(setting.Mode))
            yield ("UpDelay", setting.UpDelay)
            yield ("DownDelay", setting.DownDelay)
            yield ("ARPInterval", setting.ARPInterval)
            if len(setting.ARPIPTarget) > 0:
                yield ("ARPIPTarget", ", ".join(setting.ARPIPTarget))
        elif setting.classname == "LMI_BridgingSlaveSettingData":
            yield ("Type", "Bridge slave")
        elif setting.classname == "LMI_BridgingMasterSettingData":
            yield ("Type", "Bridge master")
            yield ("Interface", setting.InterfaceName)


        ip4method = get_setting_ip4_method(ns, setting)
        if ip4method != SETTING_IP_METHOD_DISABLED:
            yield ("IPv4", SETTING_IP_METHOD_DESC.get(ip4method, 'Unknown'))
        ip6method = get_setting_ip6_method(ns, setting)
        if ip6method != SETTING_IP_METHOD_DISABLED:
            yield ("IPv6", SETTING_IP_METHOD_DESC.get(ip6method, 'Unknown'))

        for subsetting in get_sub_setting(ns, setting):
            if subsetting.classname == 'LMI_ExtendedStaticIPAssignmentSettingData':
                if subsetting.ProtocolIFType == ns.LMI_ExtendedStaticIPAssignmentSettingData.ProtocolIFTypeValues.IPv4:
                    version = "IPv4"
                    masks = subsetting.SubnetMasks
                else:
                    version = "IPv6"
                    masks = subsetting.IPv6SubnetPrefixLengths

                for i in range(len(subsetting.IPAddresses)):
                    mask = masks[i] if i < len(masks) else "(none)"
                    gateway = subsetting.GatewayAddresses[i] if i < len(subsetting.GatewayAddresses) else None

                    if i < len(subsetting.GatewayAddresses) and len(subsetting.GatewayAddresses[i]) > 0:
                        yield ("%s Address" % version, "%s/%s %s" % (subsetting.IPAddresses[i], mask, subsetting.GatewayAddresses[i]))
                    else:
                        yield ("%s Address" % version, "%s/%s" % (subsetting.IPAddresses[i], mask))

            elif subsetting.classname == 'LMI_DNSSettingData':
                for dns in subsetting.DNSServerAddresses:
                    yield ("DNS Server", dns)
            elif subsetting.classname in ('LMI_BridgingMasterSettingData', 'LMI_BondingMasterSettingData'):
                yield ("Master Setting", subsetting.Caption)
            elif subsetting.classname in ('LMI_BridgingSlaveSettingData', 'LMI_BondingSlaveSettingData'):
                yield ("Slave Setting", subsetting.Caption)
        # Don't show device for bridge and bond master
        if setting.classname not in ('LMI_BondingMasterSettingData', 'LMI_BridgingMasterSettingData'):
            for device in get_applicable_devices(ns, setting):
                yield ("Device", device.ElementName)
        if is_setting_active(ns, setting):
            yield ("Status", "Active")
        else:
            yield ("Status", "Inactive")
        if get_autoconnect(ns, setting):
            yield ("Autoconnect", "Enabled")
        else:
            yield ("Autoconnect", "Disabled")

        for route in get_static_routes(ns, setting):
            if route.AddressType == ns.LMI_IPRouteSettingData.AddressTypeValues.IPv4:
                yield ("IPv4 Static Route", "%s/%s %d %s" % (route.DestinationAddress, route.DestinationMask, route.RouteMetric, route.NextHop))
            else:
                yield ("IPv6 Static Route", "%s/%s %d %s" % (route.DestinationAddress, route.PrefixLength, route.RouteMetric, route.NextHop))

## Activation

def cmd_activate(ns, caption, device_name):
    setting = get_setting_by_caption(ns, caption)
    if setting is None:
        raise errors.LmiFailed("No such setting: %s" % caption)
    if device_name:
        device = get_device_by_name(ns, device_name)
        if device is None:
            raise errors.LmiFailed("No such device: %s" % device_name)
    else:
        device = None
    return activate(ns, setting, device)

def cmd_deactivate(ns, caption, device_name):
    setting = get_setting_by_caption(ns, caption)
    if setting is None:
        raise errors.LmiFailed("No such setting: %s" % caption)
    if device_name:
        device = get_device_by_name(ns, device_name)
        if device is None:
            raise errors.LmiFailed("No such device: %s" % device_name)
    else:
        device = None
    return deactivate(ns, setting, device)

class Activate(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name):
        return cmd_activate(ns, caption, device_name)

    def transform_options(self, options):
        """
        Activate takes only one caption and device, get only one element
        from the list for better readability.
        """
        if '<device_name>' in options and len(options['<device_name>']) > 0:
            options['<device_name>'] = options['<device_name>'][0]

class Deactivate(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name):
        return cmd_deactivate(ns, caption, device_name)

    def transform_options(self, options):
        """
        Activate takes only one caption and device, get only one element
        from the list for better readability.
        """
        if '<device_name>' in options and len(options['<device_name>']) > 0:
            options['<device_name>'] = options['<device_name>'][0]

## Autoconnecting

def cmd_set_autoconnect(ns, caption, device_name, enable):
    setting = get_setting_by_caption(ns, caption)
    if setting is None:
        raise errors.LmiFailed("No such setting: %s" % caption)

    device = None
    if device_name is not None:
        device = get_device_by_name(ns, device_name)
        if device is None:
            raise errors.LmiFailed("No such device: %s" % device_name)

    return set_autoconnect(ns, setting, device, enable)

class EnableAutoconnect(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name):
        return cmd_set_autoconnect(ns, caption, device_name, True)

class DisableAutoconnect(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name):
        return cmd_set_autoconnect(ns, caption, device_name, False)

class ShowAutoconnect(command.LmiLister):
    def execute(self, ns, caption, device_name):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)

        device = None
        if device_name is not None:
            device = get_device_by_name(ns, device_name)
            if device is None:
                raise errors.LmiFailed("No such device: %s" % device_name)

        if get_autoconnect(ns, setting, device):
            yield ("Setting %s is automatically activated" % caption,)
        else:
            yield ("Setting %s is not automatically activated" % caption,)

class Autoconnect(command.LmiCommandMultiplexer):
    """
     Manage the automatic setting activation.

    Usage:
        %(cmd)s show <caption> [<device_name>]
        %(cmd)s enable <caption> [<device_name>]
        %(cmd)s disable <caption> [<device_name>]

    Commands:
        show     Show currect status of automatic setting activation
        enable   Activate setting automatically when network resources are available
        disable  Setting will be only activated manually
    """
    COMMANDS = { 'show': ShowAutoconnect, 'enable' : EnableAutoconnect, 'disable': DisableAutoconnect }
    OWN_USAGE = True

## SETTING

class ListSetting(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_settings'
    COLUMNS = ('Caption', 'Type')
    def transform_options(self, options):
        """
        Rename 'caption' option to 'captions' parameter name for better
        readability.
        """
        options['<captions>'] = options.pop('<caption>')

class ShowSetting(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_show_settings'
    COLUMNS = []
    def transform_options(self, options):
        """
        Rename 'caption' option to 'captions' parameter name for better
        readability.
        """
        options['<captions>'] = options.pop('<caption>')

class CreateSetting(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name, _ethernet, _bridging, _bonding, _ipv4, _ipv6):
        type = SETTING_TYPE_ETHERNET
        if _bridging:
            type = SETTING_TYPE_BRIDGE_MASTER
        elif _bonding:
            type = SETTING_TYPE_BOND_MASTER

        if _ipv4 not in SETTING_IPv4_METHODS:
            raise errors.LmiInvalidOptions("Invalid --ipv4 option: %s" % _ipv4)
        if _ipv6 not in SETTING_IPv6_METHODS:
            raise errors.LmiInvalidOptions("Invalid --ipv6 option: %s" % _ipv6)

        ipv4_method = SETTING_IPv4_METHODS[_ipv4]
        ipv6_method = SETTING_IPv6_METHODS[_ipv6]

        device = get_device_by_name(ns, device_name)
        if device is None:
            raise errors.LmiFailed("No such device: %s" % device_name)
        create_setting(ns, caption, device, type, ipv4_method, ipv6_method)
        return 0

    def transform_options(self, options):
        """
        Create takes only one caption and device, get only one element
        from the list for better readability.
        """
        if '<caption>' in options and len(options['<caption>']) > 0:
            options['<caption>'] = options['<caption>'][0]

class DeleteSetting(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return delete_setting(ns, setting)

    def transform_options(self, options):
        """
        Delete takes only one caption, get only one element
        from the list for better readability.
        """
        if '<caption>' in options and len(options['<caption>']) > 0:
            options['<caption>'] = options['<caption>'][0]

class Setting(command.LmiCommandMultiplexer):
    """
    Manage the network configuration settings.

    Usage:
        %(cmd)s list [<caption> ...]
        %(cmd)s show [<caption> ...]
        %(cmd)s create <caption> <device_name>
                      [--ethernet | --bridging | --bonding]
                      [--ipv4 <ipv4_method>]  [--ipv6 <ipv6_method>]
        %(cmd)s delete <caption>

    Commands:
        list     List basic information about settings.
        show     Show detailed information about settings.
        create   Create new setting.
        delete   Delete existing setting.

    Options:
        --ethernet  Create ethernet setting [default].
        --bridging  Create bridging master setting.
        --bonding   Create bonding master setting.
        --ipv4 (disabled | static | dhcp)
                    IPv4 method [default: dhcp].
        --ipv6 (disabled | static | dhcpv6 | stateless)
                    IPv6 method [default: stateless].
    """
    COMMANDS = { 'list': ListSetting, 'show': ShowSetting, 'create' : CreateSetting, 'delete' : DeleteSetting }
    OWN_USAGE = True

# ADDRESS

def cmd_list_address(ns, caption=None):
    for setting in list_settings(ns, caption):
        for subsetting in get_sub_setting(ns, setting):
            if subsetting.classname == 'LMI_ExtendedStaticIPAssignmentSettingData':
                for i, address in enumerate(subsetting.IPAddresses):
                    if subsetting.ProtocolIFType == ns.LMI_ExtendedStaticIPAssignmentSettingData.ProtocolIFTypeValues.IPv4:
                        yield (
                            "IPv4",
                            address,
                            subsetting.SubnetMasks[i],
                            subsetting.GatewayAddresses[i])
                    else:
                        yield (
                            "IPv6",
                            address,
                            subsetting.IPv6SubnetPrefixLengths[i],
                            subsetting.GatewayAddresses[i])


class ListAddress(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_address'
    COLUMNS = ('Type', 'IP Address', 'Netmask/Prefix', 'Default Gateway')

class AddAddress(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address, prefix, gateway):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return add_ip_address(ns, setting, address, prefix, gateway)

class RemoveAddress(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return remove_ip_address(ns, setting, address)

class ReplaceAddress(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address, prefix, gateway):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return replace_ip_address(ns, setting, address, prefix, gateway)

class Address(command.LmiCommandMultiplexer):
    """
    Manage the list of IP addresses.

    Usage:
        %(cmd)s list <caption>
        %(cmd)s add <caption> <address> <prefix> [<gateway>]
        %(cmd)s remove <caption> <address>
        %(cmd)s replace <caption> <address> <prefix> [<gateway>]

    Commands:
        list     List static IP addresses for given setting
        add      Add IP address to the existing list of addresses.
        remove   Remove given IP address from the list of addresses.
        replace  Replace all IP address with new address.
    """
    COMMANDS = {
        'list': ListAddress,
        'add': AddAddress,
        'remove': RemoveAddress,
        'replace': ReplaceAddress
    }
    OWN_USAGE = True


## ROUTE

def cmd_list_route(ns, caption=None):
    for setting in list_settings(ns, caption):
        for route in get_static_routes(ns, setting):
            if route.AddressType == ns.LMI_IPRouteSettingData.AddressTypeValues.IPv4:
                yield (
                    "IPv4",
                    route.DestinationAddress,
                    route.DestinationMask,
                    route.RouteMetric,
                    route.NextHop)
            else:
                yield (
                    "IPv6",
                    route.DestinationAddress,
                    route.PrefixLength,
                    route.RouteMetric,
                    route.NextHop)

class ListRoute(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_route'
    COLUMNS = ('Type', 'IP Address', 'Netmask/Prefix', 'Metric', 'Next Hop')

class AddRoute(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address, prefix, metric, next_hop):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return add_static_route(ns, setting, address, prefix, metric, next_hop)

class RemoveRoute(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return remove_static_route(ns, setting, address)

class ReplaceRoute(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address, prefix, metric, next_hop):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return replace_static_route(ns, setting, address, prefix, metric, next_hop)

class Route(command.LmiCommandMultiplexer):
    """
    Manage the list of static routes.

    Usage:
        %(cmd)s list <caption>
        %(cmd)s add <caption> <address> <prefix> [<metric>] [<next_hop>]
        %(cmd)s remove <caption> <address>
        %(cmd)s replace <caption> <address> <prefix> [<metric>] [<next_hop>]

    Commands:
        list     List static routes for given setting.
        add      Add static route to the existing list of static routes.
        remove   Remove given static route from the list of static route.
        replace  Replace all static routes with new route.
    """
    COMMANDS = {
        'list': ListRoute,
        'add': AddRoute,
        'remove': RemoveRoute,
        'replace': ReplaceRoute
    }
    OWN_USAGE = True

## DNS

def cmd_list_dns(ns, caption=None):
    for setting in list_settings(ns, caption):
        for subsetting in get_sub_setting(ns, setting):
            if subsetting.classname == 'LMI_DNSSettingData':
                for dns in subsetting.DNSServerAddresses:
                    if subsetting.ProtocolIFType == ns.LMI_DNSSettingData.ProtocolIFTypeValues.IPv4:
                        yield ("IPv4", dns)
                    else:
                        yield ("IPv6", dns)

class ListDns(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_dns'
    COLUMNS = ('Type', 'IP Address')

class AddDns(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return add_dns_server(ns, setting, address)

class RemoveDns(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return remove_dns_server(ns, setting, address)

class ReplaceDns(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return replace_dns_server(ns, setting, address)

class Dns(command.LmiCommandMultiplexer):
    """
    Manage the list of DNS servers.

    Usage:
        %(cmd)s list <caption>
        %(cmd)s add <caption> <address>
        %(cmd)s remove <caption> <address>
        %(cmd)s replace <caption> <address>

    Commands:
        list     List DNS servers of given setting.
        add      Add DNS server to the existing list of DNS servers for given setting.
        remove   Remove given DNS server from the list of DNS servers for given setting.
        replace  Replace all DNS servers with given DNS server for given setting.
    """
    COMMANDS = {
        'list': ListDns,
        'add': AddDns,
        'remove': RemoveDns,
        'replace': ReplaceDns
    }
    OWN_USAGE = True

class Enslave(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, master_caption, device_name):
        setting = get_setting_by_caption(ns, master_caption)
        device = get_device_by_name(ns, device_name)
        return enslave(ns, setting, device)

    def transform_options(self, options):
        """
        Activate takes only one caption and device, get only one element
        from the list for better readability.
        """
        if '<device_name>' in options and len(options['<device_name>']) > 0:
            options['<device_name>'] = options['<device_name>'][0]

Networking = command.register_subcommands(
    'Networking', __doc__,
    {
        'device':     Device,
        'setting':    Setting,
        'activate':   Activate,
        'deactivate': Deactivate,
        'autoconnect': Autoconnect,
        'enslave':    Enslave,
        'address':    Address,
        'route':      Route,
        'dns':        Dns
    },
)
