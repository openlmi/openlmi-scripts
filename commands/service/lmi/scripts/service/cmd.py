# Software Management Providers
#
# Copyright (C) 2012-2013 Red Hat, Inc.  All rights reserved.
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
#
"""
System service management.

Usage:
    lmi service list [--all | --disabled | --oneshot]
    lmi service show <service>
    lmi service start <service>
    lmi service stop <service>
    lmi service restart <service>

Commands:
    list        Prints a list of services. Only enabled services are
                printed at default.
    show        Show detailed information about service.
    start       Starts a service.
    stop        Stops the service.
    restart     Restarts the service.

Options:
    --all       List all services available.
    --disabled  List only disabled services.
    --oneshot   List only oneshot services.
"""

from lmi.scripts.common import command

class Lister(command.LmiLister):
    CALLABLE = 'lmi.scripts.service:list'
    COLUMNS = ('Name', "Started", 'Status')

class Start(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.service:start'
    EXPECT = 0

class Stop(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.service:stop'
    EXPECT = 0

class Restart(command.LmiCheckResult):
    CALLABLE = 'lmi.scripts.service:restart'
    EXPECT = 0

class Show(command.LmiShowInstance):
    CALLABLE = 'lmi.scripts.service:get_instance'
    PROPERTIES = (
            'Name',
            'Caption',
            ('Enabled', lambda i: i.EnabledDefault == 2),
            ('Active', lambda i: i.Started),
            ('Status', lambda i: i.Status))

Service = command.register_subcommands(
        'Service', __doc__,
        { 'list'    : Lister
        , 'show'    : Show
        , 'start'   : Start
        , 'stop'    : Stop
        , 'restart' : Restart
        },
    )
