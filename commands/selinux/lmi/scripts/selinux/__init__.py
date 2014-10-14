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
# Authors: Vitezslav Crhonek <vcrhonek@redhat.com>
#
"""
LMI SELinux Provider client library.
"""

try:
    import lmiwbem as wbem
except ImportError:
    import pywbem as wbem

from lmi.shell import LMIExceptions
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_computer_system
from lmi.scripts.common import get_logger
import sys

LOG = get_logger(__name__)

def state2str(state):
    if state == 0: return "Disabled"
    elif state == 1: return "Permissive"
    elif state == 2: return "Enforcing"
    else: return "Unknown"

def proc_state(state):
    if state.lower() in ("0", "disabled"): return 0
    elif state.lower() in ("1", "permissive"): return 1
    elif state.lower() in ("2", "enforcing"): return 2

def proc_bool(val):
    if val.lower() in ("0", "false", "no", "off"): return False
    elif val.lower() in ("1", "true", "yes", "on"): return True
    else: return "Unknown"

def proc_action(str):
    if str.lower() in ("0", "report"): return 0
    elif str.lower() in ("1", "restore"): return 1

def get_uf_name(ns, target):
    system = get_computer_system(ns)
    uf_name = ns.LMI_UnixFile.new_instance_name(
        {'CSCreationClassName':system.classname,
         'CSName':system.name,
         'LFCreationClassName':'ignored',
         'FSCreationClassName':'ignored',
         'FSName':'ignored',
         'LFName':target})
    return uf_name

def get_uf(ns, target):
    uf_name = get_uf_name(ns, target)
    try:
        uf = uf_name.to_instance()
    except LMIExceptions.CIMError as err:
        msg = 'Could not get target'
        if err[1]:
            msg += err[1][err[1].index(':'):]
        raise LmiFailed(msg)
    else:
        return uf

def get_service(ns):
    """
    Get instance of SELinux service.

    :rtype: LMIInstance/LMI_SELinuxService
    """
    inst = ns.LMI_SELinuxService.first_instance()

    if inst is None:
        raise LmiFailed('Failed to get instance of LMI_SELinuxService.')

    return inst

def list_elements(ns, kind):
    """
    List SELinux elements (booleans and ports).

    :param kind: Elements to be listed.
    """
    try:
        for element in sorted(ns.LMI_SELinuxElement.instances(client_filtering=True),
                key=lambda i: i.ElementName):
            if kind == 'booleans' and "SELinuxBoolean" not in element.InstanceID:
                continue
            if kind == 'ports' and "SELinuxPort" not in element.InstanceID:
                continue
            yield element
    except LMIExceptions.CIMError as err:
        if err.args[0] == wbem.CIM_ERR_NOT_SUPPORTED:
            raise LmiFailed('Service provider is not installed or registered.')
        raise LmiFailed('Failed to list services: %s' % err.args[1])

def set_state(ns, new_state, default):
    """
    Set SELinux state.

    :param new_state: New state value.
    :param bool default: If set to True, makes the new state persistent.
    """
    service = get_service(ns)

    try:
        (rval, _, errorstr) = service.SyncSetSELinuxState(
            NewState=proc_state(new_state),
            MakeDefault=default,
        )
    except LMIExceptions.CIMError as err:
        msg = 'Failed to set SELinux state'
        if err[1]:
            msg += err[1][err[1].index(':'):]
        raise LmiFailed(msg)
    else:
        if default:
            LOG().info('SELinux default state changed to "%s".',
                state2str(proc_state(new_state)))
        else:
            LOG().info('SELinux state changed to "%s".',
                state2str(proc_state(new_state)))

def set_boolean(ns, target, value, default):
    """
    Set a new value of an SELinux boolean.

    :param target: An SELinux boolean to change.
    :param value: New value.
    :param bool default: If True, makes the new state persistent.
    """
    service = get_service(ns)
    id = "LMI:LMI_SELinuxBoolean:" + target
    tg = ns.LMI_SELinuxBoolean.new_instance_name({"InstanceID":id})

    try:
        (rval, _, errorstr) = service.SyncSetBoolean(
            Target=tg,
            Value=proc_bool(value),
            MakeDefault=default,
        )
    except LMIExceptions.CIMError as err:
        msg = 'Failed to set SELinux boolean'
        if err[1]:
            msg += err[1][err[1].index(':'):]
        raise LmiFailed(msg)
    else:
        LOG().info('SELinux boolean "%s" changed to "%s"%s.',
            target, proc_bool(value), ' (persistently)' if default else '')

def set_port(ns, target, protocol, port_range):
    """
    Set label on an SELinux port.

    :param target: An SELinux port to change.
    :param protocol: Network protocol (TCP/UDP).
    :param port_range: Network ports to change. Single port or a range, for example 1024-2048'.
    """
    service = get_service(ns)
    id = "LMI:LMI_SELinuxPort:" + protocol.upper() + ":" + target
    tg = ns.LMI_SELinuxBoolean.new_instance_name({"InstanceID":id})

    try:
        (rval, _, errorstr) = service.SyncSetPortLabel(
            Target=tg,
            PortRange=port_range,
        )
    except LMIExceptions.CIMError as err:
        msg = 'Failed to set SELinux port'
        if err[1]:
            if err[0] == 4:
                msg += err[1][err[1].index(':'):]
            else:
                msg += ": " + err[1]
        raise LmiFailed(msg)
    else:
        LOG().info('SELinux port "%s" changed to "%s" (%s)',
            target, port_range, protocol.upper())

def get_file_label(ns, target):
    """
    Get label of an SELinux file.

    :param target: An SELinux file.
    """
    uf = get_uf(ns, target)
    ident = uf.associators(AssocClass='LMI_FileIdentity')[0]

    print "SELinuxCurrentContext: %s" % uf.SELinuxCurrentContext
    print "SELinuxExpectedContext: %s" % uf.SELinuxExpectedContext

def set_file_label(ns, target, label):
    """
    Set label on an SELinux file.

    :param target: An SELinux file to change.
    :param label: New label.
    """
    uf_name = get_uf_name(ns, target)
    service = get_service(ns)

    try:
        (rval, _, errorstr) = service.SyncSetFileLabel(
            Target=uf_name,
            Label=label,
        )
    except LMIExceptions.CIMError as err:
        msg = 'Failed to set SELinux boolean'
        if err[1]:
            msg += ": " + err[1]
        raise LmiFailed(msg)
    else:
        LOG().info('SELinux label on "%s" changed to "%s"', target, label)

def restore(ns, target, action, recursively):
    """
    Restore default SELinux security contexts on files.

    :param target: SELinux file to change.
    :param action: Action to take on mislabeled files.
    :param recursively: Restore labels recursively in case Target is a directory.
    """
    uf_name = get_uf_name(ns, target)
    service = get_service(ns)

    try:
        (rval, params, errorstr) = service.SyncRestoreLabels(
            Target=uf_name,
            Action=action,
            Recursively=recursively,
        )
    except LMIExceptions.CIMError as err:
        msg = 'Failed to restore default SELinux security context'
        if err[1]:
            if err[0] == 4:
                msg += err[1][err[1].index(':'):]
            else:
                msg += ": " + err[1]
        raise LmiFailed(msg)
    else:
        LOG().info('SELinux security contexts on "%s" restored.', target)
