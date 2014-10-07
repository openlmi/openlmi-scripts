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
# Authors: Vitezslav Crhonek <vcrhonek@redhat.com>
#
"""
SELinux management.

Usage:
    %(cmd)s show
    %(cmd)s list (booleans | ports)
    %(cmd)s set-state [--default] <new_state>
    %(cmd)s set-boolean [--default] <target> <value>
    %(cmd)s set-port <target> <protocol> <port_range>
    %(cmd)s get-label <target>
    %(cmd)s set-label <target> <label>
    %(cmd)s restore [--recursively] <target> <action>

Commands:
    show              Show detailed information about SELinux settings on the managed system.
    list              List SELinux policy booleans or SELinux ports.
    set-state         Set SELinux state.
    set-bool          Set a new value of an SELinux boolean.
    set-port          Set label on an SELinux port.
    get-label         Get label on an SELinux file.
    set-label         Set label on an SELinux file.
    restore           Restore default SELinux security contexts on files.

Options:
    --default         If set, makes the new state persistent.
    --recursively     If set, restores labels recursively in case target is a directory.
"""

from lmi.scripts import selinux as sel
from lmi.scripts.common import command

class Show(command.LmiShowInstance):
    DYNAMIC_PROPERTIES = True

    def execute(self, ns):
        columns = [
            ('PolicyType'),
            ('PolicyVersion'),
            ('SELinuxState', lambda i: sel.state2str(sel.get_service(ns).SELinuxState)),
            ('SELinuxDefaultState', lambda i: sel.state2str(sel.get_service(ns).SELinuxDefaultState)),
        ]
        return columns, sel.get_service(ns)

class ListElements(command.LmiInstanceLister):
    DYNAMIC_PROPERTIES = True

    def execute(self, ns, booleans, ports):
        if booleans:
            columns = [
                ('ElementName'),
                ('State'),
                ('DefaultState'),
            ]
            kind = "booleans"
            
        if ports:
            columns = [
                ('ElementName'),
                ('Ports'),
                ('Protocol'),
            ]
            kind = "ports"

        def generator():
            for sel_ele_inst in sel.list_elements(ns, kind):
                yield sel_ele_inst

        return columns, generator()

class SetState(command.LmiCheckResult):
    CALLABLE = sel.set_state
    OPT_NO_UNDERSCORES = True
    EXPECT = None

class SetBoolean(command.LmiCheckResult):
    CALLABLE = sel.set_boolean
    OPT_NO_UNDERSCORES = True
    EXPECT = None
    
class SetPort(command.LmiCheckResult):
    CALLABLE = sel.set_port
    OPT_NO_UNDERSCORES = True
    EXPECT = None

class GetLabel(command.LmiCheckResult):
    CALLABLE = sel.get_file_label
    OPT_NO_UNDERSCORES = True
    EXPECT = None

class SetLabel(command.LmiCheckResult):
    CALLABLE = sel.set_file_label
    OPT_NO_UNDERSCORES = True
    EXPECT = None

class Restore(command.LmiCheckResult):
    CALLABLE = sel.restore
    OPT_NO_UNDERSCORES = True
    EXPECT = None

Selinux = command.register_subcommands(
        'Selinux', __doc__,
        { 'show' : Show,
          'list' : ListElements,
          'set-state' : SetState,
          'set-boolean' : SetBoolean,
          'set-port' : SetPort,
          'get-label' : GetLabel,
          'set-label' : SetLabel,
          'restore' : Restore,
        },
    )
