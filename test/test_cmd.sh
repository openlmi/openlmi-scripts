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
TEST="openlmi-scripts/test/test_cmd.sh"

# Package being tested
PACKAGE="openlmi-scripts"

rlJournalStart

rlPhaseStartSetup
    rlLogInfo "Creating temporary python sandbox"
    sandbox=`mktemp -d`
    export PYTHONPATH="$sandbox"
    pushd ..
    rlLogInfo "Installing lmi meta-command"
    rlRun "python setup.py develop --install-dir=$sandbox" 
    popd
    export "$sandbox:$PATH"
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test help messages without subommands"

    rlRun -s "$LMI_ --help" 
    rlAssertGrep "^Usage:$"    $rlRun_LOG
    rlAssertGrep "^Options:$"  $rlRun_LOG
    rlAssertGrep "^Commands:$" $rlRun_LOG
    rlAssertGrep "^    help$"  $rlRun_LOG
    rlRun "head -n 1 $rlRun_LOG | grep -q '[[:alpha:]]\+'" 0 \
        "Test whether first line is not blank"
    rm $rlRun_LOG

    rlRun -s "$LMI help" 
    rlAssertNotDiffer "cmd/help_without_test.out" $rlRun_LOG
    rm $rlRun_LOG

    # suppress warning messages
    rlRun -s "$LMI -q help foo" 
    rlAssertNotDiffer "cmd/help_foo.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI help help" 
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

    rlRun -s "$LMI_ --help" 
    rlAssertGrep "^Usage:$"         $rlRun_LOG
    rlAssertGrep "^Options:$"       $rlRun_LOG
    rlAssertGrep "^Commands:$"      $rlRun_LOG
    rlAssertGrep "^    help test$"  $rlRun_LOG
    rlRun "head -n 1 $rlRun_LOG | grep -q '[[:alpha:]]\+'" 0 \
        "Test whether first line is not blank"
    rm $rlRun_LOG

    rlRun -s "$LMI help 2>/dev/null" 
    rlAssertNotDiffer "cmd/help_with_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI help test 2>/dev/null" 
    rlAssertNotDiffer "cmd/help_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI test --help 2>/dev/null" 
    rlAssertNotDiffer "cmd/help_test.out" $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI test list --help 2>/dev/null" 
    rlAssertNotDiffer "cmd/help_test_list.out" $rlRun_LOG
    rm $rlRun_LOG

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test the *no headings* option"
    with_headings=`mktemp with_headingsXXXX`
    without_headings=`mktemp without_headingsXXXX`
    expected_colonized=`mktemp expectedXXXX`

    rlRun -s "$LMI test show pkg hwdata >$with_headings"
    whl=`cat $with_headings | wc -l`
    rlRun -s "$LMI -N test show pkg hwdata >$without_headings"
    nhl=`cat $without_headings | wc -l`
    rlAssertEquals "Output without headings needs to be one line shorter" \
        $((whl - 1)) $nhl
    rlAssertGrep "Prop\s\+Value" $with_headings
    rlAssertNotGrep "Prop\s\+Value" $without_headings
    cat >$expected_colonized <<EOF
Name:hwdata
Architecture:noarch
Installed:True
EOF
    rlRun "sed -n -e '/^warning :/ d' -e '1 !s/\s\+/:/gp' $with_headings | cmp $expected_colonized -" 0 \
        "Compare the output to expected with reduced spaces"

    rlRun -s "$LMI test show repo fedora >$with_headings"
    whl=`cat $with_headings | wc -l`
    rlRun -s "$LMI -N test show repo fedora >$without_headings"
    nhl=`cat $without_headings | wc -l`
    rlAssertEquals "Output without headings needs to be one line shorter" \
        $((whl - 1)) $nhl
    rlAssertGrep    "^Name\s\+Enabled" $with_headings
    rlAssertNotGrep "^Name\s\+Enabled" $without_headings
    echo "fedora:True" >$expected_colonized
    rlRun "sed -n -e '/^warning :/ d' -e '1 !s/\s\+/:/gp' $with_headings | cmp $expected_colonized -" 0 \
        "Compare the output to expected with reduced spaces"

    rlRun -s "$LMI -v test show repo fedora >$with_headings"
    whl=`cat $with_headings | wc -l`
    rlRun -s "$LMI -v -N test show repo fedora >$without_headings"
    nhl=`cat $without_headings | wc -l`
    rlAssertEquals "Output without headings needs to be one line shorter" \
        $((whl - 1)) $nhl
    rlAssertGrep    "^Name\s\+Enabled\s\+Packages" $with_headings
    rlAssertNotGrep "^Name\s\+Enabled\s\+Packages" $without_headings
    sed -i '1 s/$/:1000/' $expected_colonized
    rlRun "sed -n -e '/^warning :/ d' -e '1 !s/\s\+/:/gp' $with_headings | cmp $expected_colonized -" 0 \
        "Compare the output to expected with reduced spaces"

    rm $with_headings $without_headings $expected_colonized
rlPhaseEnd

rlPhaseStartCleanup
    rlLogInfo "Removing temporary python sandbox"
    rm -rf "$sandbox"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
