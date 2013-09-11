#!/bin/bash

#
# Helper script to generate developer documentation in
# doc/modules and api.rst
#

TOPDIR=..

[ -e $TOPDIR/doc/modules ] || mkdir $TOPDIR/doc/modules

function get_modules() {
    find $TOPDIR/lmi/scripts/ -type f -a -name '*.py' | \
        sed 's:/__init__\.py$::' | \
        grep -v "^${TOPDIR}/lmi/scripts/\?$" | \
        grep -v '/_' | \
        sort -u
}

function get_module_name() {
    path=`sed -e "s:^.*${TOPDIR}/lmi/scripts/\(.*\)$:\1:" -e "s:/:.:g"`
    basename -s .py "$path"
}

function get_version_string() {
    out=`python $TOPDIR/setup.py --version`
    git_version=`git describe HEAD 2>/dev/null`
    echo -n "\`\`$out\`\`"
    if [ -n "$git_version" ]; then
        echo ", git: \`\`$git_version\`\`"
    fi
}

# api.rst header
cat >$TOPDIR/doc/api.rst <<_EOF_
OpenLMI Scripts API
===================

This is a generated documentation form *OpenLMI Scripts* sources.

Developer of script library will be interested in
:py:mod:\`lmi.scripts.common\` package providing useful functionality to
script development.

Generated from version: $(get_version_string)

Contents:

.. toctree::
    :maxdepth: 2

_EOF_

# Generate modules/*.rst
for module_path in `get_modules`; do
    module=`echo "$module_path" | get_module_name`
    out=$module.rst
    len=`echo $module| wc -c`
    len=$(($len-1))
    underline=""
    for i in `seq $len`; do underline="=$underline"; done

    cat >$TOPDIR/doc/modules/$out  <<_EOF_
$module
$underline
.. automodule:: lmi.scripts.$module
    :members:
_EOF_
    echo >>$TOPDIR/doc/api.rst "    modules/$module"
done
