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
TEST="openlmi-scripts/test/test_logging.sh"

# Package being tested
PACKAGE="openlmi-scripts"

# array of supported log levels
LEVELS=( critical error warn info debug )

DEBUG_CONFIG_TEMPLATE="
[Main]
Trace = True
Verbosity = 2

[Log]
Level = DEBUG
LogToConsole = True
FileFormat = %%(levelname)s: %%(message)s
OutputFile = %s
"

rlJournalStart

rlPhaseStartSetup
    rlLogInfo "Creating temporary python sandbox"
    sandbox=`mktemp -d`
    export PYTHONPATH="$sandbox"
    pushd ..
    rlLogInfo "Installing lmi meta-command"
    rlRun "python setup.py develop --install-dir=$sandbox" 0
    popd
    pushd subcmd
    rlRun "python setup.py develop --install-dir=$sandbox" 0
    popd
    export PATH="$sandbox:$PATH"
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test logging with default settings"

    LMICMD="$LMI -c logging/defaults.conf"

    stdout=`mktemp stdoutXXXX`
    stderr=`mktemp stderrXXXX`
    rlRun "$LMICMD test log all >$stdout 2>$stderr" 0
    rlAssertNotDiffer logging/log_all_default.stdout $stdout
    rlAssertNotDiffer logging/log_all_warn.stderr $stderr

    rlRun "$LMICMD test log all --with-traceback >$stdout 2>$stderr" 0
    rlAssertNotDiffer logging/log_all_default.stdout $stdout
    tmpout=`mktemp tmpoutXXXX`
    grep '^\(warning\|error\|critical\)' $stderr > $tmpout
    rlAssertNotDiffer logging/log_all_warn.stderr $tmpout
    rlAssertEquals "Correct number of exceptions were raised" 3 \
        `grep '^RuntimeError: S\*\*t happens!' $stderr | wc -l`
    rm $tmpout

    expected_out=`mktemp expected_stdoutXXXX`
    expected_err=`mktemp expected_stderrXXXX`
    for verbosity in 0 1 2; do
        if [[ $verbosity -gt 0 ]]; then
            option=`printf -- "-v %.0s" $(seq $verbosity)`
        else
            option=''
        fi
        CMD="$LMICMD $option test log level"
        for level in `seq 0 $((${#LEVELS[@]} - 1))`; do
            rlRun "$CMD --${LEVELS[$level]} >$stdout 2>$stderr" 0
            level_name=${LEVELS[$level]}
            log_level_name=$level_name
            [ $level_name = warn ] && log_level_name=warning
            ( \
                if [ $verbosity = 2 ]; then \
                    echo 'Running command "test".'; \
                    echo 'Found registered command "test".'; \
                fi; \
                echo -n 'warning : Command "lmi.scripts.cmdtest.Show"'; \
                echo -n " is missing usage string. It will be"; \
                echo " inherited from parent command."; \
                if [ $verbosity = 2 ]; then \
                    for opt_name in '_with_traceback' '_lmi_failed'; do \
                        echo -n "Option \"$opt_name\" not handled in function"; \
                        echo ' "level", ignoring.'; \
                    done; \
                    echo "Connected to $HOSTNAME"; \
                fi; \
                if [ $(($verbosity + 2)) -ge $level ]; then \
                    if [ $level -lt 3 ]; then \
                        printf "%-8s: " $log_level_name; \
                    fi; \
                    echo "This is $level_name message."; \
                fi \
            ) >$expected_err
            rlAssertNotDiffer $expected_err $stderr
            rlAssertEquals "Nothing is written to stdout" 0 `cat $stdout | wc -c`
        done
    done

    rm $stdout $stderr $expected_out $expected_err

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test logging with debug settings"

    config_file=`mktemp configXXXX`
    log_file=`mktemp log_fileXXXX`
    printf "$DEBUG_CONFIG_TEMPLATE" $log_file >$config_file

    LMICMD="$LMI -c $config_file"

    stdout=`mktemp stdoutXXXX`
    stderr=`mktemp stderrXXXX`
    filter_debug=" | grep -v '^Option' > $stderr"
    rlRun "$LMICMD test log all 2>&1 >$stdout $filter_debug" 0
    rlAssertNotDiffer logging/log_all_debug.stdout $stdout
    rlAssertNotDiffer logging/log_all_debug.stderr $stderr
    cat $log_file | grep -v '^DEBUG: Option' >${log_file}.tmp
    mv ${log_file}{.tmp,}
    rlAssertNotDiffer logging/log_all_debug.file $log_file
    rm $log_file

    rlRun "$LMICMD test log all --with-traceback 2>&1 >$stdout $filter_debug" 0
    rlAssertNotDiffer logging/log_all_debug.stdout $stdout
    tmpout=`mktemp tmpoutXXXX`
    grep '^\(warning\|error\|critical\)' $stderr > $tmpout
    rlAssertNotDiffer logging/log_all_warn.stderr $tmpout
    rlAssertEquals "Correct number of exceptions were raised" 5 \
        `grep '^RuntimeError: S\*\*t happens!' $stderr | wc -l`
    rlAssertEquals "Correct number of exceptions were raised" 5 \
        `grep '^RuntimeError: S\*\*t happens!' $log_file | wc -l`
    rm $tmpout $log_file

    rlLogInfo "Try override log-file"
    new_log_file=`mktemp new_log_fileXXXX`
    rlRun "$LMICMD --log-file $new_log_file test log all 2>&1 >$stdout $filter_debug" 0
    rlAssertNotDiffer logging/log_all_debug.stdout $stdout
    rlAssertNotDiffer logging/log_all_debug.stderr $stderr
    cat $new_log_file | grep -v '^DEBUG: Option' >${new_log_file}.tmp
    mv ${new_log_file}{.tmp,}
    rlAssertNotDiffer logging/log_all_debug.file $new_log_file
    rlRun "[ -e $log_file ]" 1 "Log file from config file shall not be written"
    
    [ -e $new_log_file ] && rm $new_log_file
    [ -e $log_file ] && rm $log_file

    rlLogInfo "Try to disable logging to a file"
    rlRun "$LMICMD --log-file '' test log all 2>&1 >$stdout $filter_debug" 0
    rlAssertNotDiffer logging/log_all_debug.stdout $stdout
    rlAssertNotDiffer logging/log_all_debug.stderr $stderr
    rlRun "[ -e $log_file ]" 1 "Log file from config file shall not be written"
    [ -e $log_file ] && rm $log_file

    rlLogInfo "Try override verbosity"
    rlRun "$LMICMD -q test log all 2>&1 >$stdout $filter_debug" 0
    rlAssertNotDiffer logging/log_all_silent.stdout $stdout
    rlAssertNotDiffer logging/log_all_error.stderr $stderr
    cat $log_file | grep -v '^DEBUG: Option' >${log_file}.tmp
    mv ${log_file}{.tmp,}
    rlAssertNotDiffer logging/log_all_debug.file $log_file
    rm $log_file

    rlRun "$LMICMD -v test log all >$stdout 2>$stderr" 0
    rlAssertNotDiffer logging/log_all_info.stdout $stdout
    rlAssertNotDiffer logging/log_all_info.stderr $stderr
    cat $log_file | grep -v '^DEBUG: Option' >${log_file}.tmp
    mv ${log_file}{.tmp,}
    rlAssertNotDiffer logging/log_all_debug.file $log_file
    rm $log_file

    rlLogInfo "Change file log level"
    sed -i 's/DEBUG/WARNING/' $config_file
    rlAssertGrep 'Level = WARNING' $config_file
    rlRun "$LMICMD test log all 2>&1 >$stdout $filter_debug" 0
    rlAssertNotDiffer logging/log_all_debug.stdout $stdout
    rlAssertNotDiffer logging/log_all_debug.stderr $stderr
    rlAssertNotDiffer logging/log_all_warn.file $log_file
    [ -e $log_file ] && rm $log_file

    rlLogInfo "Disable logging to console"
    sed -i 's/\(LogToConsole.*\)True/\1False/' $config_file
    rlAssertGrep 'LogToConsole = False' $config_file
    rlRun "$LMICMD test log all >$stdout 2>$stderr" 0
    rlAssertNotDiffer logging/log_all_debug.stdout $stdout
    rlAssertEquals "Nothing is written to stderr" `cat $stderr | wc -c` 0
    rlAssertNotDiffer logging/log_all_warn.file $log_file
    [ -e $log_file ] && rm $log_file

    rlLogInfo "Override tracing"
    rlRun "$LMICMD --notrace test log all >$stdout 2>$stderr" 0
    rlAssertNotDiffer logging/log_all_debug_notrace.stdout $stdout
    rlAssertEquals "Nothing is written to stderr" `cat $stderr | wc -c` 0
    rlAssertNotDiffer logging/log_all_warn.file $log_file

    for f in $log_file $new_log_file $config_file $stdout $stderr; do
        [ -e $f ] && rm $f
    done

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test logging with settings"

    stdout=`mktemp stdoutXXXX`
    stderr=`mktemp stderrXXXX`
    rlRun "$LMI -c logging/defaults.conf test log all >$stdout 2>$stderr" 0
    rlAssertNotDiffer $stdout logging/log_all_default.stdout
    rlAssertNotDiffer $stderr logging/log_all_warn.stderr
    rm $stdout $stderr
rlPhaseEnd


rlPhaseStartCleanup
    rlLogInfo "Removing temporary python sandbox"
    rm -rf "$sandbox"
rlPhaseEnd
