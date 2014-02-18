# coding=utf-8
# Storage Management Providers
#
# Copyright (C) 2014 Red Hat, Inc. All rights reserved.
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
LUKS management

Usage:
    %(cmd)s list
    %(cmd)s create [-p <passphrase>] <device>
    %(cmd)s open [-p <passphrase>] <device> <name>
    %(cmd)s close <device>
    %(cmd)s addpass [-p <passphrase>] [-n <new-passphrase>] <device>
    %(cmd)s deletepass [-p <passphrase>]  <device>

Commands:
    list        List available LUKS formats and their clear-text devices
                (if any).

    create      Format given device with LUKS format. Any data on the device
                will be destroyed.

    open        Open given device formatted with LUKS and expose its clear-text
                data as a new block device.

    close       Close given device formatted with LUKS and destroy its
                clear-text block device.

    addpass     Add new passphrase to given LUKS-formatted device. Each device
                can have up to 8 separate passwords and any of them can be used
                to decrypt the device.

    deletepass  Remove given passphrase from LUKS-formatted device.

Common options:
    -p, --passphrase=passphrase  Passphrase. It will be read from the
                                 terminal, if it is not provided on command
                                 line.

    -n, --new-passphrase=passphrase  New passphrase. It will be read from the
                                     terminal, if it is not provided on command
                                     line.

Open options:
    <device>    Device with LUKS format on it.

    <name>      Name of the clear-text block device to create.

Close options:
    <device>    Device with LUKS format on it, previously opened by
                '%(cmd)s open'.
"""

from lmi.scripts.common import command
from lmi.scripts.common import get_logger
from lmi.scripts.storage import luks
import getpass

LOG = get_logger(__name__)

def read_password(prompt1='Passphrase:', prompt2='Retype the passphrase:'):
    """
    Read password from tty without echo. Read it twice and check that they
    match.
    """
    p1 = getpass.getpass(prompt=prompt1)
    p2 = getpass.getpass(prompt=prompt2)

    while p1 != p2:
        print "Passphrases do not match"
        p1 = getpass.getpass(prompt=prompt1)
        p2 = getpass.getpass(prompt=prompt2)

    return p1


class LUKSList(command.LmiLister):
    COLUMNS = ("Device name", "Clear-text device name")

    def execute(self, ns):
        """
        Implementation of 'luks list' command.
        """
        for l in luks.get_luks_list(ns):
            clear = luks.get_luks_device(ns, l)
            if clear:
                clear_name = clear.Name
            else:
                clear_name = ""
            yield (l.ElementName, clear_name)


class LUKSCreate(command.LmiCheckResult):
    EXPECT = None
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, device, passphrase=None):
        """
        Implementation of 'luks create' command.
        """
        if not passphrase:
            passphrase = read_password()
        luks.create_luks(ns, device, passphrase)

class LUKSOpen(command.LmiCheckResult):
    EXPECT = None
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, device, name, passphrase=None):
        """
        Implementation of 'luks open' command.
        """
        if not passphrase:
            passphrase = getpass.getpass('Passphrase:')
        luks.open_luks(ns, device, name, passphrase)

class LUKSClose(command.LmiCheckResult):
    EXPECT = None
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, device):
        """
        Implementation of 'luks close' command.
        """
        luks.close_luks(ns, device)

class LUKSAddPass(command.LmiCheckResult):
    EXPECT = None
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, device, passphrase=None, new_passphrase=None):
        """
        Implementation of 'luks addpass' command.
        """
        if not passphrase:
            passphrase = getpass.getpass('Passphrase:')
        if not new_passphrase:
            new_passphrase = read_password('New passphrase:',
                    'Retype the new passphrase:')
        luks.add_luks_passphrase(ns, device, passphrase, new_passphrase)

class LUKSDeletePass(command.LmiCheckResult):
    EXPECT = None
    OPT_NO_UNDERSCORES = True

    def execute(self, ns, device, passphrase=None):
        """
        Implementation of 'luks deletepass' command.
        """
        if not passphrase:
            passphrase = getpass.getpass('Passphrase:')
        luks.delete_luks_passphrase(ns, device, passphrase)


class LUKS(command.LmiCommandMultiplexer):
    OWN_USAGE = __doc__
    COMMANDS = {
            'list'    : LUKSList,
            'create'  : LUKSCreate,
            'open'    : LUKSOpen,
            'close'   : LUKSClose,
            'addpass' : LUKSAddPass,
            'deletepass' : LUKSDeletePass,
    }
