#!/bin/bash
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


# 'lmi mount' test.
# - create a filesystem
# - mount & unmount it

. ./base.sh

rlJournalStart

part=${PARTITIONS[0]}
testdir=$( mktemp -d /var/tmp/XXXXXXXXX )

rlPhaseStartTest "Create filesystem"
    rlLogInfo "Create filesystem"
    rlRun "$LMI fs create ext3 $part"
rlPhaseEnd

rlPhaseStartTest "Mount without any options"
    rlLogInfo "Mount the fs"
    rlRun "$LMI mount create $part $testdir"

    rlLogInfo "Check it is mounted"
    rlAssertGrep "$part.*$testdir" /proc/mounts

    rlLogInfo "Check lmi mount list shows it"
    rlRun -s "$LMI -NHL csv mount list"
    rlAssertGrep "\"$part\",\"ext3\",\"$testdir\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi mount show shows it"
    rlRun -s "$LMI -NHL csv mount show"
    rlAssertGrep "\"Mountpoint\",\"$testdir\"" $rlRun_LOG
    rlAssertGrep "\"Filesystem\",\"$part" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Unmount"
    rlLogInfo "Unmount the fs"
    rlRun "$LMI mount delete $part"

    rlLogInfo "Check it is unmounted"
    rlAssertNotGrep "$part.*$testdir" /proc/mounts

    rlLogInfo "Check lmi mount list doesn't show it"
    rlRun -s "$LMI -NHL csv mount list"
    rlAssertNptGrep "\"$part\",\"ext3\",\"$testdir\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd


rlPhaseStartTest "Delete filesystem"
    rlLogInfo "Delete filesystem"
    rlRun "$LMI fs delete $part"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
