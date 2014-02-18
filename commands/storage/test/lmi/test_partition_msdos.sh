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


# 'lmi partition' and 'lmi partition-table' test.
# - create partition table
# - create few partitions
# - delete the partitions
#

. ./base.sh

rlJournalStart

# just the disk name as 'sda', without '/dev/'
DISKNAME=$( echo $LMI_STORAGE_DISK | sed 's!.*/!!' )
SIZE1=10M # primary one
SIZE2=20M # first logical
# third is over rest of the extended partition

rlPhaseStartTest "Create the partition table"
	rlLogInfo "Creating partition table"
	rlRun "$LMI storage partition-table create --msdos $LMI_STORAGE_DISK"

    rlLogInfo "Check the partition table exists"
    rlRun -s "parted $LMI_STORAGE_DISK print"
    rlAssertGrep "Partition Table: msdos" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi storage partition-table list shows it"
    rlRun -s "$LMI -NHL csv storage partition-table list $LMI_STORAGE_DISK"
    rlAssertGrep "\"$LMI_STORAGE_DISK\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi storage partition-table show shows it"
    rlRun -s "$LMI -NHL csv storage partition-table show $LMI_STORAGE_DISK"
    rlAssertGrep "\"Partition Table Type\",\"MS-DOS\"" $rlRun_LOG
    rlAssertGrep "\"Partition Table Size (in blocks)\",1" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Create partitions"
    rlLogInfo "Creating partitions"
    rlRun "$LMI storage partition create $LMI_STORAGE_DISK $SIZE1"
    rlRun "$LMI storage partition create --extended $LMI_STORAGE_DISK"
    rlRun "$LMI storage partition create --logical $LMI_STORAGE_DISK $SIZE2"
    rlRun "$LMI storage partition create --logical $LMI_STORAGE_DISK"

    rlLogInfo "Check lmi storage partition list shows them"
    rlRun "$LMI -NHL csv storage partition list"
    rlRun "$LMI -NHL csv storage partition list ${LMI_STORAGE_DISK}2"
    rlRun -s "$LMI -NHL csv storage partition list $LMI_STORAGE_DISK"
    rlAssertGrep "\"${LMI_STORAGE_DISK}1\",\"primary\",\"$SIZE1\"" $rlRun_LOG
    rlAssertGrep "\"${LMI_STORAGE_DISK}2\",\"extended\"," $rlRun_LOG
    rlAssertGrep "\"${LMI_STORAGE_DISK}5\",\"logical\",\"$SIZE2\"" $rlRun_LOG
    rlAssertGrep "\"${LMI_STORAGE_DISK}6\",\"logical\"," $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi partition show shows them"
    rlRun -s "$LMI -NHL csv storage partition show ${LMI_STORAGE_DISK}1"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}1\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}1\"" $rlRun_LOG
    rlAssertGrep "\"Total Size\",\"$SIZE1\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rlAssertGrep "\"Partition Type\",\"primary\"" $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -NHL csv storage partition show ${LMI_STORAGE_DISK}2"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}2\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}2\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rlAssertGrep "\"Partition Type\",\"extended\"" $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -NHL csv storage partition show ${LMI_STORAGE_DISK}5"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}5\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}5\"" $rlRun_LOG
    rlAssertGrep "\"Total Size\",\"$SIZE2\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rlAssertGrep "\"Partition Type\",\"logical\"" $rlRun_LOG
    rm $rlRun_LOG
    rlRun -s "$LMI -NHL csv storage partition show ${LMI_STORAGE_DISK}6"
    rlAssertGrep "\"Name\",\"${LMI_STORAGE_DISK}6\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"${DISKNAME}6\"" $rlRun_LOG
    rlAssertGrep "\"Disk\",\"${LMI_STORAGE_DISK}\"" $rlRun_LOG
    rlAssertGrep "\"Partition Type\",\"logical\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Delete partitions"
    rlLogInfo "Deleting partitions"
    rlRun "$LMI storage partition delete ${LMI_STORAGE_DISK}1 ${LMI_STORAGE_DISK}5 ${LMI_STORAGE_DISK}5 ${LMI_STORAGE_DISK}2"

    rlLogInfo "Check lmi storage partition list does not show them"
    rlRun -s "$LMI -NHL csv storage partition list $LMI_STORAGE_DISK"
    rlAssertNotGrep "\"${LMI_STORAGE_DISK}1\"" $rlRun_LOG
    rlAssertNotGrep "\"${LMI_STORAGE_DISK}2\"" $rlRun_LOG
    rlAssertNotGrep "\"${LMI_STORAGE_DISK}5\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
