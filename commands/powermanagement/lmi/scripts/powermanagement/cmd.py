# Networking Providers
#
# Copyright (C) 2014 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Radek Novacek <rnovacek@redhat.com>
#
"""
System power state management.

Usage:
    %(cmd)s list
    %(cmd)s suspend
    %(cmd)s hibernate
    %(cmd)s reboot [--force]
    %(cmd)s poweroff [--force]

Commands:
    list             Prints a list of available power states.
    suspend          Suspend the system (suspend to RAM).
    hibernate        Hibernate the system (suspend to disk).
    reboot           Shutdown and reboot the system (--force will skip shutdown of running services).
    poweroff         Shutdown the system (--force will skip shutdown of running services).

Options:
    --force          Skip shutting down services first
"""

import abc

from lmi.scripts.common import command
from lmi.scripts.common import errors
from lmi.scripts.common.formatter import command as fcmd
from lmi.scripts.powermanagement import *

def cmd_list(ns):
    """
    Implementation of 'power list' command.
    """
    state_names = {
        POWER_STATE_POWEROFF: "poweroff",
        POWER_STATE_POWEROFF_FORCE: "force poweroff",
        POWER_STATE_REBOOT: "reboot",
        POWER_STATE_REBOOT_FORCE: "force reboot",
        POWER_STATE_SUSPEND: "suspend",
        POWER_STATE_HIBERNATE: "hibernate"
    }

    available_states = list_power_states(ns)
    for state, name in state_names.items():
        if state in available_states:
            yield (name, "yes")
        else:
            yield (name, "no")

def _do_switch_power_state(ns, cmd):
    """
    Executes given command on particular host and logs it.
    """
    res = switch_power_state(ns, cmd)
    LOG().info('Machine %s has been %s.', ns.connection.uri,
            { POWER_STATE_POWEROFF       : "shut down"
            , POWER_STATE_POWEROFF_FORCE : "forcefully shut down"
            , POWER_STATE_REBOOT         : "rebooted"
            , POWER_STATE_REBOOT_FORCE   : "forcefully rebooted"
            , POWER_STATE_SUSPEND        : "suspended"
            , POWER_STATE_HIBERNATE      : "hibernated"}[cmd])
    return res

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.powermanagement.cmd:cmd_list'
    COLUMNS = ('PowerState','Available')

class PowerCmd(command.LmiCheckResult):
    EXPECT = 0
    OPT_NO_UNDERSCORES = True

    @abc.abstractmethod
    def get_cmd_code(self, force=False):
        pass
    
    def execute(self, ns, **kwargs):
        return _do_switch_power_state(ns, self.get_cmd_code(**kwargs))

class Suspend(PowerCmd):
    
    def get_cmd_code(self, force=False):
        return POWER_STATE_SUSPEND

class Hibernate(PowerCmd):

    def get_cmd_code(self, force=False):
        return POWER_STATE_HIBERNATE

class Poweroff(PowerCmd):

    def get_cmd_code(self, force=False):
        return POWER_STATE_POWEROFF_FORCE if force else POWER_STATE_POWEROFF

class Reboot(PowerCmd):

    def get_cmd_code(self, force=False):
        return POWER_STATE_REBOOT_FORCE if force else POWER_STATE_REBOOT

PowerManagement = command.register_subcommands(
    'PowerManagement', __doc__,
    {
        'list':       Lister,
        'suspend':    Suspend,
        'hibernate':  Hibernate,
        'poweroff':   Poweroff,
        'reboot':     Reboot
    },
)
