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

GROUP=$LMI_ACCOUNT_GROUP
USER=$LMI_ACCOUNT_USER
USERS=$(for i in $(seq -w 10); do echo ${USER}$i; done)

GROUP_GID=9999

RESERVED_THRESHOLD=1000

rlJournalStart

rlPhaseStartSetup
    # add test user, without group and home
    for i in $USERS; do
        useradd -N -M $i
    done
rlPhaseEnd


rlPhaseStartTest "Test creation of non-reserved group"
    rlLogInfo "Create non-reserved group"
    rlRun "$LMI group create $GROUP"

    rlLogInfo "Check that '/etc/group' shows it"
    rlAssertGrep "^$GROUP:" /etc/group

    rlLogInfo "Check that 'lmi group list' shows it"
    rlRun -s "$LMI -L csv -N group list"
    rlAssertGrep "\"$GROUP\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that 'lmi group list $GROUP' shows it"
    rlRun -s "$LMI -L csv -N group list $GROUP"
    rlAssertGrep "\"$GROUP\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that 'lmi group list root' does not show it"
    rlRun -s "$LMI -L csv -N group list root"
    rlAssertNotGrep "\"$GROUP\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that GID is non-reserved"
    gid=`grep </etc/group "^$GROUP:" | cut -f 3 -d ':'`
    rlAssertGreaterOrEqual "group is non-reserved" "$gid" $RESERVED_THRESHOLD

    rlLogInfo "Remove the group"
    rlRun "$LMI group delete $GROUP"

    rlLogInfo "Check that 'lmi group list $GROUP' does not show it"
    rlRun -s "$LMI -L csv -N group list $GROUP" 1
    rlAssertNotGrep "\"$GROUP\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that '/etc/group' does not show it"
    rlAssertNotGrep "^$GROUP:" /etc/group
rlPhaseEnd

rlPhaseStartTest "Test creation of reserved group"
    rlLogInfo "Create reserved group"
    rlRun "$LMI group create --reserved $GROUP"

    rlLogInfo "Check that GID is reserved"
    gid=`grep </etc/group "^$GROUP:" | cut -f 3 -d ':'`
    rlAssertGreater "group is reserved" $RESERVED_THRESHOLD "$gid"

    rlLogInfo "Remove the group"
    rlRun "$LMI group delete $GROUP"
rlPhaseEnd


rlPhaseStartTest "Test creation of group with specific GID"
    rlLogInfo "Create group with gid=$GROUP_GID"
    rlRun "$LMI group create --gid=$GROUP_GID $GROUP"

    rlLogInfo "Check that GID is correct"
    gid=`grep </etc/group "^$GROUP:" | cut -f 3 -d ':'`
    rlAssertEquals "gid" $GROUP_GID "$gid"

    rlLogInfo "Remove the group"
    rlRun "$LMI group delete $GROUP"
rlPhaseEnd


rlPhaseStartTest "Test adding/removing users"
    rlLogInfo "Create group"
    rlRun "$LMI group create $GROUP"

    rlLogInfo "Sequentially add users to the group"
    for i in `seq -w 10`; do
        # check the user is not in the group (yet)
        usr="$USER$i"
        rlRun -s "$LMI -L csv -N group listuser $GROUP"
        rlAssertNotGrep $usr $rlRun_LOG
        rm $rlRun_LOG

        # add the user
        rlRun "$LMI group adduser $GROUP $usr"

        # check _all_ the previous users + this one are in the group
        rlRun -s "$LMI -L csv -N group listuser $GROUP"
        for j in `seq -w $i`; do
            usr="$USER$j"
            rlAssertGrep $usr $rlRun_LOG
            rlAssertGrep "^$GROUP:.*:[^:]*\<$USER$j\>[^:]*\$" /etc/group
        done
        rm $rlRun_LOG
    done

    rlLogInfo "Sequentially delete users from the group"
    for i in `seq -w 10 | tac`; do
        # check _all_ the previous users + this one are in the group
        rlRun -s "$LMI -L csv -N group listuser $GROUP"
        for j in `seq -w $i`; do
            usr="$USER$j"
            rlAssertGrep $usr $rlRun_LOG
            rlAssertGrep "^$GROUP:.*:[^:]*\<$USER$j\>[^:]*\$" /etc/group
        done
        rm $rlRun_LOG

        usr="$USER$i"
        # delete the user
        rlRun "$LMI group removeuser $GROUP $usr"

        # check the user is deleted
        rlRun -s "$LMI -L csv -N group listuser $GROUP"
        rlAssertNotGrep $usr $rlRun_LOG
        rm $rlRun_LOG
    done

    rlLogInfo "Remove the group"
    rlRun "$LMI group delete $GROUP"
rlPhaseEnd

rlPhaseStartTest "Test listing"
    # store 'lmi group list' output
    rlRun -s "$LMI -L csv -N group list"
    GROUP_LIST=$rlRun_LOG
    # and check it with /etc/group
    glist=`cut -f 1 -d ':' /etc/group`
    for gname in $glist; do
        #check gid
        gid=`grep </etc/group "^$gname:" | cut -f 3 -d ':'`
        rlAssertGrep "^\"$gname\",\"$gid\"" $GROUP_LIST

        # check all members
        rlRun -s "$LMI -L csv -N group listuser $gname"
        members=`grep </etc/group "^$gname:" | cut -f 4 -d ':' | sed 's/,/\n/g'`
        for usr in $members; do
            rlAssertGrep "\b$usr\b" $rlRun_LOG '-P'
        done
        rm $rlRun_LOG
    done
    rm $GROUP_LIST
rlPhaseEnd


rlPhaseStartCleanup
    # remove any stray group
    groupdel $GROUP
    for i in $USERS; do
        userdel $i
    done

rlPhaseEnd

rlJournalPrintText
rlJournalEnd
