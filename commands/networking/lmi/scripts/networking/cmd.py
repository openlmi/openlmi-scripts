# Networking Providers
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
# Authors: Radek Novacek <rnovacek@redhat.com>
#
"""
Networking service management.

Usage:
    %(cmd)s list device [<device_name> ...]
    %(cmd)s list setting [<caption> ...]
    %(cmd)s show device [<device_name> ...]
    %(cmd)s show setting [<caption> ...]
    %(cmd)s activate <caption> [<device_name>]
    %(cmd)s deactivate <caption> [<device_name>]
    %(cmd)s create <caption> <device_name> [--ethernet | --bridging | --bonding] [--ipv4 <ipv4_method>]  [--ipv6 <ipv6_method>]
    %(cmd)s delete <caption>
    %(cmd)s enslave <master_caption> <device_name>
    %(cmd)s address add <caption> <address> <prefix> [gateway]
    %(cmd)s address remove <caption> <address>

Commands:
    list            Prints a list of devices or settings.
    show            Show detailed information about device or setting.
    activate        Activates setting on given network device.
    deactivate      Deactivates the setting.
    create          Create new setting.
    delete          Delete existing setting.
    enslave         Create new slave setting.
    address         Manipulate the list of IP addresses on given setting.

Options:
    --all       List all services available.
    --disabled  List only disabled services.
    --oneshot   List only oneshot services.
    --ethernet  Create ethernet setting [default].
    --bridging  Create bridging master setting.
    --bonding   Create bonding master setting.
    -4 --ipv4 (disabled | static | dhcp)
                IPv4 method [default: dhcp].
    -6 --ipv6 (disabled | static | dhcpv6 | stateless)
                IPv6 method [default: stateless].
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
        for ip, prefix_or_mask in get_ip_adresses(ns, device):
            yield ("IP Address", "%s/%s" % (ip, prefix_or_mask))
        for gw in get_default_gateways(ns, device):
            yield ("Default Gateway", gw)
        for dns in get_dns_servers(ns, device):
            yield ("DNS Server", dns)
        for setting in get_active_settings(ns, device):
            yield ("Active Setting", setting.Caption)
        for setting in get_available_settings(ns, device):
            yield ("Available Setting", setting.Caption)


class DeviceLister(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_devices'
    COLUMNS = ('ElementName','OperatingStatus','MAC Address')
    def transform_options(self, options):
        """
        Rename 'device_name' option to 'devices' parameter name for better
        readability.
        """
        options['<device_names>'] = options.pop('<device_name>')

class DeviceShower(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_show_devices'
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'device_name' option to 'devices' parameter name for better
        readability.
        """
        options['<device_names>'] = options.pop('<device_name>')


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
    SETTING_IP_METHOD_DHCP: 'DHCP',
    SETTING_IP_METHOD_STATIC: 'Static',
    SETTING_IP_METHOD_STATELESS: 'Stateless',
    SETTING_IP_METHOD_DHCPv6: 'DHCPv6'
}


def cmd_list_settings(ns, captions=None):
    for setting in list_settings(ns, captions):
        #import ipdb
        #ipdb.set_trace()
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
                        yield ("%s Address/Netmask Gateway" % version, "%s/%s %s" % (version, subsetting.IPAddresses[i], mask, subsetting.GatewayAddresses[i]))
                    else:
                        yield ("%s Address" % version, "%s/%s" % (subsetting.IPAddresses[i], mask))

            elif subsetting.classname == 'LMI_DNSSettingData':
                for dns in subsetting.DNSServerAddresses:
                    yield ("DNS Server", dns)
            elif subsetting.classname in ('LMI_BridgingMasterSettingData', 'LMI_BondingMasterSettingData'):
                yield ("Master Setting", subsetting.Caption)
            elif subsetting.classname in ('LMI_BridgingSlaveSettingData', 'LMI_BondingSlaveSettingData'):
                yield ("Slave Setting", subsetting.Caption)
        for device in get_applicable_devices(ns, setting):
            yield ("Device", device.ElementName)

class SettingLister(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_list_settings'
    COLUMNS = ('Caption', 'Type')
    def transform_options(self, options):
        """
        Rename 'caption' option to 'captions' parameter name for better
        readability.
        """
        options['<captions>'] = options.pop('<caption>')

class SettingShower(command.LmiLister):
    CALLABLE = 'lmi.scripts.networking.cmd:cmd_show_settings'
    COLUMNS = ('Name', 'Value')
    def transform_options(self, options):
        """
        Rename 'caption' option to 'captions' parameter name for better
        readability.
        """
        options['<captions>'] = options.pop('<caption>')

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

## Mutliplexing

class Lister(command.LmiCommandMultiplexer):
    """ List information about devices or settings. """
    COMMANDS = { 'device' : DeviceLister, 'setting' : SettingLister }

class Shower(command.LmiCommandMultiplexer):
    """ Show detailed information about devices or settings. """
    COMMANDS = { 'device' : DeviceShower, 'setting' : SettingShower }

class Activate(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name):
        return cmd_activate(ns, caption, device_name)

    def transform_options(self, options):
        """
        Activate takes only one caption and device, get only one element
        from the list for better readability.
        """
        if '<caption>' in options and len(options['<caption>']) > 0:
            options['<caption>'] = options['<caption>'][0]
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
        if '<caption>' in options and len(options['<caption>']) > 0:
            options['<caption>'] = options['<caption>'][0]
        if '<device_name>' in options and len(options['<device_name>']) > 0:
            options['<device_name>'] = options['<device_name>'][0]

class Create(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, device_name, _ethernet, _bridging, _bonding, _ipv4, _ipv6):
        type = SETTING_TYPE_ETHERNET
        if _bridging:
            type = SETTING_TYPE_BRIDGE_MASTER
        elif _bonding:
            type = SETTING_TYPE_BOND_MASTER
        ipv4_method = SETTING_IP_METHOD_DISABLED
        ipv6_method = SETTING_IP_METHOD_DISABLED
        for k, v in SETTING_IP_METHOD_DESC.items():
            if v.lower() == _ipv4:
                ipv4_method = k
            if v.lower() == _ipv6:
                ipv6_method = k

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
        if '<device_name>' in options and len(options['<device_name>']) > 0:
            options['<device_name>'] = options['<device_name>'][0]

class Delete(command.LmiCheckResult):
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


class AddAddress(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address, prefix, gateway):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return add_ip_address(ns, setting, address, prefix, gateway)

    def transform_options(self, options):
        """
        AddAddress takes only one caption, get only one element
        from the list for better readability.
        """
        if '<caption>' in options and len(options['<caption>']) > 0:
            options['<caption>'] = options['<caption>'][0]

class RemoveAddress(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, caption, address):
        setting = get_setting_by_caption(ns, caption)
        if setting is None:
            raise errors.LmiFailed("No such setting: %s" % caption)
        return remove_ip_address(ns, setting, address)

    def transform_options(self, options):
        """
        RemoveAddress takes only one caption, get only one element
        from the list for better readability.
        """
        if '<caption>' in options and len(options['<caption>']) > 0:
            options['<caption>'] = options['<caption>'][0]

class Address(command.LmiCommandMultiplexer):
    """ Manage the list of IP addresses. """
    COMMANDS = { 'add' : AddAddress, 'remove' : RemoveAddress }

Networking = command.register_subcommands(
    'Networking', __doc__,
    {
        'list':       Lister,
        'show':       Shower,
        'activate':   Activate,
        'deactivate': Deactivate,
        'create':     Create,
        'delete':     Delete,
        'address':    Address
    },
)
