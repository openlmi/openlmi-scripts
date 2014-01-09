# Storage Management Providers
#
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#

"""
MD RAID management.

Usage:
    %(cmd)s list
    %(cmd)s create [ --name=<name> ] <level> <device> ...
    %(cmd)s delete <device> ...
    %(cmd)s show [ <device> ...]

Commands:
    list        List all MD RAID devices on the system.

    create      Create MD RAID array with given RAID level from list of devices.

    delete      Delete given MD RAID devices.

    show        Show detailed information about given MD RAID devices. If no
                devices are provided, all MD RAID devices are displayed.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import raid, show
from lmi.scripts.storage.common import str2device
from lmi.scripts.common import formatter
from lmi.scripts.common.formatter import command as fcmd

class Lister(command.LmiLister):
    COLUMNS = ('DeviceID', 'Name', "Level", "Nr. of members")

    def execute(self, ns):
        """
        Implementation of 'raid list' command.
        """
        for r in raid.get_raids(ns):
            members = raid.get_raid_members(ns, r)
            yield (r.DeviceID, r.ElementName, r.Level, len(members))


class Create(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices, level, _name=None):
        """
        Implementation of 'raid create' command.
        """
        raid.create_raid(ns, devices, int(level), _name)


class Delete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices):
        """
        Implementation of 'raid delete' command.
        """
        for dev in devices:
            raid.delete_raid(ns, dev)


class Show(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, devices=None):
        """
        Implementation of 'raid show' command.
        """
        if not devices:
            devices = raid.get_raids(ns)
        for r in devices:
            r = str2device(ns, r)
            cmd = fcmd.NewTableCommand(title=r.DeviceID)
            yield cmd
            for line in show.raid_show(ns, r, self.app.config.human_friendly):
                yield line


Raid = command.register_subcommands(
        'raid', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
