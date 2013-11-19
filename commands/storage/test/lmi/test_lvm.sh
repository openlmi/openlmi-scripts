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


# 'lmi vg' and 'lmi lv' test.
# - create vg
# - check that 'lmi vg list + show' shows it
# - create lvs on it
# - check that 'lmi lv list + show' shows it
# - delete the lvs
# - delete the vg

. ./base.sh

EXTENT_SIZE=1024K
VGNAME=mytest
LVNAME1=mylv1
LVSIZESPEC1=10M
LVSIZE1=10M
LVNAME2=mylv2
LVSIZE2=20M
LVSIZESPEC2=20E

rlJournalStart

rlPhaseStartTest "CreateVG"
    rlLogInfo "Creating a VG with specific extent size"
    rlRun "$LMI vg create --extent-size=$EXTENT_SIZE $VGNAME ${PARTITIONS[*]}"

    rlLogInfo "Check that the VG exists"
    rlRun -s "vgs --noheading -o vg_name"
    rlAssertGrep $VGNAME $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check VG has all PVs"
    rlRun -s "pvs --noheading -o pv_name"
    for part in ${PARTITIONS[*]}; do
        rlAssertGrep $part $rlRun_LOG
    done
    rm $rlRun_LOG

    rlLogInfo "Check lmi vg list shows it"
    rlRun -s "$LMI -N -H -L csv vg list"
    rlAssertGrep "\"LMI:VG:$VGNAME\"" $rlRun_LOG
    rlAssertGrep "\"$VGNAME\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi vg show shows it"
    rlRun -s "$LMI -N -H -L csv vg show"
    rlAssertGrep "\"InstanceID\",\"LMI:VG:$VGNAME\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"$VGNAME\"" $rlRun_LOG
    rlAssertGrep "\"Extent Size\",\"1024K\"" $rlRun_LOG
    for part in ${PARTITIONS[*]}; do
        rlAssertGrep "Physical Volumes.*$part" $rlRun_LOG
    done
    rlAssertGrep '"Logical Volumes",""' $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd


rlPhaseStartTest "CreateLV"
    rlLogInfo "Creating LVs"
    rlRun "$LMI lv create $VGNAME $LVNAME1 $LVSIZESPEC1"
    rlRun "$LMI lv create $VGNAME $LVNAME2 $LVSIZESPEC2"

    rlLogInfo "Check that the LVs exist"
    rlRun -s "lvs --noheading -o lv_name"
    rlAssertGrep $LVNAME1 $rlRun_LOG
    rlAssertGrep $LVNAME2 $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi lv list shows them"
    rlRun -s "$LMI -N -H -L csv lv list $VGNAME"
    rlAssertGrep "\"/dev/disk/by-id/dm-name-$VGNAME-$LVNAME1\"" $rlRun_LOG
    rlAssertGrep "\"$LVNAME1\"" $rlRun_LOG
    rlAssertGrep "\"$LVSIZE1\"" $rlRun_LOG
    rlAssertGrep "\"/dev/disk/by-id/dm-name-$VGNAME-$LVNAME2\"" $rlRun_LOG
    rlAssertGrep "\"$LVNAME2\"" $rlRun_LOG
    rlAssertGrep "\"$LVSIZE2\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi lv show shows them"
    rlRun -s "$LMI -N -H -L csv lv show $LVNAME1"
    rlAssertGrep "\"DeviceID\",\"/dev/disk/by-id/dm-name-$VGNAME-$LVNAME1\"" $rlRun_LOG
    rlAssertGrep "\"Name\",\"/dev/mapper/$VGNAME-$LVNAME1\"" $rlRun_LOG
    rlAssertGrep "\"Volume Group\",\"$VGNAME\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"$LVNAME1\"" $rlRun_LOG
    rlAssertGrep "\"Total Size\",\"$LVSIZE1\"" $rlRun_LOG
    rlAssertGrep "\"Extent Size\",\"$EXTENT_SIZE\"" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI -N -H -L csv lv show $LVNAME2"
    rlAssertGrep "\"DeviceID\",\"/dev/disk/by-id/dm-name-$VGNAME-$LVNAME2\"" $rlRun_LOG
    rlAssertGrep "\"Name\",\"/dev/mapper/$VGNAME-$LVNAME2\"" $rlRun_LOG
    rlAssertGrep "\"Volume Group\",\"$VGNAME\"" $rlRun_LOG
    rlAssertGrep "\"ElementName\",\"$LVNAME2\"" $rlRun_LOG
    rlAssertGrep "\"Total Size\",\"$LVSIZE2\"" $rlRun_LOG
    rlAssertGrep "\"Extent Size\",\"$EXTENT_SIZE\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi vg show shows them"
    rlRun -s "$LMI -N -H -L csv vg show"
    rlAssertGrep "Logical Volumes.*$LVNAME1" $rlRun_LOG
    rlAssertGrep "Logical Volumes.*$LVNAME2" $rlRun_LOG

rlPhaseEnd


rlPhaseStartTest "DeleteLV"
    rlLogInfo "Deleting LVs"
    rlRun "$LMI lv delete $LVNAME1 $LVNAME2"

    rlLogInfo "Check that the LVs is deleted"
    rlRun -s "lvs --noheading -o lv_name"
    rlAssertNotGrep $LVNAME1 $rlRun_LOG
    rlAssertNotGrep $LVNAME2 $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi lv list doesn't show them"
    rlRun -s "$LMI -N -H -L csv lv list $VGNAME"
    rlAssertNotGrep "\"LMI:/dev/disk/by-id/dm-name-$VGNAME-$LVNAME1\"" $rlRun_LOG
    rlAssertNotGrep "\"$LVNAME1\"" $rlRun_LOG
    rlAssertNotGrep "\"$LVSIZE1\"" $rlRun_LOG
    rlAssertNotGrep "\"LMI:/dev/disk/by-id/dm-name-$VGNAME-$LVNAME2\"" $rlRun_LOG
    rlAssertNotGrep "\"$LVNAME2\"" $rlRun_LOG
    rlAssertNotGrep "\"$LVSIZE2\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi vg show doesn't show them"
    rlRun -s "$LMI -N -H -L csv vg show"
    rlAssertNotGrep "Logical Volumes.*$LVNAME1" $rlRun_LOG
    rlAssertNotGrep "Logical Volumes.*$LVNAME2" $rlRun_LOG
rlPhaseEnd


rlPhaseStartTest "DeleteVG"
    rlLogInfo "Delete the VG"
    rlRun "$LMI vg delete $VGNAME"

    rlLogInfo "Check that the VG is removed"
    rlRun -s "vgs --noheading -o vg_name"
    rlAssertNotGrep $VGNAME $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check lmi vg list does not show"
    rlRun -s "$LMI -N -L csv vg list"
    rlAssertNotGrep "\"LMI:VG:$VGNAME\"" $rlRun_LOG
    rlAssertNotGrep "\"$VGNAME\"" $rlRun_LOG
    rm $rlRun_LOG
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
