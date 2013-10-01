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
POSIX user information and management.

Usage:
    %(cmd)s list
    %(cmd)s show [ <user> ...]
    %(cmd)s create <name> [options]
    %(cmd)s delete [--no-delete-home] [--no-delete-group] [--force] <user> ...

Commands:
    list        Prints a list of users.

    show        Show detailed information about user. If no users are provided,
                all of them are displayed.

    create      Creates a new user. See Create options below for options
                description.

    delete      Delete specified user (or user list). See Delete options
                below for options description.

Create options:
    -c gecos, --gecos=gecos       Set the GECOS field to gecos.
    -d dir, --directory=dir       Set the user's home directory to dir.
                                  If this option is not set, a default value
                                  is used.
    -s shell, --shell=shell       Set user's login shell to shell. If this
                                  option is not set, a default value is used.
    -u uid, --uid=uid             Use user ID uid for the newly created user.
                                  If this option is not set, a default value
                                  is used.
    -g gid, --gid=gid             Set user's primary group ID to gid. If this
                                  option is not set, a default value is used.
    -r, --reserved                The user is a system user.
                                  Implies the -M option.
    -M, --no-user-home            Don't create a home directory.
    -n, --no-user-group           Don't create a primary group for user.
    -p, --password=pwd            Set user's password to 'pwd'.
    -P, --plain-password          If set, the password set in '-p' parameter
                                  is plain text. Otherwise, it is already
                                  encrypted by supported hash algorithm.
                                  See crypt(3).

Delete options:
    --no-delete-home   Do not remove home directory.
    --no-delete-group  Do not remove users primary group.
    --force            Remove home directory even if the user is not owner.
"""

# TODO -- option separator

from lmi.scripts.common import command
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common.errors import LmiInvalidOptions
from lmi.scripts import account

def get_user_info(ns, user):
    """
    Return detailed information of the user to show.
    """
    return (user.Name, user.UserID, user.HomeDirectory, user.LoginShell,
            user.PasswordLastChange)


class Lister(command.LmiLister):
    COLUMNS = ('Name', "UID", "Full name")

    def execute(self, ns):
        for s in sorted(account.list_users(ns),
                        key=lambda i: i.Name):
            yield (s.Name, s.UserID, s.ElementName)


class Show(command.LmiInstanceLister):
    PROPERTIES = (
            'Name',
            ('UID', 'UserID'),
            ('Home', 'HomeDirectory'),
            ('Login shell', 'LoginShell'),
            ('Password last change', lambda i: i.PasswordLastChange.datetime.strftime("%Y/%m/%d"))
    )

    def transform_options(self, options):
        """
        Rename 'user' option to 'users' parameter name for better
        readability
        """
        options['<users>'] = options.pop('<user>')

    def execute(self, ns, users):
        if users:
            for user in users:
                inst = account.get_user(ns, user)
                yield inst
        else:
            for user in account.list_users(ns):
                yield user

class Delete(command.LmiCheckResult):
    OPT_NO_UNDERSCORES = True
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'user' option to 'users' parameter name for better
        readability
        """
        options['<users>'] = options.pop('<user>')

    def execute(self, ns, users, no_delete_group=False, no_delete_home=False,
            force=False):
        for user in users:
            inst = account.get_user(ns, user)
            account.delete_user(ns, inst, no_delete_group, no_delete_home,
                    force)

class Create(command.LmiCheckResult):
    OPT_NO_UNDERSCORES = True
    EXPECT = None

    def verify_options(self, opts):
        uid = opts['uid']
        gid = opts['gid']
        if uid is not None and not uid.isdigit():
            raise LmiInvalidOptions("User ID must be a number")
        if gid is not None and not gid.isdigit():
            raise LmiInvalidOptions("Group ID must be a number")

    def execute(self, ns, name,
            gecos=None,
            directory=None,
            shell=None,
            uid=None,
            gid=None,
            reserved=None,
            no_user_home=False,
            no_user_group=False,
            password=None,
            plain_password=False):

        account.create_user(ns, name,
                gecos=gecos,
                home=directory,
                create_home=not no_user_home,
                shell=shell,
                uid=uid,
                gid=gid,
                create_group=not no_user_group,
                reserved=reserved,
                password=password,
                plain_password=plain_password)


User = command.register_subcommands(
        'user', __doc__,
        { 'list'    : Lister
        , 'show'    : Show
        , 'create'  : Create
        , 'delete'  : Delete
        },
    )
