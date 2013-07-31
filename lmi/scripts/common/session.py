# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
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
# Authors: Michal Minar <miminar@redhat.com>
# -*- coding: utf-8 -*-

from collections import defaultdict
import getpass
import os
import pywbem
import readline

from lmi.scripts.common import errors
from lmi.scripts.common import get_logger
from lmi.shell import LMIUtil
from lmi.shell.LMIConnection import LMIConnection

LOG = get_logger(__name__)

class Session(object):

    def __init__(self, app, hosts, credentials=None):
        self._app = app
        self._connections = {h: None for h in hosts}
        self._credentials = defaultdict(lambda: ('', ''))
        if credentials is not None:
            if not isinstance(credentials, dict):
                raise TypeError("credentials must be a dictionary")
            self._credentials.update(credentials)

    def __getitem__(self, hostname):
        if self._connections[hostname] is None:
            self._connections[hostname] = self._connect(
                    hostname, interactive=True)
        return self._connections[hostname]

    def __len__(self):
        return len(self._connections)

    def __iter__(self):
        successful_connections = 0
        for h in self._connections:
            try:
                connection = self[h]
                if connection is not None:
                    yield connection
                    successful_connections += 1
            except Exception as exc:
                LOG().error('failed to make a connection to "%s": %s', h, exc)
        if successful_connections == 0:
            raise errors.LmiNoConnections('no successful connection made')

    def _connect(self, hostname, interactive=False):
        username, password = self.get_credentials(hostname)
        prompt_prefix = '[%s] '%hostname if len(self) > 1 else ''
        if not username:
            while True:
                try:
                    username = raw_input(prompt_prefix + "username: ")
                    if username:
                        break
                except EOFError, e:
                    self._app.stdout.write("\n")
                    continue
                except KeyboardInterrupt, e:
                    self._app.stdout.write("\n")
                    return None
            if self._app.interactive_mode:
                readline.remove_history_item(
                        readline.get_current_history_length() - 1)
        if not password:
            try:
                password = getpass.getpass(prompt_prefix + 'password: ')
            except EOFError, e:
                password = ""
                LOG().warn('End of File when reading password for "%s"',
                        hostname)
            except KeyboardInterrupt, e:
                LOG().warn('failed to get password for host "%s"', hostname)
                return None
            if self._app.interactive_mode:
                readline.remove_history_item(
                        readline.get_current_history_length() - 1)
        # Try to get some non-existing class as a login check
        connection = LMIConnection(hostname, username, password, interactive)
        use_exceptions = LMIUtil.lmi_get_use_exceptions()
        try:
            LMIUtil.lmi_set_use_exceptions(True)
            connection.root.cimv2.NonExistingClass
        except pywbem.cim_operations.CIMError, e:
            if e.args[0] == pywbem.cim_constants.CIM_ERR_NOT_FOUND:
                return connection
            LOG().error('failed to connect to host "%s"', hostname)
            if use_exceptions:
                raise
            return None
        except pywbem.cim_http.AuthError, e:
            LOG().error('failed to authenticate against host "%s"', hostname)
            return None
        finally:
            LMIUtil.lmi_set_use_exceptions(use_exceptions)
        LOG().debug('connection to host "%s" successfully created', hostname)
        return connection

    @property
    def hostnames(self):
        return self._connections.keys()

    def get_credentials(self, hostname):
        return self._credentials[hostname]

    def get_unconnected(self):
        return [h for h, c in self._connections.items() if c is None]

