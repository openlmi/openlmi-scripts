#
# Copyright (C) 2013 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Roman Rakus <rrakus@redhat.com>
#
# Bash completion for LMI commands

_lmi() {
    local helpers_path="lmi-bash-completion"
    if ! [[ -e "$helpers_path" ]]; then
        helpers_path="/usr/libexec/$helpers_path"
    fi
    local options=(-c --config-file -h --host --hosts-file --user -v --trace -q --quiet -n --noverify --same-credentials --help --version)
    local current="${COMP_WORDS[$COMP_CWORD]}"
    local previous="${COMP_WORDS[COMP_CWORD-1]}"
    local commands=( $($helpers_path/print_possible_commands.sh) )
    local used_command=

    for (( i=1; i < ${#COMP_WORDS[@]} - 1 && i < $COMP_CWORD; i++ )); do
        for (( ci=0; ci < ${#commands[@]}; ci++ )); do
            if [[ ${COMP_WORDS[$i]} == ${commands[$ci]} ]]; then
                used_command=${commands[$ci]}
                break 2;
            fi
        done
    done

    if [[ $used_command ]]; then
        # Check if we have completion executable for command
        if [[ -x $helpers_path/commands/"_$used_command" ]] ; then
            # pass the rest of words typed as parameters
            COMPREPLY=( $($helpers_path/commands/_$used_command "${COMP_WORDS[@]:$((i+1))}") )
        else
            # commands without completion - filename completion
            COMPREPLY=( $(compgen -f -- "$current") )
        fi
    else
        case $current in
            -*) COMPREPLY=( $(compgen "-W ${options[*]}" -- "$current" ) );;
            *) case $previous in
                 -c|--config-file|--hosts-file) COMPREPLY=( $(compgen -f -- "$current" ) );;
                 -h|--host) COMPREPLY=( $(compgen -A hostname -- "$current" ) );;
                 --user) COMPREPLY=( $(compgen -u -- "$current" ) );;
                 --help|--version) ;;
                 *) COMPREPLY=( $(compgen "-W ${commands[*]}" -- "$current" ) );;
               esac
        esac
    fi
}

complete -F _lmi lmi
