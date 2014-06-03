# SSSD Providers
#
# Copyright (C) 2013-2014 Red Hat, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
# Authors: Pavel Brezina <pbrezina@redhat.com>
#
"""
SSSD system service management.

Usage:
    %(cmd)s status
    %(cmd)s restart [--try]
    %(cmd)s set-debug-level <level> [--until-restart] [options]
    %(cmd)s domain (--help | <cmd> [<args> ...])
    %(cmd)s service (--help | <cmd> [<args> ...])


Commands:
    status           Prints SSSD service's status.
    restart          Restarts the SSSD service.
    set-debug-level  Set debug level of selected (all by default) components.
    service          Manage supported services.
    domain           Manage SSSD domains.
    
Restart options:
    --try         Whether to abandon the operation if the service
                  is not running.
                  
Set-debug-level options:
    --until-restart
                  Set the debug level but switch it to original
                  value when SSSD is restarted.
    --all         Select all components (default)
    --monitor     Select the SSSD monitor.
    --services=svc,...
                  Comma separated list of SSSD services.
    --domains=dom,...
                  Comma separated list of SSSD domains.
"""

from lmi.scripts.common import command
from lmi.scripts import service as srv
from lmi.scripts import sssd
from lmi.scripts.sssd.services_cmd import ServiceCommands
from lmi.scripts.sssd.domains_cmd import DomainCommands

class Status(command.LmiShowInstance):

    DYNAMIC_PROPERTIES = True

    def execute(self, ns):
        columns = (
                ('Name', lambda i: srv.RE_SUFFIX.sub('', i.Name)),
                'Caption',
                ('Enabled', lambda i: srv.get_enabled_string(ns, i)),
                ('Status', lambda i: srv.get_status_string(ns, i)))

        return columns, srv.get_service(ns, 'sssd')

class Restart(command.LmiCheckResult):
    CALLABLE = srv.restart_service
    EXPECT = 0

    def transform_options(self, options):
        """
        ``try`` is a keyword argument in python, let's rename it to
        ``just-try`` which will be transformed into ``just_try``.
        """
        options['just-try'] = options.pop('--try')
        options['service'] = 'sssd'
        
class SetDebugLevel(command.LmiCheckResult):
    OPT_NO_UNDERSCORES = True
    EXPECT = 0
    
    def execute(self, ns, level,
                until_restart=False,
                all=True,
                monitor=False,
                services=None,
                domains=None):
        components = []
        if services is not None:
            components.extend(services.split(','))
        if domains is not None:
            components.extend(domains.split(','))
        if monitor:
            components.append('monitor')
        return sssd.set_debug_level(ns, level, until_restart, components)
    
SSSD = command.register_subcommands(
        'SSSD', __doc__,
        { 'status'              : Status
        , 'restart'             : Restart
        , 'set-debug-level'     : SetDebugLevel
        , 'service'             : ServiceCommands
        , 'domain'              : DomainCommands
        },
    )
