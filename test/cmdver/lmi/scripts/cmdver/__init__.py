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

import pywbem
from lmi.scripts.common import command
from lmi.scripts.common import get_computer_system

# 1st entry point
class CmdverSw(command.LmiSelectCommand):
    """
    This is a short description for CmdverSw.
    """
    SELECT = (
            ('OpenLMI-Software < 0.4.2', 'lmi.scripts.cmdver.pre042.Cmd'),
            ('OpenLMI-Software == 0.4.2', 'lmi.scripts.cmdver.ver042.Cmd'),
            ('OpenLMI-Software > 0.4.2', 'lmi.scripts.cmdver.devel.Cmd'),
    )

def get_hw_profile_version(ns):
    try:
        return ns.connection.root.interop.wql('SELECT * FROM PG_RegisteredProfile'
            ' WHERE RegisteredName="OpenLMI-Hardware"')[0].RegisteredVersion
    except pywbem.CIMError, IndexError:
        return None

class SystemInfo(command.LmiLister):
    COLUMNS = []
    PRE042 = False

    def execute(self, ns):
        cls = ns.LMI_Chassis
        inst = cls.first_instance()
        verstr = get_hw_profile_version(ns)
        if self.PRE042:
            verstr += ' (PRE 0.4.2)'
        return [('Prov version', verstr),
                ('Chassis Type', cls.ChassisPackageTypeValues.value_name(
                    inst.ChassisPackageType))]

class HostnameInfo(command.LmiLister):
    COLUMNS = []
    PRE042 = False

    def execute(self, ns):
        verstr = get_hw_profile_version(ns)
        if self.PRE042:
            verstr += ' (PRE 0.4.2)'
        return [('Prov version', verstr),
                ('Hostname', get_computer_system(ns).Name)]

class PreSystemInfo(SystemInfo):
    PRE042 = True

class PreHostnameInfo(HostnameInfo):
    PRE042 = True

class HwCmd(command.LmiCommandMultiplexer):
    """
    Hardware testing command.

    Usage:
        %(cmd)s system
        %(cmd)s hostname
    """
    COMMANDS = {
            'system'   : SystemInfo,
            'hostname' : HostnameInfo
    }
    OWN_USAGE = True

class PreHwCmd(HwCmd):
    COMMANDS = {
            'system'   : PreSystemInfo,
            'hostname' : PreHostnameInfo
    }

class NoHwRegistered(command.LmiLister):
    """
    Hardware testing command.

    Usage: %(cmd)s <cmd>
    """
    COLUMNS = []
    OWN_USAGE = True
    def execute(self, ns, cmd):
        return [('Given command', cmd), ('Prov version', 'N/A')]

# 2nd entry point
class CmdverHw(command.LmiSelectCommand):
    """
    This is a short description for CmdverHw.
    """
    SELECT = (
            ('OpenLMI-Hardware < 0.4.2', PreHwCmd),
            ('OpenLMI-Hardware >= 0.4.2 & class LMI_Chassis == 0.3.0', HwCmd)
    )
    DEFAULT = NoHwRegistered

# 3rd entry point
class Cmdver(command.LmiCommandMultiplexer):
    """
    Command for testing version dependencies.

    Usage:
        %(cmd)s (sw|hw) [<args>...]
    """
    COMMANDS = {
            'sw' : CmdverSw,
            'hw' : CmdverHw
    }
    OWN_USAGE = True
