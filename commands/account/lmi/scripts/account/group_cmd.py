# Account Management Providers
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
#
# Authors: Roman Rakus <rrakus@redhat.com>
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
POSIX group information and management.

Usage:
    %(cmd)s list [ <group> ...]
    %(cmd)s create [--reserved] [--gid=gid] <group>
    %(cmd)s delete <group>
    %(cmd)s listuser [<group>] ...
    %(cmd)s adduser <group> <user> ...
    %(cmd)s removeuser <group> <user> ...

Commands:
    list        List groups. If no groups are given, all are listed.


    create      Creates a new group.

    delete      Deletes a group.

    listuser    List a users in a group or in a list of groups.

    adduser     Adds a user or a list of users to the group.

    removeuser  Removes a user or a list of users from the group.

Options:
    -r, --reserved  Create a system group.
    -g, --gid=gid   GID for a new group.
"""

from lmi.scripts.common import command
from lmi.scripts.common.errors import LmiInvalidOptions
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
from lmi.scripts import account

LOG = get_logger(__name__)


class Lister(command.LmiInstanceLister):
    PROPERTIES = (
            'Name',
            ('GID', lambda i: i.InstanceID.split(":")[-1])
    )

    def transform_options(self, options):
        """
        Rename 'group' option to 'groups' parameter name for better
        readability
        """
        options['<groups>'] = options.pop('<group>')

    def execute(self, ns, groups):
        if groups:
            for group in groups:
                inst = account.get_group(ns, group)
                yield inst
        else:
            for group in account.list_groups(ns):
                yield group

class ListUser(command.LmiLister):
    COLUMNS = ('Group', 'Users')

    def transform_options(self, options):
        """
        Rename 'group' option to 'groups' parameter name for better
        readability
        """
        options['<groups>'] = options.pop('<group>')

    def execute(self, ns, groups):
        if not groups:
            group_insts = account.list_groups(ns)
        else:
            group_insts = []
            for group in groups:
                group_insts.append(account.get_group(ns, group))

        for group in group_insts:
            users = account.get_users_in_group(ns, group)
            yield (group.Name, ', '.join([user.Name for user in users]))

class Create(command.LmiCheckResult):
    OPT_NO_UNDERSCORES = True
    EXPECT = None

    def verify_options(self, opts):
        _gid = opts.get('gid', None)
        if _gid is not None and not _gid.isdigit():
            raise LmiInvalidOptions("Group ID must be a number")

    def transform_options(self, options):
        """
        Change 'group' list to string
        """
        options['<group>'] = options.pop('<group>')[0]

    def execute(self, ns, group, reserved=None, gid=None):
        account.create_group(ns, group, reserved, gid)

class Delete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Change 'group' list to string
        """
        options['<group>'] = options.pop('<group>')[0]

    def execute(self, ns, group):
        group = account.get_group(ns, group)
        account.delete_group(ns, group)

class Add(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Change 'group' list to string
        Rename 'user' to 'users'
        """
        options['<group>'] = options.pop('<group>')[0]
        options['<users>'] = options.pop('<user>')

    def execute(self, ns, group, users):
        group_inst = account.get_group(ns, group)
        user_insts = []
        for user in users:
            user_inst = account.get_user(ns, user)
            user_insts.append(user_inst)
        account.add_to_group(ns, group_inst, user_insts)

class Remove(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Change 'group' list to string
        Rename 'user' to 'users'
        """
        options['<group>'] = options.pop('<group>')[0]
        options['<users>'] = options.pop('<user>')

    def execute(self, ns, group, users):
        group_inst = account.get_group(ns, group)
        user_insts = []
        for user in users:
            user_inst = account.get_user(ns, user)
            user_insts.append(user_inst)
        account.remove_from_group(ns, group_inst, user_insts)

Group = command.register_subcommands(
        'group', __doc__,
        { 'list'    : Lister
        , 'create'  : Create
        , 'delete'  : Delete
        , 'listuser': ListUser
        , 'adduser' : Add
        , 'removeuser': Remove
        },
    )
