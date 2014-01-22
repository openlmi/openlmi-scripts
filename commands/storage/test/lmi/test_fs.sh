#!/bin/bash
#
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
#
# Authors: Jan Safranek <jsafrane@redhat.com>


# 'lmi fs' test.
# - create all supported filesystems
# - check that 'lmi fs list' shows them
# - delete the filesystems

. ./base.sh

rlJournalStart

part=${PARTITIONS[0]}
rlPhaseStartTest
    rlLogInfo "Getting list of supported filesystems"
    rlRun -s "$LMI -N fs list-supported"
    filesystems=$(cat $rlRun_LOG)
    rm $rlRun_LOG
    for fsname in $filesystems; do
        rlLogInfo "Test fs create $fsname"
        rlRun "$LMI fs create $fsname $part"
        rlRun -s "$LMI -N -L csv fs list $part"

        rlLogInfo "Test fs list"
        # the last column is lower-case filesystem type in double quotes
        fstype=$(cat $rlRun_LOG | cut -f 4 -d ',' )
        rlAssertEquals "Checking fs $fsname is present on $part" "\"$fsname\"" $fstype
        rm $rlRun_LOG

        rlLogInfo "Test the fs is really created"
        rlRun -s "file -s $part"
        rlAssertGrep $fsname $rlRun_LOG -i
        rlAssertGrep "FILESYSTEM" $rlRun_LOG -i
        rm $rlRun_LOG

        rlLogInfo "Test fs delete"
        rlRun "$LMI fs delete $part"

        rlLogInfo "Test the fs is really deleted"
        rlRun -s "file -s $part"
        rlAssertGrep "$part: data" $rlRun_LOG -i
        rm $rlRun_LOG
    done
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
