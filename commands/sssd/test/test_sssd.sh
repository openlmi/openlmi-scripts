#!/bin/bash
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

. ./base.sh

rlJournalStart
rlPhaseStartSetup
    # configure sssd
    cp etc/sssd.conf /etc/sssd/sssd.conf
    chmod 600 /etc/sssd/sssd.conf
    cp var/* /var/lib/sss/db/
    service sssd stop
rlPhaseEnd

rlPhaseStartTest "Test lmi sssd status and restart"
    rlLogInfo "Test lmi sssd status with stopped sssd"
    rlRun -s "$LMI sssd status"
    rlAssertGrep "Status=Stopped" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "try-restart sssd "
    rlRun "$LMI sssd restart --try"

    rlLogInfo "Test lmi sssd status with stopped sssd"
    rlRun -s "$LMI sssd status"
    rlAssertGrep "Status=Stopped" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Restart sssd"
    rlRun "$LMI sssd restart"

    rlLogInfo "Test lmi sssd status with running sssd"
    rlRun -s "$LMI sssd status"
    rlAssertGrep "Status=Running" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test lmi sssd service"
    rlLogInfo "Check lmi sssd service list"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0010"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0010"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0010"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi sssd service list --enabled"
    rlRun -s "$LMI sssd service list --enabled"
    rlAssertNotGrep 'False' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi sssd service list --disabled"
    rlRun -s "$LMI sssd service list --disabled"
    rlAssertNotGrep 'True' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi sssd service show"
    # check just one service, no need to test all of them
    rlRun -s "$LMI sssd service show autofs"
    rlAssertGrep "Name=autofs" $rlRun_LOG
    rlAssertGrep "Enabled=False" $rlRun_LOG
    rlAssertGrep "Debug Level=0x0010" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Enable a service"
    rlRun "$LMI sssd service enable autofs"
    rlRun "$LMI sssd restart"

    rlRun -s "$LMI sssd service show autofs"
    rlAssertGrep "Enabled=True" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Disable a service"
    rlRun "$LMI sssd service disable autofs"
    rlRun "$LMI sssd restart"

    rlRun -s "$LMI sssd service show autofs"
    rlAssertGrep "Enabled=False" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test lmi sssd domain"
    rlLogInfo "Check lmi sssd domain list"
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",False,"0x0030","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x3ff0","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x3ff0","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x3ff0","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x3ff0","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi sssd domain list --enabled"
    rlRun -s "$LMI sssd domain list --enabled"
    rlAssertNotGrep 'False' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi sssd domain list --disabled"
    rlRun -s "$LMI sssd domain list --disabled"
    rlAssertNotGrep 'True' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi sssd domain show"
    rlRun -s "$LMI sssd domain show LOCAL"
    rlAssertGrep "Name=LOCAL" $rlRun_LOG
    rlAssertGrep "Enabled=False" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Enable a domain"
    rlRun "$LMI sssd domain enable LOCAL"
    rlRun "$LMI sssd restart"
    # LOCAL domain takes some time to initialize
    sleep 5

    rlRun -s "$LMI sssd domain show LOCAL"
    rlAssertGrep "Enabled=True" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Disable a domain"
    rlRun "$LMI sssd domain disable LOCAL"
    rlRun "$LMI sssd restart"

    rlRun -s "$LMI sssd domain show LOCAL"
    rlAssertGrep "Enabled=False" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Enable an D domain"
    rlRun "$LMI sssd domain enable AD.PB"
    rlRun "$LMI sssd restart"
    # AD.PB domain takes some time to initialize
    sleep 5

    rlRun -s "$LMI sssd domain show AD.PB"
    rlAssertGrep "Name=ad.pb" $rlRun_LOG
    rlAssertGrep "Enabled=True" $rlRun_LOG
    rlAssertGrep "ID Provider=ipa" $rlRun_LOG
    rlAssertGrep "Primary servers=_srv_" $rlRun_LOG
    rlAssertGrep "Backup servers=_srv_" $rlRun_LOG
    rlAssertGrep "Subdomains=\$" $rlRun_LOG
    rlAssertGrep "Parent domain=IPA.PB" $rlRun_LOG
    rlAssertGrep "Realm=AD.PB" $rlRun_LOG
    rlAssertGrep "Forest=\$" $rlRun_LOG
    rlAssertGrep "Enumerable=False" $rlRun_LOG
    rlAssertGrep "Minimum ID value=1" $rlRun_LOG
    rlAssertGrep "Maximum ID value=4294967295" $rlRun_LOG
    rlAssertGrep "Use fully qualified names=True" $rlRun_LOG
    rlAssertGrep 'Fully qualified name format=%1$s@%2$s' $rlRun_LOG
    rlAssertGrep 'Login expression=(((?P<domain>[^\\]+)\\(?P<name>.+$))|((?P<name>[^@]+)@(?P<domain>.+$))|(^(?P<name>[^@\\]+)$))' $rlRun_LOG -F
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Test lmi sssd debug log level"
    rlRun "$LMI sssd set-debug-level 0x123 --services=pam,ssh,sudo --domains=AD.PB"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0123"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0123"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0123"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0123","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x3ff0","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x3ff0","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x3ff0","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x3ff0","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check the log level is preserved across sssd restart"
    rlRun "$LMI sssd restart"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0123"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0123"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0123"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0123","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x3ff0","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x3ff0","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x3ff0","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x3ff0","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Test --until-restart"
    rlRun "$LMI sssd set-debug-level 0x023 --services=pam,ssh,sudo --domains=AD.PB --until-restart"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0023"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0023"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0023"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0023","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x3ff0","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x3ff0","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x3ff0","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x3ff0","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check the log level is restored after sssd restart"
    rlRun "$LMI sssd restart"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x3ff0"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0010"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0123"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0123"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0123"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0123","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x3ff0","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x3ff0","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x3ff0","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x3ff0","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Test implicit --all"
    rlRun "$LMI sssd set-debug-level 0x234"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0234"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x0234"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x0234"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0234"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0234"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0234"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0234"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0234","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x0234","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x0234","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x0234","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x0234","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Test explicit --all"
    rlRun "$LMI sssd set-debug-level 0x345 --all"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0345"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0345"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0345"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0345","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x0345","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x0345","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x0345","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x0345","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Test --until-restart with --all"
    rlRun "$LMI sssd set-debug-level 0x456 --until-restart"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0456"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x0456"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x0456"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0456"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0456"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0456"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0456"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0456","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x0456","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x0456","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x0456","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x0456","proxy"' $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check the log level is restored after sssd restart"
    rlRun "$LMI sssd restart"
    rlRun -s "$LMI -L csv sssd service list"
    rlRun -s "$LMI -L csv sssd service list"
    rlAssertGrep '"autofs",False,"0x0345"' $rlRun_LOG
    rlAssertGrep '"ifp",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"nss",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"pac",False,"0x0345"' $rlRun_LOG
    rlAssertGrep '"pam",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"ssh",True,"0x0345"' $rlRun_LOG
    rlAssertGrep '"sudo",True,"0x0345"' $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -L csv sssd domain list"
    rlAssertGrep '"AD.PB",True,"0x0345","ad"' $rlRun_LOG
    rlAssertGrep '"IPA.PB",True,"0x0345","ipa"' $rlRun_LOG
    rlAssertGrep '"LDAP.PB",True,"0x0345","ldap"' $rlRun_LOG
    rlAssertGrep '"LOCAL",False,"0x0345","local"' $rlRun_LOG
    rlAssertGrep '"PROXY",False,"0x0345","proxy"' $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
