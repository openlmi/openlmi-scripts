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


# 'lmi raid'test.
# - create raid
# - check that 'lmi raid list + show' shows it
# - delete the raid
#
# - all with various raid levels

. ./base.sh

rlJournalStart

function test_raid() {
    level=$1
    name=$2
    shift 2
    parts=$@

	rlPhaseStartTest "Create RAID $level: $name on $parts"
		rlLogInfo "Creating the RAID"
		rlRun "$LMI storage raid create --name="$name" $level $parts"

	    rlLogInfo "Check that the RAID exists"
	    rlRun "ls -l /dev/md/$name"
	    rlRun -s "mdadm -D /dev/md/$name"
	    for part in $parts; do
	        rlAssertGrep "(active|rebuilding).*$part" $rlRun_LOG -E
	    done
	    rm $rlRun_LOG

        rlLogInfo "Check lmi storage raid list output"
        rlRun -s "$LMI -NHL csv storage raid list"
        rlAssertGrep "\"$name\"" $rlRun_LOG
        rlAssertGrep "\"/dev/disk/by-id/md-name-.*:$name\"" $rlRun_LOG
        member_count=$(echo $parts | wc -w)
        rlAssertGrep ",$level,$member_count\$" $rlRun_LOG
        rm $rlRun_LOG

        rlLogInfo "Check lmi storage raid show output"
        rlRun -s "$LMI -NHL csv storage raid show $name"
        rlAssertGrep "\"DeviceID\",\"/dev/disk/by-id/md-name-.*:$name\"" $rlRun_LOG
        rlAssertGrep "\"Name\",\"/dev/md/$name\"" $rlRun_LOG
        rlAssertGrep "\"ElementName\",\"$name\"" $rlRun_LOG
        rlAssertGrep "\"RAID Level\",$level" $rlRun_LOG
        for part in $parts; do
            rlAssertGrep "\"RAID Members.*$part" $rlRun_LOG
        done
        rm $rlRun_LOG
    rlPhaseEnd

    rlPhaseStartTest "Delete RAID $level: $name on $parts"
        rlLogInfo "deleting the RAID"
        rlRun "$LMI storage raid delete $name"

        rlLogInfo "Check that the RAID does not exist"
        rlRun "ls -l /dev/md/$name" 2
        rlRun "mdadm -D /dev/md/$name" 1

        rlLogInfo "Check lmi storage raid list output"
        rlRun -s "$LMI -NHL csv storage raid list"
        rlAssertNotGrep "\"$name\"" $rlRun_LOG
        rlAssertNotGrep "\"/dev/disk/by-id/md-name-.*:$name\"" $rlRun_LOG
        rm $rlRun_LOG

        rlLogInfo "Check lmi storage raid show output"
        rlRun -s "$LMI -NHL csv storage raid show $name" 1
        rlAssertNotGrep "\"DeviceID\",\"/dev/disk/by-id/md-name-.*:$name\"" $rlRun_LOG
        rlAssertNotGrep "\"Name\",\"/dev/md/$name\"" $rlRun_LOG
    rlPhaseEnd
}

# RAID 0, 2 devices
test_raid 0 raid_0_2 ${PARTITIONS[0]} ${PARTITIONS[1]}

# RAID 0, all devices
test_raid 0 raid_0_all ${PARTITIONS[*]}

# RAID 1, 2 devices
test_raid 1 raid_1_2 ${PARTITIONS[0]} ${PARTITIONS[1]}

# RAID 1, all devices
test_raid 1 raid_1_all ${PARTITIONS[*]}

# RAID 4, all devices
test_raid 4 raid_4_all ${PARTITIONS[*]}

# RAID 5, all devices
test_raid 5 raid_5_all ${PARTITIONS[*]}

# RAID 6, all devices
test_raid 6 raid_6_all ${PARTITIONS[*]}

# RAID 10, all devices
test_raid 10 raid_10_all ${PARTITIONS[*]}

rlJournalPrintText
rlJournalEnd
