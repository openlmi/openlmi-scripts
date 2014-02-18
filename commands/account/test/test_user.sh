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

USER=$LMI_ACCOUNT_USER
USER_GID=1 # 'bin' group
USER_UID=9998

RESERVED_THRESHOLD=1000

rlJournalStart

rlPhaseStartSetup
rlPhaseEnd


rlPhaseStartTest "Test creation of non-reserved user"
    rlLogInfo "Create non-reserved user"
    rlRun "$LMI user create $USER"

    rlLogInfo "Check that '/etc/passwd' shows it"
    rlAssertGrep "^$USER:" /etc/passwd

    rlLogInfo "Check that '/etc/group' shows it"
    rlAssertGrep "^$USER:" /etc/group

    rlLogInfo "Check that 'lmi user list' shows it"
    rlRun -s "$LMI -L csv -N user list"
    rlAssertGrep "^\"$USER\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that 'lmi user show' shows it"
    rlRun -s "$LMI -L csv -N user show"
    rlAssertGrep "^\"$USER\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that 'lmi user show $USER' shows it"
    rlRun -s "$LMI -L csv -N user show $USER"
    rlAssertGrep "^\"$USER\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that 'lmi user show root' does not show it"
    rlRun -s "$LMI -L csv -N user show root"
    rlAssertNotGrep "^\"$USER\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that home exists"
    rlAssertExists /home/$USER

    rlLogInfo "Check that GID is non-reserved"
    gid=`grep </etc/group "^$USER:" | cut -f 3 -d ':'`
    rlAssertGreaterOrEqual "group is non-reserved" "$gid" $RESERVED_THRESHOLD

    rlLogInfo "Check that UID is non-reserved"
    uid=`grep </etc/passwd "^$USER:" | cut -f 3 -d ':'`
    rlAssertGreaterOrEqual "userid non-reserved" "$uid" $RESERVED_THRESHOLD

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"

    rlLogInfo "Check that 'lmi user show $USER' does not show it"
    rlRun -s "$LMI -L csv -N user show $USER" 1
    rlAssertNotGrep "\"$USER\"" $rlRun_LOG
    rm $rlRun_LOG

    rlLogInfo "Check that '/etc/passwd' does not show it"
    rlAssertNotGrep "^$GROUP:" /etc/passwd
    rlLogInfo "Check that '/etc/group' does not show it"
    rlAssertNotGrep "^$GROUP:" /etc/group
rlPhaseEnd

rlPhaseStartTest "Test creation of reserved user"
    rlLogInfo "Create reserved user"
    rlRun "$LMI user create -r $USER"

    rlLogInfo "Check that GID is non-reserved"
    gid=`grep </etc/group "^$USER:" | cut -f 3 -d ':'`
    rlAssertGreaterOrEqual "group is non-reserved" "$gid" $RESERVED_THRESHOLD

    rlLogInfo "Check that UID is reserved"
    uid=`grep </etc/passwd "^$USER:" | cut -f 3 -d ':'`
    rlAssertGreater "userid non-reserved" $RESERVED_THRESHOLD "$uid"

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"
rlPhaseEnd

rlPhaseStartTest "Test creation of user with specific UID"
    rlLogInfo "Create user with UID"
    rlRun "$LMI user create --uid=$USER_UID $USER"

    rlLogInfo "Check that GID is non-reserved"
    gid=`grep </etc/group "^$USER:" | cut -f 3 -d ':'`
    rlAssertGreaterOrEqual "group is non-reserved" "$gid" $RESERVED_THRESHOLD

    rlLogInfo "Check that UID is $USER_UID"
    uid=`grep </etc/passwd "^$USER:" | cut -f 3 -d ':'`
    rlAssertEquals "userid" $USER_UID "$uid"

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"
rlPhaseEnd

rlPhaseStartTest "Test creation of user with specific GID"
    rlLogInfo "Create user with GID"
    rlRun "$LMI user create --gid=$USER_GID $USER"

    rlLogInfo "Check that GID is non-reserved"
    gid=`grep </etc/passwd "^$USER:" | cut -f 4 -d ':'`
    rlAssertEquals "group" "$gid" $USER_GID

    rlLogInfo "Check that UID is non-reserved"
    uid=`grep </etc/passwd "^$USER:" | cut -f 3 -d ':'`
    rlAssertGreaterOrEqual "userid non-reserved" "$uid" $RESERVED_THRESHOLD

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"
rlPhaseEnd

rlPhaseStartTest "Test creation of user with specific UID and GID"
    rlLogInfo "Create user with UID and GID"
    rlRun "$LMI user create --gid=$USER_GID --uid=$USER_UID $USER"

    rlLogInfo "Check that GID is non-reserved"
    gid=`grep </etc/passwd "^$USER:" | cut -f 4 -d ':'`
    rlAssertEquals "group" "$gid" $USER_GID

    rlLogInfo "Check that UID is $USER_UID"
    uid=`grep </etc/passwd "^$USER:" | cut -f 3 -d ':'`
    rlAssertEquals "userid" $USER_UID "$uid"

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"
rlPhaseEnd

rlPhaseStartTest "Test creation of user with --directory, --gecos and --shell args"
    rlLogInfo "Create user with --dir, --gecos and --shell args"
    rlRun "$LMI user create -d /home/blabla -s /bin/bleble -c mygecos $USER"

    rlLogInfo "Check home"
    home=`grep </etc/passwd "^$USER:" | cut -f 6 -d ':'`
    rlAssertEquals "home" "$home" "/home/blabla"

    rlLogInfo "Check shell"
    shell=`grep </etc/passwd "^$USER:" | cut -f 7 -d ':'`
    rlAssertEquals "shell" "$shell" "/bin/bleble"

    rlLogInfo "Check gecos"
    shell=`grep </etc/passwd "^$USER:" | cut -f 5 -d ':'`
    rlAssertEquals "shell" "$shell" "mygecos"

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"
rlPhaseEnd

rlPhaseStartTest "Test creation of user without home and group"
    rlLogInfo "Create user without home and group"
    rlRun "$LMI user create -M -n $USER"

    rlLogInfo "Check home"
    home=`grep </etc/passwd "^$USER:" | cut -f 6 -d ':'`
    rlAssertEquals "home" "$home" "/home/$USER"

    rlLogInfo "Check that home does not exist"
    rlAssertNotExists /home/$USER

    rlLogInfo "Check the group does not exist"
    rlAssertNotGrep "^$USER" /etc/group

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete $USER"
rlPhaseEnd

rlPhaseStartTest "Test deletion of user without home and group"
    rlLogInfo "Create user"
    rlRun "$LMI user create $USER"

    rlLogInfo "Check home"
    home=`grep </etc/passwd "^$USER:" | cut -f 6 -d ':'`
    rlAssertEquals "home" "$home" "/home/$USER"

    rlLogInfo "Check that home exists"
    rlAssertExists /home/$USER

    rlLogInfo "Check the group exists"
    rlAssertGrep "^$USER" /etc/group

    rlLogInfo "Remove the user"
    rlRun "$LMI user delete --no-delete-home --no-delete-group $USER"

    rlLogInfo "Check that home still exists"
    rlAssertExists /home/$USER

    rlLogInfo "Check the group still exists"
    rlAssertGrep "^$USER" /etc/group

    rm -rf /home/$USER
    groupdel $USER
rlPhaseEnd

rlPhaseStartCleanup
    # remove any stray user
    userdel $USER
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
