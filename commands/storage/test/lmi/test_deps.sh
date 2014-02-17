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


# 'lmi storage' test.
# - create three partitions, p1-p3
# - add p1+p2 to MD RAID m0
# - add m0 + p3 to VG
# - create two LVs from the VG
# - create filesystems on the LVs
# - check 'lmi storage' - dependencies, listing, tree, ...

. ./base.sh

rlJournalStart

part=${PARTITIONS[0]}
testdir=$( mktemp -d /var/tmp/XXXXXXXXX )

PARTSIZE=30M

VGNAME=testvg
MDNAME=testmd
LVNAME=lv

# just the disk name as 'sda', without '/dev/'
DISKNAME=$( echo $LMI_STORAGE_DISK | sed 's!.*/!!' )

rlPhaseStartTest "Setup"
    rlLogInfo "Create partitions"
    rlRun "$LMI storage partition-table create --gpt $LMI_STORAGE_DISK"
    rlRun "$LMI storage partition create $LMI_STORAGE_DISK $PARTSIZE"
    rlRun "$LMI storage partition create $LMI_STORAGE_DISK $PARTSIZE"
    rlRun "$LMI storage partition create $LMI_STORAGE_DISK"

    rlLogInfo "Create MD RAID"
    rlRun "$LMI storage raid create --name=$MDNAME 0 ${LMI_STORAGE_DISK}1 ${LMI_STORAGE_DISK}2"

    rlLogInfo "Create VG"
    rlRun "$LMI storage vg create $VGNAME $MDNAME ${LMI_STORAGE_DISK}3"

    rlLogInfo "Create LVs"
    rlRun "$LMI storage lv create $VGNAME ${LVNAME}1 $PARTSIZE"
    rlRun "$LMI storage lv create $VGNAME ${LVNAME}2 $PARTSIZE"

    rlLogInfo "Create filesystems"
    rlRun "$LMI storage fs create xfs ${LVNAME}1"
    rlRun "$LMI storage fs create ext4 ${LVNAME}2"
rlPhaseEnd

function check_part1()
{
    prefix=$1
    rlAssertGrep "$prefix.*\"${LMI_STORAGE_DISK}1\",\"${DISKNAME}1\",\"$PARTSIZE\",\"software RAID\"" $rlRun_LOG
}

function check_part2()
{
    prefix=$1
    rlAssertGrep "$prefix.*\"${LMI_STORAGE_DISK}2\",\"${DISKNAME}2\",\"$PARTSIZE\",\"software RAID\"" $rlRun_LOG
}

function check_part3()
{
    prefix=$1
    rlAssertGrep "$prefix.*\"${LMI_STORAGE_DISK}3\",\"${DISKNAME}3\",\".*\",\"physical volume (LVM)\"" $rlRun_LOG
}

function check_md()
{
    prefix=$1
    rlAssertGrep "\"$prefix/dev/disk/by-id/md-name-.*:$MDNAME\",\"/dev/md/$MDNAME\",\"$MDNAME\",\".*\",\"physical volume (LVM)\"" $rlRun_LOG
}

function check_lv1()
{
    prefix=$1
    rlAssertGrep "\"$prefix/dev/disk/by-id/dm-name-$VGNAME-${LVNAME}1\",\"/dev/mapper/$VGNAME-${LVNAME}1\",\"${LVNAME}1\",\".*M\",\"xfs\"" $rlRun_LOG
}

function check_lv2()
{
    prefix=$1
    rlAssertGrep "\"$prefix/dev/disk/by-id/dm-name-$VGNAME-${LVNAME}2\",\"/dev/mapper/$VGNAME-${LVNAME}2\",\"${LVNAME}2\",\".*M\",\"ext4\"" $rlRun_LOG
}

function check_disk()
{
    prefix=$1
    rlAssertGrep "$prefix.*\"$LMI_STORAGE_DISK\",\"$DISKNAME\",\".*\",\"GPT partition table\"" $rlRun_LOG
}

function check_vg()
{
    prefix=$1
    rlAssertGrep "\"${prefix}LMI:VG:$VGNAME\",\"$VGNAME\",\"$VGNAME\",\".*\",\"volume group (LVM)\"" $rlRun_LOG
}

rlPhaseStartTest "lmi storage list"
    rlRun -s "$LMI -NHL csv storage list"
    check_disk ""
    check_part1 ""
    check_part2 ""
    check_part3 ""
    check_md ""
    check_lv1 ""
    check_lv2 ""
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "lmi storage depends"
    rlRun -s "$LMI -NHL csv storage depends ${LVNAME}1"
    check_vg
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage depends --deep ${LVNAME}1"
    check_disk ""
    check_part1 ""
    check_part2 ""
    check_part3 ""
    check_md ""
    check_vg
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage depends $MDNAME"
    check_part1
    check_part2
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage depends --deep $MDNAME"
    check_disk ""
    check_part1 ""
    check_part2 ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage depends ${DISKNAME}1"
    check_disk
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage depends --deep ${DISKNAME}1"
    check_disk ""
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "lmi storage provides"
    rlRun -s "$LMI -NHL csv storage provides ${DISKNAME}"
    check_part1 ""
    check_part2 ""
    check_part3 ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides --deep ${DISKNAME}"
    check_part1 ""
    check_part2 ""
    check_part3 ""
    check_md ""
    check_vg ""
    check_lv1 ""
    check_lv2 ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides ${DISKNAME}1"
    check_md ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides --deep ${DISKNAME}1"
    check_md ""
    check_vg ""
    check_lv1 ""
    check_lv2 ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides ${MDNAME}"
    check_vg
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides --deep ${MDNAME}"
    check_vg ""
    check_lv1 ""
    check_lv2 ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides ${VGNAME}"
    check_lv1 ""
    check_lv2 ""
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage provides --deep ${VGNAME}"
    check_lv1 ""
    check_lv2 ""
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "lmi storage tree"
    rlRun -s "$LMI -NHL csv storage tree ${MDNAME}"
    check_vg "└─"
    check_lv1 "  ├─"
    check_lv2 "  └─"
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage tree ${DISKNAME}1"
    check_md  "└─"
    check_vg  "  └─"
    check_lv1 "    ├─"
    check_lv2 "    └─"
    rm $rlRun_LOG

    rlRun -s "$LMI -NHL csv storage tree ${DISKNAME}"
    check_part1  "├─"
    check_part2  "├─"
    check_part3  "└─"
    check_md     "│ └─"
    check_vg     "│   └─"
    check_lv1    "│     ├─"
    check_lv2    "│     └─"
    rm $rlRun_LOG
rlPhaseEnd

rlPhaseStartTest "Cleanup"
    rlLogInfo "Delete filesystems"
    rlRun "$LMI storage fs delete ${LVNAME}1"
    rlRun "$LMI storage fs delete ${LVNAME}2"

    rlLogInfo "Delete LVs"
    rlRun "$LMI storage lv delete ${LVNAME}1"
    rlRun "$LMI storage lv delete ${LVNAME}2"

    rlLogInfo "Delete VG"
    rlRun "$LMI storage vg delete $VGNAME"

    rlLogInfo "Delete MD RAID"
    rlRun "$LMI storage raid delete $MDNAME"

    rlLogInfo "Delete partitions"
    rlRun "$LMI storage partition delete ${LMI_STORAGE_DISK}1 ${LMI_STORAGE_DISK}2 ${LMI_STORAGE_DISK}3"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
