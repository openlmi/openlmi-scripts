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

EXIT_CODE_UNSATISFIED=5
DEFAULT_VERSION='0.4.2'

# Set the full test name
TEST="openlmi-scripts/test/test_versioning"

# Package being tested
PACKAGE="openlmi-scripts"

function cmp2int() {
    digits=( `echo $1 | tr '.' ' '` )
    result=0
    for i in `seq 0 $((${#digits[@]} - 1))`; do
        result=$((result*100))
        result=$((result + ${digits[$i]}))
    done
    echo $result
}

rlJournalStart

if [[ -z "${LMI_SOFTWARE_PROVIDER_VERSION}" ]]; then
    msg="No version specified for OpenLMI-Software. Defaulting to "
    msg+="{$DEFAULT_VERSION}."
    rlLogInfo "$msg"
    LMI_SOFTWARE_PROVIDER_VERSION="${DEFAULT_VERSION}"
elif [[ "$LMI_SOFTWARE_PROVIDER_VERSION" == none ]]; then
    LMI_SOFTWARE_PROVIDER_VERSION=''
fi
if [[ -z "${LMI_HARDWARE_PROVIDER_VERSION}" ]]; then
    msg="No version specified for OpenLMI-Hardware Defaulting to "
    msg+="{$DEFAULT_VERSION}."
    rlLogInfo "$msg"
    LMI_HARDWARE_PROVIDER_VERSION="${DEFAULT_VERSION}"
elif [[ "$LMI_SOFTWARE_PROVIDER_VERSION" == none ]]; then
    LMI_HARDWARE_PROVIDER_VERSION=''
fi

rlPhaseStartSetup
    rlLogInfo "Creating temporary python sandbox"
    sandbox=`mktemp -d`
    export PYTHONPATH="$sandbox"
    pushd ..
    rlLogInfo "Installing lmi meta-command"
    rlRun "python setup.py develop --install-dir=$sandbox"
    popd
    rlLogInfo "Installing testing command"
    pushd cmdver
    rlRun "python setup.py develop --install-dir=$sandbox"
    popd
    export "$sandbox:$PATH"
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test help on select command"

    rlRun -s "$LMI_ help"
    rlAssertEquals "Check the number of subcommands available." \
        `grep '^\s\+[[:alnum:]-]\+\s\+-\s\+' $rlRun_LOG | wc -l` 4
    rlAssertGrep '\<ver\>\s\+-\s\+Command for testing version dependencies\.$' \
        $rlRun_LOG
    rlAssertGrep '\<ver-hw\s\+-\s\+This is a short description for CmdverHw\.$' \
        $rlRun_LOG
    rlAssertGrep '\<ver-sw\s\+-\s\+This is a short description for CmdverSw\.$' \
        $rlRun_LOG
    rm $rlRun_LOG

    rlRun -s "$LMI help ver"
    rlAssertGrep "^Command for testing version dependencies.$" $rlRun_LOG
    rlAssertGrep "^Usage:$" $rlRun_LOG
    rlAssertGrep "^\s\+lmi ver (sw\\|hw) \[<args>\.\.\.\]$'" $rlRun_LOG
    rm $rlRun_LOG

    if [[ -z "$LMI_SOFTWARE_PROVIDER_VERSION" ]]; then
        rlRun -s "$LMI help ver-sw" $EXIT_CODE_UNSATISFIED
        rlAssertGrep "error\s*:\s\+Profile and class dependencies were not satisfied for" \
            $rlRun_LOG
        rm $rlRun_LOG

        rlRun -s "$LMI help ver sw" $EXIT_CODE_UNSATISFIED
        rlAssertGrep "error\s*:\s\+Profile and class dependencies were not satisfied for" \
            $rlRun_LOG
        rm $rlRun_LOG

    else
        rlRun -s "$LMI help ver-sw"
        rlAssertGrep "^Software testing command.$" $rlRun_LOG
        rlAssertGrep "Usage: lmi ver-sw" $rlRun_LOG
        rm $rlRun_LOG

        rlRun -s "$LMI help ver sw" 0
        rlAssertGrep "^Software testing command.$" $rlRun_LOG
        rlAssertGrep "Usage: lmi ver sw" $rlRun_LOG
        rm $rlRun_LOG
    fi

    if [[ -z "$LMI_HARDWARE_PROVIDER_VERSION" ]]; then
        rlRun -s "$LMI help ver-hw"
        rlAssertGrep "^Hardware testing command\.$" $rlRun_LOG
        rlAssertGrep "^Usage: lmi ver-hw <cmd>$" $rlRun_LOG
        rm $rlRun_LOG

        rlRun -s "$LMI help ver hw"
        rlAssertGrep "^Hardware testing command\.$" $rlRun_LOG
        rlAssertGrep "^Usage: lmi ver hw <cmd>$" $rlRun_LOG
        rm $rlRun_LOG

    else
        rlRun -s "$LMI help ver-hw"
        rlAssertGrep "^Hardware testing command\.$" $rlRun_LOG
        rlAssertGrep "^Usage:$" $rlRun_LOG
        rlAssertGrep "^\s\+lmi ver-hw system$" $rlRun_LOG
        rlAssertGrep "^\s\+lmi ver-hw hostname$" $rlRun_LOG
        rm $rlRun_LOG

        rlRun -s "$LMI help ver hw" 0
        rlAssertGrep "^Hardware testing command.$" $rlRun_LOG
        rlAssertGrep "^Usage:$" $rlRun_LOG
        rlAssertGrep "^\s\+lmi ver hw system$" $rlRun_LOG
        rlAssertGrep "^\s\+lmi ver hw hostname$" $rlRun_LOG
        rm $rlRun_LOG

        rlRun -s "$LMI help ver hw system" 0
        rlAssertGrep "^Hardware testing command.$" $rlRun_LOG
        rlAssertGrep "^Usage:$" $rlRun_LOG
        rlAssertGrep "^\s\+lmi ver hw system$" $rlRun_LOG
        rlAssertGrep "^\s\+lmi ver hw hostname$" $rlRun_LOG
        rm $rlRun_LOG
    fi

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test software testing command"

    if [[ -z "$LMI_SOFTWARE_PROVIDER_VERSION" ]]; then
        rlRun -s "$LMI ver-sw" $EXIT_CODE_UNSATISFIED
        rlAssertGrep "Profile and class dependencies were not satisfied" \
            $rlRun_LOG
        rm $rlRun_LOG

    elif [[ `cmp2int $LMI_SOFTWARE_PROVIDER_VERSION` -lt `cmp2int 0.4.2` ]]; then

        rlRun -s "$LMI ver-sw"
        rlAssertGrep "Prov version.*${LMI_SOFTWARE_PROVIDER_VERSION} (PRE 0.4.2)" $rlRun_LOG
        rm $rlRun_LOG

    elif [[ `cmp2int $LMI_SOFTWARE_PROVIDER_VERSION` == `cmp2int 0.4.2` ]]; then
        rlRun -s "$LMI ver-sw"
        rlAssertGrep "Prov version.*${LMI_SOFTWARE_PROVIDER_VERSION} (VER 0.4.2)" $rlRun_LOG
        rm $rlRun_LOG

    else
        rlRun -s "$LMI ver-sw"
        rlAssertGrep "Prov version.*${LMI_SOFTWARE_PROVIDER_VERSION} (DEVEL)" $rlRun_LOG
        rm $rlRun_LOG
    fi

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test hardware testing command"

    if [[ -z "$LMI_HARDWARE_PROVIDER_VERSION" ]]; then
        for cmd in "system" "hostname"; do
            rlRun -s "$LMI ver-hw $cmd"
            rlAssertEquals "Printed table has just 2 rows" \
                `cat $rlRun_LOG | wc -l` 2
            rlAssertGrep "^Given command\s\+$cmd$" $rlRun_LOG
            rlAssertGrep "^Prov version\s\+N/A" $rlRun_LOG
            rm $rlRun_LOG
        done

    else
        if [[ `cmp2int $LMI_HARDWARE_PROVIDER_VERSION` -lt `cmp2int 0.4.2` ]]; then
            ver_suffix=' (PRE 0.4.2)'
        else
            ver_suffix=''
        fi
        for cmd in "system" "hostname"; do
            rlRun -s "$LMI ver-hw $cmd"
            rlAssertEquals "Printed table has just 2 rows" \
                `cat $rlRun_LOG | wc -l` 2
            rlAssertGrep "^Prov version\s\+$LMI_SOFTWARE_PROVIDER_VERSION$ver_suffix\$" \
                $rlRun_LOG
            if [[ $cmd == system ]]; then
                reg="^Chassis Type\s\+.*"
            else
                reg="^Hostname\s\+$HOSTNAME" $rlRun_LOG
            fi
            rm $rlRun_LOG
        done
    fi

rlPhaseEnd

rlPhaseStartCleanup
    rlLogInfo "Removing temporary python sandbox"
    rm -rf "$sandbox"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
