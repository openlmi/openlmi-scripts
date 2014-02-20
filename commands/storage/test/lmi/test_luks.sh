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


# 'lmi storage luks' test.

. ./base.sh

rlJournalStart

part=${PARTITIONS[0]}
pw="heslo"

rlPhaseStartTest "Create LUKS"
    rlRun "$LMI storage luks create $part -p $pw"
    rlRun -s "file -s $part"
    rlAssertGrep "LUKS encrypted file" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Open and close LUKS"
    rlRun -s "$LMI -N -H -L csv storage luks list"
    rlAssertGrep "\"$part\",\"\"" $rlRun_LOG
    rm $rlRun_LOG

    rlAssertNotExists "/dev/mapper/mydev"
    rlRun "$LMI storage luks open $part mydev -p $pw"
    rlAssertExists "/dev/mapper/mydev"

    rlRun -s "$LMI -N -H -L csv storage luks list"
    rlAssertGrep "\"$part\",\"/dev/mapper/mydev\"" $rlRun_LOG
    rm $rlRun_LOG

    rlRun "$LMI storage luks close $part"
    rlAssertNotExists "/dev/mapper/mydev"

    rlRun -s "$LMI -N -H -L csv storage luks list"
    rlAssertGrep "\"$part\",\"\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Add and remove passphrase"
    oldpw=$pw
    rlLogInfo "Add 7 passwords (=together with the initial one = 8 passwords)"
    for i in `seq 7`; do
        newpw=$pw$i
        rlLogInfo "Add password $newpw using $oldpw"
        # this also checks that addpass in the previous loop was successfull
        # and the password was really added
        rlRun "$LMI storage luks addpass $part -p $oldpw -n $newpw"
        oldpw=$newpw
    done

    rlLogInfo "Adding 9th password -> error"
    rlRun "$LMI storage luks addpass $part -p $oldpw -n ${pw}999" 1

    oldpw=$pw
    for i in `seq 7 | tac`; do
        newpw=$pw$i
        rlRun "$LMI storage luks deletepass $part -p $newpw"
        rlLogInfo "Checking the old password cannot be used"
        rlRun "$LMI storage luks open $part mydev -p $newpw" 1
    done
rlPhaseEnd

rlPhaseStartCleanup
    rlLogInfo "remove the luks format"
    rlRun "$LMI storage fs delete $part"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
