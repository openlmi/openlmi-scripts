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
System service management.

Usage:
    %(cmd)s list [(--enabled | --disabled)]
    %(cmd)s show <service>
    %(cmd)s start <service>
    %(cmd)s stop <service>
    %(cmd)s enable <service>
    %(cmd)s disable <service>
    %(cmd)s restart [--try] <service>
    %(cmd)s reload <service>
    %(cmd)s reload-or-restart [--try] <service>

Commands:
    list        Prints a list of services. Only enabled services are
                printed at default.
    show        Show detailed information about service.
    start       Starts a service.
    stop        Stops the service.
    restart     Restarts the service.
    reload      Ask the service to reload its configuration.
    reload-or-restart
                Reload the service if it supports it. If not, restart it
                instead.

Options:
    --enabled   List only enabled services.
    --disabled  List only disabled services.
    --try       Whether to abandon the operation if the service is not running.
"""
import functools

from lmi.scripts import service as srv
from lmi.scripts.common import command

class Lister(command.LmiInstanceLister):

    DYNAMIC_PROPERTIES = True

    def execute(self, ns, _enabled, _disabled):
        kind = 'all'
        if _enabled:
            kind = 'enabled'
        elif _disabled:
            kind = 'disabled'

        columns = [
                ('Name', lambda i: srv.RE_SUFFIX.sub('', i.Name)),
                ('Status', lambda i: srv.get_status_string(ns, i))]
        if kind == 'all':
            columns.append(('Enabled', lambda i: srv.get_enabled_string(ns, i)))

        def generator():
            for service_inst in srv.list_services(ns, kind):
                yield service_inst

        return columns, generator()

class Start(command.LmiCheckResult):
    CALLABLE = srv.start_service
    EXPECT = 0

class Stop(command.LmiCheckResult):
    CALLABLE = srv.stop_service
    EXPECT = 0

class Enable(command.LmiCheckResult):
    CALLABLE = srv.enable_service
    EXPECT = 0

    def transform_options(self, options):
        options['<enable>'] = True

class Disable(command.LmiCheckResult):
    CALLABLE = srv.enable_service
    EXPECT = 0

    def transform_options(self, options):
        options['<enable>'] = False

class Restart(command.LmiCheckResult):
    CALLABLE = srv.restart_service
    EXPECT = 0

    def transform_options(self, options):
        """
        ``try`` is a keyword argument in python, let's rename it to
        ``just-try`` which will be transformed into ``just_try``.
        """
        options['just-try'] = options.pop('--try')

class Reload(command.LmiCheckResult):
    EXPECT = 0

    def execute(self, ns, service):
        return srv.reload_service(ns, service)

class ReloadOrRestart(command.LmiCheckResult):
    EXPECT = 0

    def execute(self, ns, service, _try=False):
        return srv.reload_service(ns, service, force=True, just_try=_try)

class Show(command.LmiShowInstance):

    DYNAMIC_PROPERTIES = True

    def execute(self, ns, service):
        columns = (
                ('Name', lambda i: srv.RE_SUFFIX.sub('', i.Name)),
                'Caption',
                ('Enabled', lambda i: srv.get_enabled_string(ns, i)),
                ('Status', lambda i: srv.get_status_string(ns, i)))

        return columns, srv.get_service(ns, service)

Service = command.register_subcommands(
        'Service', __doc__,
        { 'list'    : Lister
        , 'show'    : Show
        , 'start'   : Start
        , 'stop'    : Stop
        , 'enable'  : Enable
        , 'disable' : Disable
        , 'restart' : Restart
        , 'reload'  : Reload
        , 'reload-or-restart' : ReloadOrRestart
        },
    )
