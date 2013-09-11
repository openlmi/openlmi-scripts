#!/bin/bash

# prints possible commands
# one per line
# parse lmi help
re_command="^[[:blank:]]*([[:alnum:]]+)[[:blank:]]*-"
while IFS= read line; do
    if [[ $line =~ $re_command ]]; then
        printf '%s\n' "${BASH_REMATCH[1]}"
    fi
done < <(lmi help 2>/dev/null)
