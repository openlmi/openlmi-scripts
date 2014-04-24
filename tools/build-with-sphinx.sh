#!/bin/bash
# This script creates a temporary python workspace directory, where the
# openlmi-scripts and all specified commands are installed in order for
# sphinx-build to successfuly find them and generate devel documentation out of
# them.
#
# There are several environment variables affecting the execution:
#   * SPHINXBUILD
#           sphinx binary generating the documentation
#   * SRCDIR
#           directory with sources
#   * REQUIRED_COMMANDS  list of commands that shall be installed before
#                        this command separated with commas

SPHINXBUILD=${SPHINXBUILD:-sphinx-build}
SRCDIR="${SRCDIR:-.}"
REQUIRED_COMMANDS="${REQUIRED_COMMANDS:-}"
tmp=`mktemp -d`
export PYTHONPATH=$tmp
pushd "$SRCDIR"
echo "$REQUIRED_COMMANDS" | while IFS=,  read cmd; do
    [ -z "$cmd" ] && continue
    pushd ../$cmd
    python setup.py develop --install-dir=$tmp || exit 1
    popd
done
python setup.py develop --install-dir=$tmp || exit 1
popd  # ..
echo "Running: ${SPHINXBUILD} $@"
${SPHINXBUILD} "$@" || exit 1
rm -rf $tmp
