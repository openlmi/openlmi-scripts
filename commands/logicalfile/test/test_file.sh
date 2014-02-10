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
TEST="openlmi-scripts/test/test_file.sh"

# Package being tested
PACKAGE="openlmi-scripts-logicalfile"

function list_dir() {
    # Generate the same output as `lmi file list <path>` should do
    declare -a column_sizes
    declare -a data
    path="$1"
    [ "$path" == '/' ] || path+=/
    data[$((line_no++))]="Type@Mode@Current SELinux Context@Name"
    while IFS=  read col_name; do
        column_sizes[$((col_index++))]=${#col_name}
    done < <(echo "${data[0]}" | tr '@' '\n')

    while IFS=  read line; do
        if [[ "$line" == EOF ]]; then
            for i in `seq 0 $((${#data[@]} - 1))`; do
                IFS=@ read ft fm sl fn <<<"${data[i]}"
                printf "%-*s %-*s %-*s %s\n" \
                    ${column_sizes[0]} "$ft" \
                    ${column_sizes[3]} "$fn" \
                    ${column_sizes[1]} "$fm" \
                    "$sl"
            done
            break
        fi

        file_type=${line:0:1}
        if [[ $file_type == 'd' ]]; then
            file_type=Dir
        else
            file_type=`echo ${file_type^^} | tr '-' 'F'`
        fi
        [ ${column_sizes[0]:-0} -lt ${#file_type} ] && column_sizes[0]=${#file_type}

        file_mode=${line:1:3}
        [ ${column_sizes[1]:-0} -lt ${#file_mode} ] && column_sizes[1]=${#file_mode}

        selinux=`echo $line | cut -d \  -f 4`
        [ ${column_sizes[2]:-0} -lt ${#selinux} ] && column_sizes[2]=${#selinux}

        file_name="$path$(echo $line | cut -d \  -f 5)"
        [ ${column_sizes[3]:-0} -lt ${#file_name} ] && column_sizes[3]=${#file_name}

        data[$((line_no++))]="$file_type@$file_mode@$selinux@$file_name"

    done < <(ls -la -Z "$1" | tail -n +3; echo EOF)

    unset column_sizes data path file_type file_mode selinux file_name \
        line_no col_index
}

rlJournalStart

rlPhaseStartSetup
    rlLogInfo "Creating temporary python sandbox"
    sandbox=`mktemp -d`
    export PYTHONPATH="$sandbox"
    pushd ../../..
    rlLogInfo "Installing lmi meta-command"
    rlRun "python setup.py develop --install-dir=$sandbox" 0
    popd
    pushd ..
    rlLogInfo "Installing file subcommand"
    rlRun "python setup.py develop --install-dir=$sandbox" 0
    popd
    export PATH="$sandbox:$PATH"
rlPhaseEnd


rlPhaseStartTest
    rlLogInfo "Test list directory"

    for directory in / /usr /usr/lib; do
        list_dir_tmp_out=`mktemp list_dirXXXX`
        rlRun -s "$LMI file list $directory" 0
        list_dir "$directory" > $list_dir_tmp_out
        rlAssertNotDiffer $list_dir_tmp_out $rlRun_LOG
        rm $rlRun_LOG $list_dir_tmp_out
    done

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test create and delete non-ascii directory"

    list_dir_tmp_out=`mktemp list_dirXXXX`
    temp_dir=`mktemp -d`
    dir="$temp_dir/ěščřžýáíé"
    if [ -e $dir ]; then
        rm -rf $dir
    fi

    rlRun -s "$LMI file list $temp_dir" 0
    list_dir "$temp_dir" > $list_dir_tmp_out
    rlAssertNotDiffer $list_dir_tmp_out $rlRun_LOG
    rm $rlRun_LOG

    rlRun "$LMI file createdir $dir" 0
    rlRun "[ -d $dir ]" 0
    rlRun -s "$LMI file list $temp_dir" 0
    list_dir $temp_dir > $list_dir_tmp_out
    rlAssertGrep "$dir" $list_dir_tmp_out
    rlAssertNotDiffer $list_dir_tmp_out $rlRun_LOG
    rm $rlRun_LOG

    rlRun "$LMI file deletedir $dir" 0
    rlRun "[ -e $dir ]" 1
    rlRun -s "$LMI file list $temp_dir" 0
    list_dir $temp_dir > $list_dir_tmp_out
    rlAssertNotGrep "$dir" $list_dir_tmp_out
    rlAssertNotDiffer $list_dir_tmp_out $rlRun_LOG

    rm -rf $list_dir_tmp_out $temp_dir $rlRun_LOG

rlPhaseEnd

rlPhaseStartCleanup
    rlLogInfo "Removing temporary python sandbox"
    rm -rf "$sandbox"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
