#!/bin/bash
# This script needs to be run from openlmi-scripts/man directory. It creates a
# man page in current directory for lmi meta-command. It's generated from lmi's
# help message and from the configuration file.
# Requirements:
#  * lmi meta-command needs to be installed and on PATH.

dest=${1:-lmi.1}
usage_file=`mktemp`
options_file=`mktemp`
configuration_file=`mktemp`

# states:
#   desc - parse description
#   wusg - wait for usage
#   pusg - parse usage
#   wopt - wait for options
#   popt - parse options
state="desc"
re_option="^([[:blank:]]+)((-[-[:alpha:]_]+)"
re_option+="(\ [][:alpha:]<>_()[|-]+)*)(\ \ +(.*))?"
DESCRIPTION=

if ! which "lmi" >/dev/null 2>&1; then
    echo "Please install lmi meta-command first!" >&2
    exit 1
fi

while IFS= read line; do
    case "$state" in
        "desc")
            if [[ "$line" =~ ^[[:blank:]]*$ ]] && [ -n "$DESCRIPTION" ]; then
                state="wusg"
            else
                [ -n "$DESCRIPTION" ] && DESCRIPTION+=" "
                DESCRIPTION+="$line"
            fi
            ;;

        "wusg")
            if [[ "$line" =~ ^[Uu]sage: ]]; then
               state="pusg0"
               printf ".nf\n" >$usage_file
            fi
            ;;

        pusg*)
            if [[ "$line" =~ ^[[:blank:]]*$ ]]; then
                state="wopt"
                printf ".fi\n" >>$usage_file
            else
                usg_count=`echo $state | sed 's/^pusg\([[:digit:]]\+\)/\1/'`
                if [ "$usg_count" = 0 ]; then
                    spaces=`echo "$line" | sed 's/^\(\s\+\).*/\1/' | wc -c`
                elif [ $spaces -lt `echo "$line" | sed 's/^\(\s\+\).*/\1/' | wc -c` ];
                then
                    indented=true
                    printf ".RS\n" >>$usage_file
                elif $indented; then
                    indented=false
                    printf ".RE\n" >>$usage_file
                fi
                printf ".B " >>$usage_file
                echo "$line" >>$usage_file
                #echo "$line" | sed -e 's/^\s\+//' -e 's/\s\+$//' >>$usage_file
                state="pusg$((usg_count+1))"
            fi
            ;;

        "wopt")
            if [[ "$line" =~ ^[Oo]ption ]]; then
               state="popt0"
            fi
            ;;

        popt*)
            if [[ "$line" =~ ^[[:blank:]]*$ ]]; then
                printf "\n"
                break
            elif [[ "$line" =~ $re_option ]]; then
                opt_count=`echo $state | sed 's/^popt\([[:digit:]]\+\)/\1/'`
                [ "$opt_count" -gt 0 ] && printf '\n'
                printf ".TP\n.I ${BASH_REMATCH[2]}\n"
                printf -- "${BASH_REMATCH[5]}" | sed -e 's/^\s\+//' -e 's/\s\+$//'
                state="popt$((opt_count+1))"
            else
                printf " "
                printf "$line" | sed -e 's/^\s\+//' -e 's/\s\+$//'
            fi
            ;;

        *)  break
            ;;

    esac
done < <( lmi --help ) >$options_file;

# states:
#   wsct - wait for the first section
#   psct - parsing the section
#   pdsc - parsing description of section
state="wsct"
re_sct_start="^\[([[:alpha:]]+)\]"
re_opt_desc="^#(\s+(.*)|$)"
re_opt_value="^#?([[:alpha:]]+)\s*=\s*(.*)"
while IFS= read line; do
    case $state in
        "wsct")
            if [[ "$line" =~ $re_sct_start ]]; then
                state="psct"
                printf ".TP\n.B ${BASH_REMATCH[1]} Section\n"
            fi
            ;;

        "psct")
            if [[ "$line" =~ $re_opt_desc ]]; then
                state="pdsc"
                DESCRIPTION="${BASH_REMATCH[2]}"
            elif [[ "$line" =~ $re_sct_start ]]; then
                printf ".TP\n.B ${BASH_REMATCH[1]} Section\n"
            fi
            ;;

        "pdsc")
            if [[ "$line" =~ $re_opt_value ]]; then
                state="psct"
                #DESCRIPTION="${DESCRIPTION} ${BASH_REMATCH[2]}"
                printf ".RS 4\n.TP 4\n.B ${BASH_REMATCH[1]}\n"
                if [ -n "${BASH_REMATCH[2]}" ]; then
                   echo "Default:"
                   echo ".B ${BASH_REMATCH[2]}"
                   printf ".IP\n"
                fi
                echo "${DESCRIPTION}"
                printf ".RE\n"
            elif [[ "$line" =~ $re_opt_desc ]]; then
                DESCRIPTION="${DESCRIPTION} ${BASH_REMATCH[2]}"
            elif [[ $line =~ ^$ ]]; then
                state="psct"
            fi
            ;;

    esac
done < ../config/lmi.conf >$configuration_file

DATE=`LC_ALL="en_US.utf8" date '+%B %Y'`
VERSION=`lmi --version`

cat >$dest <<EOF
.TH lmi 1 "${DATE}" "openlmi-scripts ${VERSION}" "User Commands"

.SH NAME
lmi \- meta-command for managing systems with OpenLMI providers
.SH SYNOPSIS
EOF

cat $usage_file >>$dest
rm $usage_file

cat >>$dest << EOF
.SH DESCRIPTION
${DESCRIPTION}
.SH OPTIONS
EOF

cat $options_file >>$dest
rm $options_file

cat >>$dest <<EOF
.SH CONFIGURATION
There is a system-wide configuration file located at
\`/etc/openlmi/lmi.conf\` and user configuration file searched at \`~/.lmirc\`.
File path of the later can also be specified with
.B --config-file
option. Options in user configuration overrides system-wide.

The configuration consists of sections, led by a
.B [section]
header and followed by
.B name: value
entries. Comments are prefixed with
.B #
or
.B ;
.PP
Please refer to
.B RFC 822
for more details on this format. Follows a list of possible configuration
options with leading section names.
EOF

cat $configuration_file >>$dest
rm $configuration_file

cat >>$dest <<EOF
.SH AUTHORS
.LP
Michal Minar <miminar@redhat.com>
EOF
