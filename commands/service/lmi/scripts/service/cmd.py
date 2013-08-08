# Copyright (c) 2013, Red Hat, Inc. All rights reserved.
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
#
"""
System service management.

Usage:
    %(cmd)s list [--all | --disabled | --oneshot]
    %(cmd)s show <service>
    %(cmd)s start <service>
    %(cmd)s stop <service>
    %(cmd)s restart <service>

Commands:
    list        Prints a list of services. Only enabled services are
                printed at default.
    show        Show detailed information about service.
    start       Starts a service.
    stop        Stops the service.
    restart     Restarts the service.

Options:
    --all       List all services available.
    --disabled  List only disabled services.
    --oneshot   List only oneshot services.
"""

from lmi.scripts.common import command

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.service:list'
    COLUMNS = ('Name', "Started", 'Status')

    def transform_options(self, options):
        for opt in ('all', 'disabled', 'oneshot'):
            # let's remove underscores to make the interface pretty
            options[opt] = options.pop('--'+opt)

class Start(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.service:start'
    EXPECT = 0

class Stop(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.service:stop'
    EXPECT = 0

class Restart(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.service:restart'
    EXPECT = 0

class Show(command.LmiShowInstance):
    CALLABLE = 'lmi.scripts.service:get_instance'
    PROPERTIES = (
            'Name',
            'Caption',
            ('Enabled', lambda i: i.EnabledDefault == 2),
            ('Active', lambda i: i.Started),
            ('Status', lambda i: i.Status))

Service = command.register_subcommands(
        'Service', __doc__,
        { 'list'    : Lister
        , 'show'    : Show
        , 'start'   : Start
        , 'stop'    : Stop
        , 'restart' : Restart
        },
    )
