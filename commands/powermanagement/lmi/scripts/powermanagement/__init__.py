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

"""
LMI power management provider client library.
"""

from lmi.scripts.common.errors import LmiFailed, LmiInvalidOptions
from lmi.scripts.common import get_logger

import IPy

LOG = get_logger(__name__)

POWER_STATE_POWEROFF = 12
''' Turn off the system. '''

POWER_STATE_POWEROFF_FORCE = 8
''' Turn off the system without shutting down services first. '''

POWER_STATE_REBOOT= 15
''' Reboot the system. '''

POWER_STATE_REBOOT_FORCE = 5
''' Reboot the system without shutting down services first. '''

POWER_STATE_SUSPEND = 4
''' Suspend the system. '''

POWER_STATE_HIBERNATE = 7
''' Hibernate the system. '''


def list_power_states(ns):
    '''
    Get list of available power states.

    :return: list of power states
    :rtype: list of POWER_STATE_* constants
    '''
    capabilities = ns.LMI_PowerManagementCapabilities.first_instance()
    for state in capabilities.PowerStatesSupported:
        yield state

def switch_power_state(ns, state):
    '''
    Switch system power state.

    :param state: Requested power state.
    :type state: POWER_STATE_* constant
    '''
    # Check if the power state is available first
    capabilities = ns.LMI_PowerManagementCapabilities.first_instance()
    if not state in capabilities.PowerStatesSupported:
        raise LmiInvalidOptions("Power state is not supported.")
    service = ns.LMI_PowerManagementService.first_instance()
    service.RequestPowerStateChange(PowerState=state)
    return 0
