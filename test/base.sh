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
# Authors: Jan Safranek <jsafrane@redhat.com>
# Authors: Michal Minar <miminar@redhat.com>

# Basic framework for all 'lmi' tests.
# It is based on Beakerlib, https://fedorahosted.org/beakerlib/

. /usr/share/beakerlib/beakerlib.sh

LMI_CIMOM_URL=${LMI_CIMOM_URL:-kvm-rhel7}
LMI_CIMOM_USERNAME=${LMI_CIMOM_USERNAME:-root}
LMI_CIMOM_PASSWORD=${LMI_CIMOM_PASSWORD:-redhat}

SCHEMA=$(echo $LMI_CIMOM_URL | sed -n 's!^\([[:alpha:]]\+://\).*!\1!p')
HOSTNAME=$(echo $LMI_CIMOM_URL | sed -e 's!^.*//!!' -e 's!/.*!!')
LMI="lmi"
[ -n "$HOSTNAME" ] && \
    LMI+=" -n -h $SCHEMA$LMI_CIMOM_USERNAME:$LMI_CIMOM_PASSWORD@$HOSTNAME"
export LMI
