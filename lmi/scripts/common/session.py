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
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Module for session object representing all connection to remote hosts.
"""

from collections import defaultdict

from lmi.scripts.common import errors
from lmi.scripts.common import get_logger
from lmi.scripts.common.util import FilteredDict
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
    :param list hosts: List of hostname strings.
    :param dictionary credentials: Mapping assigning a pair
        ``(user, password)`` to each hostname.
    :param boolean same_credentials: Use the same credentials for all
        hosts in session. The first credentials given will be used.
    """

    def __init__(self, app, hosts, credentials=None, same_credentials=False):
        self._app = app
        self._connections = {h: None for h in hosts}
        # { hostname : (username, password, verified), ... }
        # where verified is a flag saying, whether these credentials
        # were successfuly used for logging in
        self._credentials = defaultdict(lambda: ('', '', False))
        self._same_credentials = same_credentials
        if credentials is not None:
            if not isinstance(credentials, dict):
                raise TypeError("credentials must be a dictionary")
            for hostname, creds in credentials.items():
                credentials[hostname] = (creds[0], creds[1], False)
            self._credentials.update(credentials)

    def __getitem__(self, hostname):
        """
        :rtype: (``LMIConnection``) Connection object to remote host.
            ``None`` if connection can not be made.
        """
        if self._connections[hostname] is None:
            try:
                self._connections[hostname] = self._connect(
                        hostname, interactive=True)
            except Exception as exc:
                LOG().error('Failed to make a connection to "%s": %s',
                        hostname, exc)
        return self._connections[hostname]

    def __len__(self):
        """ Get the number of hostnames in session. """
        return len(self._connections)

    def __contains__(self, uri):
        return uri in self._connections

    def __iter__(self):
        """ Yields connection objects. """
        successful_connections = 0
        for hostname in self._connections:
            connection = self[hostname]
            if connection is not None:
                yield connection
                successful_connections += 1
        if successful_connections == 0:
            raise errors.LmiNoConnections('No successful connection made.')

    def _connect(self, hostname, interactive=False):
        """
        Makes the connection to host.

        :param string hostname: Name of host.
        :param boolean interactive: Whether we can interact with user
            and expect a reply from him.
        :returns: Connection to remote host or ``None``.
        :rtype: :py:class:`lmi.shell.LMIConnection` or ``None``
        """
        username, password = self.get_credentials(hostname)
        kwargs = {
                'verify_server_cert' : self._app.config.verify_server_cert,
                'interactive'        : interactive
        }
        if len(self._connections) > 1:
            kwargs['prompt_prefix'] = '[%s] ' % hostname
        connection = connect(hostname, username, password, **kwargs)
        if connection is not None:
            tp = connection._client._cliconn.creds
            if tp is None:
                tp = ('', '')
            self._credentials[hostname] = (tp[0], tp[1], True)
        else:
            LOG().error('Failed to connect to host "%s".', hostname)
        return connection

    @property
    def hostnames(self):
        """
        List of hostnames in session.

        :rtype: list
        """
        return self._connections.keys()

    def get_credentials(self, hostname):
        """
        :param string hostname: Name of host to get credentials for.
        :returns: Pair of ``(username, password)`` for given hostname. If no
            credentials were given for this host, ``('', '')`` is returned.
        :rtype: tuple
        """
        username, password, verified = self._credentials[hostname]
        if (   not verified
           and (not username or not password)
           and self._same_credentials):
            for tp in self._credentials.values():
                if tp[2]:
                    username, password = tp[0], tp[1]
                    break
        return username, password

    def get_unconnected(self):
        """
        :returns:  List of hostnames, which do not have associated connection
            yet.
        :rtype: list
        """
        return [h for h, c in self._connections.items() if c is None]

class SessionProxy(Session):
    """
    Behaves like a session. But it just encapsulates other session object and
    provides access to a subset of its items.

    :param session: Session object or even another session proxy.
    :param list uris: Subset of uris in encapsulated session object.
    """

    def __init__(self, session, uris):
        uris = set(uris)
        if not all(isinstance(uri, basestring) for uri in uris):
            raise ValueError("uris must be iterable of uris")
        for uri in uris:
            if not uri in session:
                raise ValueError('uri "%s" needs to belong to given session'
                        % uri)
        Session.__init__(self, session._app, uris, session._credentials,
                session._same_credentials)
        self._origin = session
        self._connections = FilteredDict(uris, session._connections)
        # let the credentials propagage to original session
        self._credentials = session._credentials

