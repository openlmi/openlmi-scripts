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
LMI account provider client library.

This set of functions can create, modify and delete users and groups on
a remote managed system.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.shell.LMIInstanceName import LMIInstanceName
from lmi.scripts.common import get_logger
import pywbem
import lmi.scripts.common

LOG = get_logger(__name__)

def list_users(ns):
    """
    Yield all users on the system.

    :rtype: generator of LMIInstances.
    """
    for user in ns.LMI_Account.instances():
            yield user

def list_groups(ns):
    """
    Yield all groups on the system.

    :rtype: generator of LMIInstances.
    """
    for group in ns.LMI_Group.instances():
            yield group

def get_user(ns, username):
    """
    Return LMIInstance of the user. This function raises LmiFailed if the user
    is not found.

    :type username: string
    :param username: Name of the user.
    :rtype: LMIInstance of LMI_Account
    :returns: The user.
    """

    cs = lmi.scripts.common.get_computer_system(ns)
    keys = {
            'Name': username,
            'CreationClassName': 'LMI_Account',
            'SystemCreationClassName': cs.CreationClassName,
            'SystemName': cs.Name,
    }
    try:
        user = ns.LMI_Account.new_instance_name(keys).to_instance()
    except pywbem.CIMError, err:
        if err[0] == pywbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the user: %s" % username)
        raise
    return user

def get_group(ns, groupname):
    """
    Return LMIInstance of the group. This function raises LmiFailed if the user
    is not found.

    :type groupname: string
    :param groupname: Name of the group.
    :rtype: LMIInstance of LMI_Group
    :returns: The group.
    """

    keys = {'Name' : groupname, 'CreationClassName': 'LMI_Group'}
    try:
        group = ns.LMI_Group.new_instance_name(keys).to_instance()
    except pywbem.CIMError, err:
        if err[0] == pywbem.CIM_ERR_NOT_FOUND:
            raise LmiFailed("Cannot find the group: %s" % groupname)
        raise
    return group

def delete_user(ns, user,
        no_delete_group=False,
        no_delete_home=False,
        force=False):
    """
    Delete a user.

    :type user: LMIInstance or LMIInstanceName of LMI_Account.
    :param user: User to delete.
    :type no_delete_group: boolean
    :param no_delete_group: True, if the user's private group should be preserved.
            (default = False, the group is deleted).
    :type no_delete_home: boolean
    :param no_delete_home: True, if user's home directory should be preserved.
            (default = False, home is deleted).
    :type force: boolean
    :param force: True, if the home directory should be remove even though the
            user is not owner of the directory. (default = False, do not remove
            user's home if it is owned by someone else).
    """
    params = {
        "DontDeleteHomeDirectory": no_delete_home,
        "DontDeleteGroup": no_delete_group,
        "Force": force
    }
    for key in params.keys():
        if params[key] is None:
            del params[key]
    LOG().debug("Removing user %s with arguments %s", user.Name, str(params))
    user.DeleteUser(**params)

def create_user(ns, name,
        gecos=None,
        home=None, create_home=True,
        shell=None,
        uid=None,
        gid=None, create_group=True,
        reserved=False,
        password=None, plain_password=False,
        ):
    """
    Create a new user.

    :type name: string
    :param name: Name of the user.
    :type gecos: string
    :param gecos: GECOS information of the new user.
    :type home: string
    :param home: Home directory.
    :type create_home: boolean
    :param create_home: True, if home directory should be automatically created.
    :type shell: string
    :param shell: User's shell.
    :type uid: int
    :param uid: Desired UID. If None, system will allocate a free one.
    :type gid: int
    :param gid: Desired GID. If None, system will allocate a free one.
    :type create_group: boolean
    :param create_group: True, if user's private group should be created.
    :type reserved: boolean
    :param reserved: True, if the account is system one, i.e. it's UID will
            be allocated in system account space (below system defined
            threshold). (default=False, the account is an user).
    :type password: string
    :param password: User password.
    :type plain_password: boolean
    :param plain_password: True, if the provided password is plain text string,
            False if it is already hashed by crypt().
    :rtype: LMIInstanceName
    :returns: Created used.
    """
    cs = lmi.scripts.common.get_computer_system(ns)
    lams = ns.LMI_AccountManagementService.first_instance()

    params = dict({
        "Name": name,
        "System": cs,
        "GECOS": gecos,
        "HomeDirectory": home,
        "DontCreateHome": not create_home,
        "Shell": shell,
        "UID":  int(uid) if uid else uid,
        "GID": int(gid) if gid else gid,
        "SystemAccount": reserved,
        "Password": password,
        "DontCreateGroup": not create_group,
        "PasswordIsPlain": plain_password
        })
    for key in params.keys():
        if params[key] is None:
            del params[key]

    LOG().debug("Creating user %s with arguments %s", name, str(params))
    (ret, outparams, err) = lams.CreateAccount(**params)

    if ret != 0:
        if err:
            raise LmiFailed("Cannot create the user: %s." % err)
        values = lams.CreateAccount.CreateAccountValues
        raise LmiFailed("Cannot create the user: %s."
                % (values.value_name(ret),))
    return outparams['Account']


def get_users_in_group(ns, group):
    """
    Yields users in given group.

    :type group: LMIInstance or LMIInstanceName of LMI_Group.
    :param group: The group to inspect.
    :returns: Generator of LMIInstances of LMI_Account.
    """
    for identity in group.associators(
            AssocClass="LMI_MemberOfGroup", ResultClass="LMI_Identity"):
        yield identity.first_associator(
                AssocClass="LMI_AssignedAccountIdentity",
                ResultClass="LMI_Account")

def create_group(ns, group, reserved=False, gid=None):
    """
    Create a new group on the system.

    :type group: string
    :param group: Name of the group.
    :type reserved: boolean
    :param reserved: Whether the group is a system one (its GID will be
            allocated lower than system-defined threshold).
    :type gid: int
    :param gid: Required GID. It will be allocated automatically if it's None.
    :rtype: LMIInstanceName of the created group.
    :returns: Created group.
    """
    cs = lmi.scripts.common.get_computer_system(ns)
    lams = ns.LMI_AccountManagementService.first_instance()

    params = {
        "Name" : group,
        "System" : cs}
    if reserved:
        params["SystemAccount"] = True
    if gid is not None:
        params["GID"] = int(gid)

    LOG().debug("Creating group %s with arguments %s", group, str(params))

    (ret, outparams, err) = lams.CreateGroup(**params)
    if ret != 0:
        if err:
            raise LmiFailed("Cannot create the group: %s." % err)
        values = lams.CreateGroup.CreateGroupValues
        raise LmiFailed("Cannot create the group: %s."
                % (values.value_name(ret),))
    return outparams['Group']


def delete_group(ns, group):
    """
    Delete a group.

    :type group: LMIInstance or LMIInstanceName of LMI_Group.
    :param group: The group to delete.
    """
    LOG().debug("Removing group %s", group.Name)
    group.delete()

def is_in_group(group, user):
    """
    Return True if user is in group

    :type group: LMIInstance or LMIInstanceName of LMI_Group.
    :param group: The group.
    :type user: LMIInstance or LMIInstanceName of LMI_Account.
    :param user: User to check.
    """
    if isinstance(user, LMIInstanceName):
        user_inst = user.to_instance()
        if not user_inst:
            raise LmiFailed("Cannot find the user: %s." % user.Name)
        user = user_inst

    identity = group.first_associator(
        AssocClass="LMI_MemberOfGroup",
        ResultClass="LMI_Identity")
    if identity is None:
        return False
    return identity.InstanceID.split(":")[-1] == user.UserID

def add_to_group(ns, group, users):
    """
    Add users to a group.

    :type group: LMIInstance or LMIInstanceName of LMI_Group.
    :param group: The group.
    :type users: List (or generator) of LMIInstances or LMIInstanceNames of
            LMI_Account.
    :param users: Users to add.
    """
    for user in users:
        if is_in_group(group, user):
            LOG().info('User "%s" already is in group "%s", skipping.',
                user.Name, group.Name)
        else:
            # get identity
            identity = user.first_associator(
                    AssocClass="LMI_AssignedAccountIdentity",
                    ResultClass="LMI_Identity")
            # add the user; create instance of LMI_MemberOfGroup
            LOG().info('Adding user %s to group %s', user.Name, group.Name)
            ns.LMI_MemberOfGroup.create_instance(
                {"Member":identity.path, "Collection":group.path})

def remove_from_group(ns, group, users):
    """
    Remove users from a group.

    :type group: LMIInstance or LMIInstanceName of LMI_Group.
    :param group: The group.
    :type users: List (or generator) of LMIInstances or LMIInstanceNames of
            LMI_Account.
    :param users: Users to remove.
    """
    for user in users:
        LOG().debug("Removing user %s from group %s", user.Name, group.Name)
        # get identity
        identity = user.first_associator(
                AssocClass="LMI_AssignedAccountIdentity",
                ResultClass="LMI_Identity")
        # get MemberOfGroup
        for mog in identity.references(ResultClass="LMI_MemberOfGroup"):
            if mog.Collection.Name == group.Name:
                mog.delete()
