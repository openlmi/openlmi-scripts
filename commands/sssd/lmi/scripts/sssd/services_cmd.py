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
    %(cmd)s show <service>
    %(cmd)s enable <service>
    %(cmd)s disable <service>


Commands:
    list        Prints all services supported by SSSD.
    show        Prints information about provided service.
    enable      Enable service in SSSD. SSSD needs to be restarted in order for
                this command to take effect.
    disable     Disable service in SSSD. SSSD needs to be restarted in order for
                this command to take effect.
    
List options:
    --enabled   List only enabled services.
    --disabled  List only disabled services.
"""

from lmi.scripts.common import command
from lmi.scripts import sssd

class List(command.LmiLister):
    COLUMNS = ('Name', "Enabled", "Debug Level")

    def execute(self, ns,  _enabled, _disabled):
        kind = 'all'
        if _enabled:
            kind = 'enabled'
        elif _disabled:
            kind = 'disabled'

        for s in sorted(sssd.list_services(ns, kind), key=lambda i: i.Name):
            yield (s.Name, s.IsEnabled, sssd.debug_level(s.DebugLevel))
            
class Show(command.LmiShowInstance):
    DYNAMIC_PROPERTIES = True
    
    def execute(self, ns, service):
        columns = (
            'Name',
            ('Enabled', 'IsEnabled'),
            ('Debug Level', lambda i: sssd.debug_level(i.DebugLevel)))

        return columns, sssd.get_service(ns, service)
    
class Enable(command.LmiCheckResult):
    CALLABLE = sssd.enable_service
    EXPECT = 0
    
class Disable(command.LmiCheckResult):
    CALLABLE = sssd.disable_service
    EXPECT = 0

class ServiceCommands(command.LmiCommandMultiplexer):
    COMMANDS = {
            'list'    : List,
            'show'    : Show,
            'enable'  : Enable,
            'disable' : Disable
    }
    OWN_USAGE = __doc__
