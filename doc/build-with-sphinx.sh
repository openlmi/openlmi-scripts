#!/bin/bash
# This script creates a temporary python workspace directory, where the
# openlmi-scripts and all specified commands are installed in order for
# sphinx-build to successfuly find them and generate devel documentation out of
# them.
#
# There are several environment variables affecting the execution:
#   * SPHINXBUILD
#           sphinx binary generating the documentation
#   * INCLUDE_COMMANDS
#           whether the command should be included in generated documentation
#   * COMMANDS
#           list of subcommands to include

SPHINXBUILD=${SPHINXBUILD:-sphinx-build}
INCLUDE_COMMANDS=${INCLUDE_COMMANDS:-1}
tmp=`mktemp -d`
pushd ..
export PYTHONPATH=$tmp
python setup.py develop --install-dir=$tmp || exit 1
if [ "$INCLUDE_COMMANDS" == 1 ]; then
    pushd commands
    COMMANDS="$1"
    for cmd in ${COMMANDS}; do
        pushd $cmd
        python setup.py develop --install-dir=$tmp || exit 1
        popd
    done
    popd
fi
popd  # ..
shift
${SPHINXBUILD} $@ || exit 1
rm -rf $tmp
