# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
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
# Author: Tomas Smetana <tsmetana@redhat.com>
#
"""
Manage AD or Kerberos domain membership.

Usage:
    %(cmd)s [show]
    %(cmd)s join -u <user> [-p <password>] -d <domain>
    %(cmd)s leave -u <user> [-p <password>] -d <domain>

Commands:
    show         Show joined domain.
    join         Join the given domain.
    leave        Leave the given domain.

Options:
    -u, --user      The username to be used when authenticating to the domain.
    -p, --password  Optional password for the authentication. If omitted you
                    will be prompted for one.
    -d, --domain    The domain to be joined/left.
"""

from lmi.scripts.common import command

class Show(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = 'lmi.scripts.realmd:show'

class Join(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = 'lmi.scripts.realmd:join'

class Leave(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = 'lmi.scripts.realmd:leave'

Realmd = command.register_subcommands(
        'Realmd', __doc__,
        { 'show'         : Show
        , 'join'         : Join
        , 'leave'        : Leave
        },
        fallback_command=Show
    )
