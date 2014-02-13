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
TEST="openlmi-scripts/test/test_imode.sh"

# Package being tested
PACKAGE="openlmi-scripts"

function run_and_compare_output() {
    # Run lmi command and compare its output to a contents of given file.
    #
    # Args:
    #   command  - command to run which is executed in subshell
    #   expected - file name with expected output stored in imode without
    #              extension
    rlRun -s "$1" 0
    rlRun -l "cmp imode/$2.out $rlRun_LOG" 0
    rm $rlRun_LOG
}

function run_test_command() {
    # Run command in interactive mode with expect script
    # `imode/run_test_cmd.exp`. Command is run iteratively from different
    # command namespaces. stderr is redirected to /dev/null when running
    # the `command`.
    #
    # Args:
    #   command  - command path (without `lmi` prefix)
    #   expected - path to a file with expected output
    #   dir...   - command namespaces to nest to before running command
    #
    # Common prefix of `command` and current namespace is removed from command
    # in each iteration before running it.
    cmd="$1"
    expected_output="$2"
    shift 2
    while [ $# -gt 0 ]; do
        dir="$1"
        cmd_="${cmd#$dir }"
        out_file=`mktemp out_fileXXXX`
        prompt='lmi> '
        path="$(echo $dir | tr ' ' '/')"
        [ "$dir" = '.' ] || prompt=">$(echo $dir | sed 's/\([^ ]\+ \)/>/g')> "
        rlRun "expect imode/run_test_cmd.exp $out_file \"$path\" \"$prompt\" \"$cmd_\"" 0
        rlAssertNotDiffer $expected_output $out_file
        rm $out_file
        shift
    done
}

function make_error_message() {
    # Args:
    #   level   - one of debug, info, warn, error, critical
    #   message
    level=$1
    message="$2"
    [ "$level" = 'warn' ] && level=warning
    case "$level" in
        warning)  color='\x1b[38;5;11m'; ;;
        error)    color='\x1b[38;5;9m'; ;;
        critical) color='\x1b[38;5;13m'; ;;
        *)        unset color; ;;
    esac
    if [[ -n "$color" ]]; then
        printf "$color%-8s:\x1b[39m %s\n" $level "$message"
    else
        echo "$message"
    fi
}

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
    rlLogInfo "Try to import lmi meta-command"
    rlRun 'python -c "import lmi.scripts._metacommand"' 0
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test exit command"
    rlRun "expect imode/exit.exp" 0
    rlRun "expect imode/exit.exp 0" 0
    rlRun "expect imode/exit.exp 1" 1
    rlRun "expect imode/exit.exp 2" 2
    rlRun "expect imode/exit.exp 10" 10
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test end of file"
    rlRun "expect imode/eof.exp" 0
    rlRun "expect imode/eof.exp ':pwd' '/lmi'" 0
    errmsg=`make_error_message error 'No such subcommand \"foo\".'`
    rlRun "expect imode/eof.exp ':cd foo' \"$errmsg\"" 0
    rlRun "expect imode/empty_lines.exp" 0
    run_and_compare_output "$LMI < imode/empty_lines.txt" empty_lines
rlPhaseEnd

rlPhaseStartSetup
    rlLogInfo "Installing testing command"
    pushd subcmd
    rlRun "python setup.py develop --install-dir=$sandbox"
    popd
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Check whether test command is installed"
    run_and_compare_output "$LMI help 2>/dev/null" lmi_test_help
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test nesting to subcommands"
    rlRun "expect imode/cd_test.exp" 1
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test help messages in interactive mode"
    run_and_compare_output "echo help | $LMI" "help"
    run_and_compare_output "echo help help | $LMI" "help_help"
    run_and_compare_output "echo \": help\" | $LMI" "builtin_help"
    run_and_compare_output "echo help exit | $LMI 2>/dev/null" "help_exit"
    run_and_compare_output "echo help test | $LMI 2>/dev/null" "help_test"
    run_and_compare_output "$LMI 2>/dev/null < imode/test_help_exit.txt" \
        "help_exit"
    run_and_compare_output "$LMI 2>/dev/null < imode/test_help.txt" \
        "test_help"
    run_and_compare_output "$LMI 2>/dev/null < imode/test_builtin_help.txt" \
        "builtin_help"
    run_and_compare_output "$LMI 2>/dev/null < imode/test_help_list.txt" \
        "test_help_list"
    run_and_compare_output "$LMI 2>/dev/null < imode/test_help_show.txt" \
        "test_help_show"
    run_and_compare_output "echo help foo | $LMI" "help_foo"

    rlLogInfo "Test --help"
    outfile=`mktemp outfileXXXX`
    expected=`mktemp expectedXXXX`
    rlRun "expect imode/run_test_cmd.exp $outfile . 'lmi> ' 'test --help'" 0
    rlAssertNotDiffer imode/test_opt_help.out $outfile

    rlRun "expect imode/run_test_cmd.exp $outfile . 'lmi> ' 'test list --help'" 0
    rlAssertNotDiffer imode/test_list_opt_help.out $outfile

    cmd="test list pkgs --help"
    rlRun "expect imode/run_test_cmd.exp $outfile . 'lmi> ' '$cmd'" 0
    rlAssertNotDiffer imode/test_list_opt_help.out $outfile

    cmd="test show --help"
    rlRun "expect imode/run_test_cmd.exp $outfile . 'lmi> ' '$cmd'" 0
    rlAssertNotDiffer imode/test_opt_help.out $outfile

    cmd="test foo --help"
    rlRun "expect imode/run_test_cmd.exp $outfile . 'lmi> ' '$cmd'" 0
    rlAssertNotDiffer imode/test_opt_help.out $outfile

    cmd="list --help"
    sed 's/^    test /    /' imode/test_list_opt_help.out >$expected
    rlRun "expect imode/run_test_cmd.exp $outfile test '>test> ' '$cmd'" 0
    rlAssertNotDiffer $expected $outfile

    cmd="list pkgs --help"
    rlRun "expect imode/run_test_cmd.exp $outfile test '>test> ' '$cmd'" 0
    rlAssertNotDiffer $expected $outfile

    cmd="show --help"
    rlRun "expect imode/run_test_cmd.exp $outfile test '>test> ' '$cmd'" 0
    rlAssertNotDiffer imode/test_opt_help.out  $outfile

    rm $expected $outfile

rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Test completion in interactive mode"
    # this also tests exit command nested in subcommand (with 20 as argument)
    rlRun "expect imode/completion.exp" 20
    rlRun "expect imode/complete_builtin.exp" 0
rlPhaseEnd

rlPhaseStartTest
    rlLogInfo "Check behaviour of test subcommand"

    rlLogInfo \
        "First create files in non-interactive mode we will then compare to"
    rlRun -s "$LMI test list pkgs 2>/dev/null" 0
    rlAssertEquals "List of all packages is sane" \
        `grep -E '^(tog-pegasus|pywbem|hwdata|python-docopt)' $rlRun_LOG | wc -l` 4
    all_packages=`mktemp all_packagesXXXX`
    mv $rlRun_LOG $all_packages

    rlRun -s "$LMI test list pkgs --installed 2>/dev/null" 0
    rlAssertEquals "List of installed packages is sane"\
        `grep -E '^(pywbem|hwdata)' $rlRun_LOG | wc -l` 2
    installed_packages=`mktemp installed_packagesXXXX`
    mv $rlRun_LOG $installed_packages

    rlRun -s "$LMI test list repos 2>/dev/null" 0
    rlAssertEquals "List of repositories is sane" \
        `grep -E '^(fedora|updates)' $rlRun_LOG | wc -l` 2
    all_repos=`mktemp all_reposXXXX`
    mv $rlRun_LOG $all_repos

    rlRun -s "$LMI test show pkg hwdata 2>/dev/null" 0
    rlAssertEquals "Package description is sane" \
        `grep -E '^(Name|Arch|Installed)' $rlRun_LOG | wc -l` 3
    one_package=`mktemp one_packageXXXX`
    mv $rlRun_LOG $one_package

    rlLogInfo "Now compare outputs to interactive mode"

    run_test_command 'test list pkgs'  $all_packages \
        '.' 'test' 'test list'
    run_test_command 'test list pkgs --installed' $installed_packages \
        '.' 'test' 'test list'
    run_test_command 'test list repos' $all_repos \
        '.' 'test' 'test list'
    run_test_command 'test show pkg hwdata' $one_package \
        '.' 'test'

    rm $all_packages $installed_packages $all_repos $one_package

rlPhaseEnd

rlPhaseStartCleanup
    rlLogInfo "Removing temporary python sandbox"
    rm -rf "$sandbox"
rlPhaseEnd

rlJournalPrintText
rlJournalEnd
