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

def cmd_suspend(ns):
    """
    Implementation of 'power suspend' command.
    """
    return switch_power_state(ns, POWER_STATE_SUSPEND)

def cmd_hibernate(ns):
    """
    Implementation of 'power hibernate' command.
    """
    return switch_power_state(ns, POWER_STATE_HIBERNATE)

def cmd_poweroff(ns, force=False):
    """
    Implementation of 'power poweroff' command.
    """
    if force:
        return switch_power_state(ns, POWER_STATE_POWEROFF_FORCE)
    else:
        return switch_power_state(ns, POWER_STATE_POWEROFF)

def cmd_reboot(ns, force=False):
    """
    Implementation of 'power reboot' command.
    """
    if force:
        return switch_power_state(ns, POWER_STATE_REBOOT_FORCE)
    else:
        return switch_power_state(ns, POWER_STATE_REBOOT)

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.powermanagement.cmd:cmd_list'
    COLUMNS = ('PowerState','Available')

class Suspend(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns):
        return cmd_suspend(ns)

class Hibernate(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns):
        return cmd_hibernate(ns)

class Poweroff(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, _force):
        return cmd_poweroff(ns, _force)

class Reboot(command.LmiCheckResult):
    EXPECT = 0
    def execute(self, ns, _force):
        return cmd_reboot(ns, _force)

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
