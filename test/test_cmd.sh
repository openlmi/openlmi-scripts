#!/bin/bash
#
# Copyright (c) 2014, Red Hat, Inc. All rights reserved.
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
# Authors: Michal Minar <miminar@redhat.com>

. ./base.sh

# Set the full test name
TEST="openlmi-scripts/test/test_lmi.sh"

# Package being tested
PACKAGE="openlmi-scripts"

# for some tests no other options are not welcomed
LMI_=`echo $LMI | cut -d \  -f 1`

rlJournalStart

rlPhaseStartSetup
    rlLogInfo "Creating temporary python sandbox"
    sandbox=`mktemp -d`
    export PYTHONPATH="$sandbox"
    pushd ..
    rlLogInfo "Installing lmi meta-command"
    rlRun "python setup.py develop --install-dir=$sandbox" 0
    popd
    export "$sandbox:$PATH"
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test help messages without subommands"

    rlRun -s "$LMI_ --help" 0
    rlAssertGrep "^Usage:$"    $rlRun_LOG
    rlAssertGrep "^Options:$"  $rlRun_LOG
    rlAssertGrep "^Commands:$" $rlRun_LOG
    rlAssertGrep "^    help$"  $rlRun_LOG
    rlRun "head -n 1 $rlRun_LOG | grep -q '[[:alpha:]]\+'" 0 \
        "Test whether first line is not blank"
    rm $rlRun_LOG

    rlRun -s "$LMI help" 0
    rlAssertNotDiffer "cmd/help_without_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI help foo" 0
    rlAssertNotDiffer "cmd/help_foo.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI help help" 0
    rlAssertNotDiffer "cmd/help_help.out" $rlRun_LOG
    rm $rlRun_LOG

rlPhaseEnd

rlPhaseStartSetup
    rlLogInfo "Installing testing command"
    pushd subcmd
    rlRun "python setup.py develop --install-dir=$sandbox"
    popd
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test help messages with test subcommand"

    rlRun -s "$LMI_ --help" 0
    rlAssertGrep "^Usage:$"         $rlRun_LOG
    rlAssertGrep "^Options:$"       $rlRun_LOG
    rlAssertGrep "^Commands:$"      $rlRun_LOG
    rlAssertGrep "^    help test$"  $rlRun_LOG
    rlRun "head -n 1 $rlRun_LOG | grep -q '[[:alpha:]]\+'" 0 \
        "Test whether first line is not blank"
    rm $rlRun_LOG

    rlRun -s "$LMI help 2>/dev/null" 0
    rlAssertNotDiffer "cmd/help_with_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI help test 2>/dev/null" 0
    rlAssertNotDiffer "cmd/help_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI test --help 2>/dev/null" 0
    rlAssertNotDiffer "cmd/help_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI test list --help 2>/dev/null" 0
    rlAssertNotDiffer "cmd/help_test_list.out" $rlRun_LOG
    rm $rlRun_LOG

rlPhaseEnd

rlPhaseStartCleanup
    rlLogInfo "Removing temporary python sandbox"
    rm -rf "$sandbox"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
