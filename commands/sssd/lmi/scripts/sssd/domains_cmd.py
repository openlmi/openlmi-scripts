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
SSSD service management.

Usage:
    %(cmd)s list [(--enabled | --disabled)]
    %(cmd)s show <domain>
    %(cmd)s enable <domain>
    %(cmd)s disable <domain>


Commands:
    list        Prints all domains managed by SSSD.
    show        Prints information about provided domain.
    enable      Enable domain in SSSD. SSSD needs to be restarted in order for
                this command to take effect.
    disable     Disable domain in SSSD.  SSSD needs to be restarted in order for
                this command to take effect.
    
List options:
    --enabled   List only enabled domains.
    --disabled  List only disabled domains.
"""

from lmi.scripts.common import command
from lmi.scripts import sssd

class List(command.LmiLister):
    COLUMNS = ('Name', 'Enabled', 'Debug Level', 'ID Provider')

    def execute(self, ns,  _enabled, _disabled):
        kind = 'all'
        if _enabled:
            kind = 'enabled'
        elif _disabled:
            kind = 'disabled'

        for s in sorted(sssd.list_backends(ns, kind), key=lambda i: i.Name):
            yield (s.Name, s.IsEnabled, sssd.debug_level(s.DebugLevel),
                   sssd.get_provider(ns, 'id_provider', s))
            
class Show(command.LmiShowInstance):
    DYNAMIC_PROPERTIES = True
    
    def execute(self, ns, domain):
        for backend in ns.LMI_SSSDBackend.instances():
            if backend.Name == domain and not backend.IsEnabled:
                columns = (
                    'Name',
                    ('Enabled', 'IsEnabled'))
                return columns, backend

        columns = (
            'Name',
            ('Enabled', lambda i: True),
            ('ID Provider', 'Provider'),
            ('Primary servers', lambda i: ', '.join(i.PrimaryServers)),
            ('Backup servers', lambda i: ', '.join(i.BackupServers)),
            ('Subdomains', lambda i: sssd. \
                                list_subdomains_comma_separated(ns, i)),
            ('Parent domain', 'ParentDomain'),
            'Realm',
            'Forest',
            ('Enumerable', 'Enumerate'),
            ('Minimum ID value', 'MinId'),
            ('Maximum ID value', 'MaxId'),
            ('Use fully qualified names', 'UseFullyQualifiedNames'),
            ('Fully qualified name format', 'FullyQualifiedNameFormat'),
            ('Login expression', 'LoginFormat'))
        return columns, sssd.get_domain(ns, domain)
    
class Enable(command.LmiCheckResult):
    CALLABLE = sssd.enable_backend
    EXPECT = 0
    
class Disable(command.LmiCheckResult):
    CALLABLE = sssd.disable_backend
    EXPECT = 0
    
class DomainCommands(command.LmiCommandMultiplexer):
    COMMANDS = {
            'list'    : List,
            'show'    : Show,
            'enable'  : Enable,
            'disable' : Disable
    }
    OWN_USAGE = __doc__
