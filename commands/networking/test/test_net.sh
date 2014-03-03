#!/bin/bash
#
# Copyright (C) 2014 Red Hat, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
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


. ./base.sh

IFS=',' read -a PORTS <<< "${LMI_NETWORKING_PORTS}"
PORT1=${PORTS[0]}
PORT2=${PORTS[1]}

rlJournalStart

rlPhaseStartSetup

rlPhaseEnd

rlPhaseStartTest "Test enumerations"
    rlLogInfo "List devices"
    rlRun -s "$LMI net device list"
    rlAssertGrep "$PORT1" $rlRun_LOG
    rlAssertGrep "$PORT2" $rlRun_LOG

    rlLogInfo "Show devices"
    rlRun -s "$LMI net device show"
    rlAssertGrep "Device $PORT1" $rlRun_LOG
    rlAssertGrep "Device $PORT2" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test basic settings"
    rlLogInfo "List settings"
    rlRun "$LMI net setting list"
    rlRun "$LMI net setting show"

    rlLogInfo "Create setting with default options"
    rlRun "$LMI net setting create 'XXX Test' $PORT1"
    rlRun -s "$LMI net setting list"
    rlAssertGrep "XXX Test +Ethernet" $rlRun_LOG -E

    rlLogInfo "Delete setting"
    rlRun "$LMI net setting delete 'XXX Test'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test static settings"
    rlLogInfo "Create setting with static IPv4"
    rlRun "$LMI net setting create 'XXX Test Static' $PORT1 --ipv4 static"
    rlRun -s "$LMI net setting list"
    rlAssertGrep "XXX Test Static +Ethernet" $rlRun_LOG -E

    rlLogInfo "Replace static IPv4 address"
    rlRun "$LMI net address replace 'XXX Test Static' 192.168.1.1 24"
    rlRun -s "$LMI net setting show 'XXX Test Static'"
    rlAssertGrep "IPv4 Address +192.168.1.1/255.255.255.0" $rlRun_LOG -E

    rlLogInfo "Add static IPv4 address"
    rlRun "$LMI net address add 'XXX Test Static' 192.168.1.2 24 192.168.1.100"
    rlRun -s "$LMI net setting show 'XXX Test Static'"
    rlAssertGrep "IPv4 Address +192.168.1.1/255.255.255.0" $rlRun_LOG -E
    rlAssertGrep "IPv4 Address +192.168.1.2/255.255.255.0 192.168.1.100" $rlRun_LOG -E

    rlLogInfo "Remove static IPv4 address"
    rlRun "$LMI net address remove 'XXX Test Static' 192.168.1.2"
    rlRun -s "$LMI net setting show 'XXX Test Static'"
    rlAssertGrep "IPv4 Address +192.168.1.1/255.255.255.0" $rlRun_LOG -E
    rlAssertNotGrep "IPv4 Address +192.168.1.2/255.255.255.0" $rlRun_LOG -E

    rlLogInfo "Delete static IPv4 setting"
    rlRun "$LMI net setting delete 'XXX Test Static'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test Static" $rlRun_LOG

    rlLogInfo "Create setting with static IPv6"
    rlRun "$LMI net setting create 'XXX Test Static' $PORT1 --ipv6 static"
    rlRun -s "$LMI net setting list"
    rlAssertGrep "XXX Test Static +Ethernet" $rlRun_LOG -E

    rlLogInfo "Replace static IPv6 address"
    rlRun "$LMI net address replace 'XXX Test Static' 2001:DB8::1 32"
    rlRun -s "$LMI net setting show 'XXX Test Static'"
    rlAssertGrep "IPv6 Address +2001:DB8::1/32" $rlRun_LOG '-E -i'

    rlLogInfo "Add static IPv6 address"
    rlRun "$LMI net address add 'XXX Test Static' 2001:DB8::2 32"
    rlRun -s "$LMI net setting show 'XXX Test Static'"
    rlAssertGrep "IPv6 Address +2001:DB8::1/32" $rlRun_LOG '-E -i'
    rlAssertGrep "IPv6 Address +2001:DB8::2/32" $rlRun_LOG '-E -i'

    rlLogInfo "Remove static IPv6 address"
    rlRun "$LMI net address remove 'XXX Test Static' 2001:DB8::2"
    rlRun -s "$LMI net setting show 'XXX Test Static'"
    rlAssertGrep "IPv6 Address +2001:DB8::1/32" $rlRun_LOG '-E -i'
    rlAssertNotGrep "IPv6 Address +2001:DB8::2/32" $rlRun_LOG '-E -i'

    rlLogInfo "Delete static IPv6 setting"
    rlRun "$LMI net setting delete 'XXX Test Static'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test Static" $rlRun_LOG

    rlLogInfo "Create setting with static IPv4 and IPv6"
    rlRun "$LMI net setting create 'XXX Test Static' $PORT1 --ipv4 static --ipv6 static"
    rlRun -s "$LMI net setting list"
    rlAssertGrep "XXX Test Static +Ethernet" $rlRun_LOG -E

    rlLogInfo "Delete static IPv6 setting"
    rlRun "$LMI net setting delete 'XXX Test Static'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test Static" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test DHCP(v6) settings"
    rlLogInfo "Create setting with IPv4 DHCP"
    rlRun "$LMI net setting create 'XXX Test DHCP' $PORT1 --ipv4 dhcp"
    rlRun -s "$LMI net setting list"
    rlAssertGrep "XXX Test DHCP +Ethernet" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test DHCP'"
    rlAssertGrep "IPv4 +DHCP" $rlRun_LOG -E

    rlLogInfo "Delete IPv4 DHCP setting"
    rlRun "$LMI net setting delete 'XXX Test DHCP'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test DHCP" $rlRun_LOG

    rlLogInfo "Create setting with IPv6 DHCPv6"
    rlRun "$LMI net setting create 'XXX Test DHCP' $PORT1 --ipv6 dhcpv6"
    rlRun -s "$LMI net setting list"
    rlAssertGrep "XXX Test DHCP +Ethernet" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test DHCP'"
    rlAssertGrep "IPv6 +DHCPv6" $rlRun_LOG -E

    rlLogInfo "Delete IPv6 DHCPv6 setting"
    rlRun "$LMI net setting delete 'XXX Test DHCP'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test DHCP" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test setting activation"
    rlLogInfo "Create setting with DHCP IPv4 and Stateless IPv6"
    rlRun "$LMI net setting create 'XXX Test DHCP' $PORT1 --ipv4 dhcp --ipv6 stateless"

    rlLogInfo "Activate setting with port specified"
    rlRun "$LMI net activate 'XXX Test DHCP' $PORT1"
    rlRun -s "$LMI net setting show 'XXX Test DHCP'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E

    rlLogInfo "Deactivate setting with port specified"
    rlRun "$LMI net deactivate 'XXX Test DHCP' $PORT1"
    rlRun -s "$LMI net setting show 'XXX Test DHCP'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E

    rlLogInfo "Activate setting without port specified"
    rlRun "$LMI net activate 'XXX Test DHCP'"
    rlRun -s "$LMI net setting show 'XXX Test DHCP'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E

    rlLogInfo "Deactivate setting without port specified"
    rlRun "$LMI net deactivate 'XXX Test DHCP'"
    rlRun -s "$LMI net setting show 'XXX Test DHCP'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E

    rlLogInfo "Delete setting"
    rlRun "$LMI net setting delete 'XXX Test DHCP'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test DHCP" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test bridging"
    rlLogInfo "Create bridge setting"
    rlRun "$LMI net setting create 'XXX Test Bridge' $PORT1 --bridging"
    rlRun -s "$LMI net setting show 'XXX Test Bridge'"
    rlAssertGrep "Type +Bridge master" $rlRun_LOG -E
    rlAssertGrep "Slave Setting +XXX Test Bridge Slave 1" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bridge Slave 1'"
    rlAssertGrep "Type +Bridge slave" $rlRun_LOG -E
    rlAssertGrep "Master Setting +XXX Test Bridge" $rlRun_LOG -E
    rlAssertGrep "Device +$PORT1" $rlRun_LOG -E

    rlLogInfo "Enslave device"
    rlRun "$LMI net enslave 'XXX Test Bridge' $PORT2"
    rlRun -s "$LMI net setting show 'XXX Test Bridge'"
    rlAssertGrep "Type +Bridge master" $rlRun_LOG -E
    rlAssertGrep "Slave Setting +XXX Test Bridge Slave 1" $rlRun_LOG -E
    rlAssertGrep "Slave Setting +XXX Test Bridge Slave 2" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bridge Slave 2'"
    rlAssertGrep "Type +Bridge slave" $rlRun_LOG -E
    rlAssertGrep "Master Setting +XXX Test Bridge" $rlRun_LOG -E
    rlAssertGrep "Device +$PORT2" $rlRun_LOG -E

    rlLogInfo "Activate bridge"
    rlRun "$LMI net activate 'XXX Test Bridge'"
    rlRun -s "$LMI net setting show 'XXX Test Bridge'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bridge Slave 1'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bridge Slave 2'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E

    rlLogInfo "Deactivate bridge"
    rlRun "$LMI net deactivate 'XXX Test Bridge'"
    rlRun -s "$LMI net setting show 'XXX Test Bridge'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bridge Slave 1'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bridge Slave 2'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E

    rlLogInfo "Delete bridge"
    rlRun "$LMI net setting delete 'XXX Test Bridge'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test Bridge" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test bonding"
    rlLogInfo "Create bonding setting"
    rlRun "$LMI net setting create 'XXX Test Bond' $PORT1 --bonding"
    rlRun -s "$LMI net setting show 'XXX Test Bond'"
    rlAssertGrep "Type +Bond master" $rlRun_LOG -E
    rlAssertGrep "Slave Setting +XXX Test Bond Slave 1" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bond Slave 1'"
    rlAssertGrep "Type +Bond slave" $rlRun_LOG -E
    rlAssertGrep "Master Setting +XXX Test Bond" $rlRun_LOG -E
    rlAssertGrep "Device +$PORT1" $rlRun_LOG -E

    rlLogInfo "Enslave device"
    rlRun "$LMI net enslave 'XXX Test Bond' $PORT2"
    rlRun -s "$LMI net setting show 'XXX Test Bond'"
    rlAssertGrep "Type +Bond master" $rlRun_LOG -E
    rlAssertGrep "Slave Setting +XXX Test Bond Slave 1" $rlRun_LOG -E
    rlAssertGrep "Slave Setting +XXX Test Bond Slave 2" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bond Slave 2'"
    rlAssertGrep "Type +Bond slave" $rlRun_LOG -E
    rlAssertGrep "Master Setting +XXX Test Bond" $rlRun_LOG -E
    rlAssertGrep "Device +$PORT2" $rlRun_LOG -E

    rlLogInfo "Activate bond"
    rlRun "$LMI net activate 'XXX Test Bond'"
    rlRun -s "$LMI net setting show 'XXX Test Bond'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bond Slave 1'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bond Slave 2'"
    rlAssertGrep "Status +Active" $rlRun_LOG -E

    rlLogInfo "Deactivate bond"
    rlRun "$LMI net deactivate 'XXX Test Bond'"
    rlRun -s "$LMI net setting show 'XXX Test Bond'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bond Slave 1'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E
    rlRun -s "$LMI net setting show 'XXX Test Bond Slave 2'"
    rlAssertGrep "Status +Inactive" $rlRun_LOG -E

    rlLogInfo "Delete bond"
    rlRun "$LMI net setting delete 'XXX Test Bond'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test Bond" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test static routes"
    rlLogInfo "Create test setting"
    rlRun "$LMI net setting create 'XXX Test' $PORT1 --ipv4 static --ipv6 static"

    rlLogInfo "Add static IPv4 route"
    rlRun "$LMI net route add 'XXX Test' 192.168.100.1 24"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "IPv4 Static Route +192.168.100.1/255.255.255.0 0 0.0.0.0" $rlRun_LOG -E

    rlLogInfo "Add another static IPv4 route"
    rlRun "$LMI net route add 'XXX Test' 192.168.100.2 24 100"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "IPv4 Static Route +192.168.100.1/255.255.255.0 0 0.0.0.0" $rlRun_LOG -E
    rlAssertGrep "IPv4 Static Route +192.168.100.2/255.255.255.0 100 0.0.0.0" $rlRun_LOG -E

    rlLogInfo "Replace static IPv4 route"
    rlRun "$LMI net route replace 'XXX Test' 192.168.100.3 24 100 192.168.100.30"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "IPv4 Static Route +192.168.100.1" $rlRun_LOG -E
    rlAssertNotGrep "IPv4 Static Route +192.168.100.2" $rlRun_LOG -E
    rlAssertGrep "IPv4 Static Route +192.168.100.3/255.255.255.0 100 192.168.100.30" $rlRun_LOG -E

    rlLogInfo "Remove static IPv4 route"
    rlRun "$LMI net route remove 'XXX Test' 192.168.100.3"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "IPv4 Static Route +192.168.100.3" $rlRun_LOG "-E -i"

    rlLogInfo "Add static IPv6 route"
    rlRun "$LMI net route add 'XXX Test' 2001:DB8::1 32"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "IPv6 Static Route +2001:DB8::1/32 0 ::" $rlRun_LOG "-E -i"

    rlLogInfo "Add another static IPv6 route"
    rlRun "$LMI net route add 'XXX Test' 2001:DB8::2 32 100"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "IPv6 Static Route +2001:DB8::1/32 0 ::" $rlRun_LOG "-E -i"
    rlAssertGrep "IPv6 Static Route +2001:DB8::2/32 100" $rlRun_LOG "-E -i"

    rlLogInfo "Replace static IPv6 route"
    rlRun "$LMI net route replace 'XXX Test' 2001:DB8::3 32 100 2001:DB8::30"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "IPv6 Static Route +2001:DB8::1" $rlRun_LOG "-E -i"
    rlAssertNotGrep "IPv6 Static Route +2001:DB8::2" $rlRun_LOG "-E -i"
    rlAssertGrep "IPv6 Static Route +2001:DB8::3/32 100 2001:DB8::30" $rlRun_LOG "-E -i"

    rlLogInfo "Remove static IPv6 route"
    rlRun "$LMI net route remove 'XXX Test' 2001:DB8::3"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "IPv6 Static Route +2001:DB8::3" $rlRun_LOG "-E -i"

    rlLogInfo "Delete test setting"
    rlRun "$LMI net setting delete 'XXX Test'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test" $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test setup DNS servers"
    rlLogInfo "Create test setting"
    rlRun "$LMI net setting create 'XXX Test' $PORT1 --ipv4 static --ipv6 static"

    rlLogInfo "Add IPv4 DNS server"
    rlRun "$LMI net dns add 'XXX Test' 192.168.100.1"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "DNS Server +192.168.100.1" $rlRun_LOG -E

    rlLogInfo "Add another IPv4 DNS server"
    rlRun "$LMI net dns add 'XXX Test' 192.168.100.2"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "DNS Server +192.168.100.1" $rlRun_LOG -E
    rlAssertGrep "DNS Server +192.168.100.2" $rlRun_LOG -E

    rlLogInfo "Remove IPv4 DNS server"
    rlRun "$LMI net dns remove 'XXX Test' 192.168.100.1"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "DNS Server +192.168.100.1" $rlRun_LOG -E
    rlAssertGrep "DNS Server +192.168.100.2" $rlRun_LOG -E

    rlLogInfo "Replace IPv4 DNS server"
    rlRun "$LMI net dns replace 'XXX Test' 192.168.100.3"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "DNS Server +192.168.100.1" $rlRun_LOG -E
    rlAssertNotGrep "DNS Server +192.168.100.2" $rlRun_LOG -E
    rlAssertGrep "DNS Server +192.168.100.3" $rlRun_LOG -E

    rlLogInfo "Add IPv6 DNS server"
    rlRun "$LMI net dns add 'XXX Test' 2001:DB8::1"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "DNS Server +2001:DB8::1" $rlRun_LOG "-E -i"

    rlLogInfo "Add another IPv6 DNS server"
    rlRun "$LMI net dns add 'XXX Test' 2001:DB8::2"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertGrep "DNS Server +2001:DB8::1" $rlRun_LOG "-E -i"
    rlAssertGrep "DNS Server +2001:DB8::2" $rlRun_LOG "-E -i"

    rlLogInfo "Remove IPv6 DNS server"
    rlRun "$LMI net dns remove 'XXX Test' 2001:DB8::1"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "DNS Server +2001:DB8::1" $rlRun_LOG "-E -i"
    rlAssertGrep "DNS Server +2001:DB8::2" $rlRun_LOG "-E -i"

    rlLogInfo "Replace IPv6 DNS server"
    rlRun "$LMI net dns replace 'XXX Test' 2001:DB8::3"
    rlRun -s "$LMI net setting show 'XXX Test'"
    rlAssertNotGrep "DNS Server +2001:DB8::1" $rlRun_LOG "-E -i"
    rlAssertNotGrep "DNS Server +2001:DB8::2" $rlRun_LOG "-E -i"
    rlAssertGrep "DNS Server +2001:DB8::3" $rlRun_LOG "-E -i"

    rlLogInfo "Delete test setting"
    rlRun "$LMI net setting delete 'XXX Test'"
    rlRun -s "$LMI net setting list"
    rlAssertNotGrep "XXX Test" $rlRun_LOG
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
