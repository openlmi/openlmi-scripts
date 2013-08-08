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
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Module for session object representing all connection to remote hosts.
"""

from collections import defaultdict

from lmi.scripts.common import errors
from lmi.scripts.common import get_logger
from lmi.shell.LMIConnection import connect

LOG = get_logger(__name__)

class Session(object):
    """
    Session object keeps connection objects to remote hosts. Their are
    associated with particular hostnames. It also caches credentials for them.
    Connections are made as they are needed. When credentials are missing
    for connection to be made, the user is asked to supply them from
    standard input.

    :param app: Instance of main application.
    :param hosts: (``list``) List of hostname strings.
    :param credentials: (``dict``) Mapping assigning pair (user, passward) to
        each hostname.
    """

    def __init__(self, app, hosts, credentials=None):
        self._app = app
        self._connections = {h: None for h in hosts}
        self._credentials = defaultdict(lambda: ('', ''))
        if credentials is not None:
            if not isinstance(credentials, dict):
                raise TypeError("credentials must be a dictionary")
            self._credentials.update(credentials)

    def __getitem__(self, hostname):
        """
        :rtype: (``LMIConnection``) Connection object to remote host.
            ``None`` if connection can not be made.
        """
        if self._connections[hostname] is None:
            self._connections[hostname] = self._connect(
                    hostname, interactive=True)
        return self._connections[hostname]

    def __len__(self):
        """ Get the number of hostnames in session. """
        return len(self._connections)

    def __iter__(self):
        """ Yields connection objects. """
        successful_connections = 0
        for hostname in self._connections:
            try:
                connection = self[hostname]
                if connection is not None:
                    yield connection
                    successful_connections += 1
            except Exception as exc:
                LOG().error('failed to make a connection to "%s": %s',
                        hostname, exc)
        if successful_connections == 0:
            raise errors.LmiNoConnections('no successful connection made')

    def _connect(self, hostname, interactive=False):
        """
        Makes the connection to host.

        :param hostname: (``str``) Name of host.
        :param interactive: (``bool``) Whether we can interact with user
            and expect a reply from him.
        :rtype: (``LMIConnection``) Connection to remote host or ``None``.
        """
        username, password = self.get_credentials(hostname)
        connection = connect(hostname, username, password,
                interactive=interactive)
        if connection is not None:
            LOG().debug('connection to host "%s" successfully created',
                    hostname)
            if not username or not password:
                # connect function of lmi shell may obtain credentials from
                # user vie stdin
                self._credentials[hostname] = \
                        connection._client._cliconn.creds
        else:
            LOG().error('failed to connect to host "%s"', hostname)
        return connection

    @property
    def hostnames(self):
        """ :rtype: (``list``) List of hostnames in session. """
        return self._connections.keys()

    def get_credentials(self, hostname):
        """
        :rtype: (``tuple``) Pair of (username, password) for given
            hostname. If no credentials were given for this host,
            ('', '') is returned.
        """
        return self._credentials[hostname]

    def get_unconnected(self):
        """
        :rtype: (``list``) List of hostnames, which do not have associated
            connection yet.
        """
        return [h for h, c in self._connections.items() if c is None]

