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


# 'lmi partition' and 'lmi partition-table' test.
# - create partition table
# - create few partitions
# - delete the partitions
#

. ./base.sh

rlJournalStart

# just the disk name as 'sda', without '/dev/'
DISKNAME=$( echo $LMI_STORAGE_DISK | sed 's!.*/!!' )
SIZE1=10M
SIZE2=20M
# third partition has the rest of the disk

rlPhaseStartTest "Create the partition table"
	rlLogInfo "Creating partition table"
	rlRun "$LMI partition-table create --gpt $LMI_STORAGE_DISK"

    rlLogInfo "Check the partition table exists"
    rlRun -s "parted $LMI_STORAGE_DISK print"
    rlAssertGrep "Partition Table: gpt" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi partition-table list shows it"
    rlRun -s "$LMI -NHL csv partition-table list $LMI_STORAGE_DISK"
    rlAssertGrep "\"$LMI_STORAGE_DISK\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi partition-table show shows it"
    rlRun -s "$LMI -NHL csv partition-table show $LMI_STORAGE_DISK"
    rlAssertGrep "\"Partition Table Type\",\"GPT\"" $rlRun_LOG
    rlAssertGrep "\"Partition Table Size (in blocks)\",68" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Create partitions"
    rlLogInfo "Creating partitions"
    rlRun "$LMI partition create $LMI_STORAGE_DISK $SIZE1"
    rlRun "$LMI partition create $LMI_STORAGE_DISK $SIZE2"
    rlRun "$LMI partition create $LMI_STORAGE_DISK"

    rlLogInfo "Check lmi partition list shows them"
    rlRun -s "$LMI -NHL csv partition list $LMI_STORAGE_DISK"
    rlAssertGrep "\"${LMI_STORAGE_DISK}1\",\"${DISKNAME}1\",\"\",\"$SIZE1\"" $rlRun_LOG
    rlAssertGrep "\"${LMI_STORAGE_DISK}2\",\"${DISKNAME}2\",\"\",\"$SIZE2\"" $rlRun_LOG
    rlAssertGrep "\"${LMI_STORAGE_DISK}3\",\"${DISKNAME}3\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi partition show shows them"
    rlRun -s "$LMI -NHL csv partition show ${LMI_STORAGE_DISK}1"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}1\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}1\"" $rlRun_LOG
    rlAssertGrep "\"Total Size\",\"$SIZE1\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -NHL csv partition show ${LMI_STORAGE_DISK}2"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}2\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}2\"" $rlRun_LOG
    rlAssertGrep "\"Total Size\",\"$SIZE2\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -NHL csv partition show ${LMI_STORAGE_DISK}3"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}3\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}3\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Delete partitions"
    rlLogInfo "Deleting partitions"
    rlRun "$LMI partition delete ${LMI_STORAGE_DISK}1 ${LMI_STORAGE_DISK}2 ${LMI_STORAGE_DISK}3"

    rlLogInfo "Check lmi partition list does not show them"
    rlRun -s "$LMI -NHL csv partition list $LMI_STORAGE_DISK"
    rlAssertNotGrep "\"${LMI_STORAGE_DISK}1\",\"${DISKNAME}1\",\"\",\"$SIZE1\"" $rlRun_LOG
    rlAssertNotGrep "\"${LMI_STORAGE_DISK}2\",\"${DISKNAME}2\",\"\",\"$SIZE2\"" $rlRun_LOG
    rlAssertNotGrep "\"${LMI_STORAGE_DISK}3\",\"${DISKNAME}3\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
