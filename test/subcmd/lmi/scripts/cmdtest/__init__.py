# Copyright (c) 2014, Red Hat, Inc. All rights reserved.
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
Test command for lmi-metacommand.

Usage:
    %(cmd)s list <cmd> [<args> ...]
    %(cmd)s show pkg <name>
    %(cmd)s show repo <name>
"""

from lmi.scripts.common import errors
from lmi.scripts.common import command

class ListPackages(command.LmiLister):
    OPT_NO_UNDERSCORES = True
    COLUMNS = ('Name', 'Arch')

    def execute(self, ns, installed, available):
        fltr = lambda a: True
        if installed:
            fltr = lambda a: a[2]
        elif available:
            fltr = lambda a: not a[2]
        for pkg in PACKAGES:
            if fltr(pkg):
                yield (pkg[0], pkg[1])

class ListRepos(command.LmiLister):
    OPT_NO_UNDERSCORES = True
    COLUMNS = ('Name', )

    def execute(self, ns, enabled, disabled):
        fltr = lambda a: True
        if enabled:
            fltr = lambda a: a[1]
        elif disabled:
            fltr = lambda a: not a[1]
        for repo in REPOSITORIES:
            if fltr(repo):
                yield (repo[0], )

class Lister(command.LmiCommandMultiplexer):
    """
    List various types of software data.

    Usage:
        %(cmd)s pkgs [(--installed | --available)]
        %(cmd)s repos [(--enabled | --disabled)]
    """
    COMMANDS = {
            'pkgs'  : ListPackages,
            'repos' : ListRepos
    }
    OWN_USAGE = True

class ShowPackage(command.LmiLister):
    COLUMNS = ("Prop", "Value")

    def execute(self, ns, name):
        pkgd = { p[0] : p for p in PACKAGES }
        if not name in pkgd:
            raise errors.LmiFailed('no such package "%s"' % name)
        for n, v in zip(('Name', 'Architecture', 'Installed'), pkgd[name]):
            yield n, v

class ShowRepository(command.LmiLister):
    COLUMNS = ("Prop", "Value")

    def execute(self, ns, name):
        repod = { r[0] : r for r in REPOSITORIES }
        if not name in repod:
            raise errors.LmiFailed('no such repository "%s"' % name)
        for n, v in zip(('Name', 'Enabled'), repod[name]):
            yield n, v

class Show(command.LmiCommandMultiplexer):
    COMMANDS = {
            'pkg' : ShowPackage,
            'repo' : ShowRepository
    }

Test = command.register_subcommands(
        'Test', __doc__,
        { 'list'    : Lister,
          'show'    : Show,
        },
    )

PACKAGES = (
        # Name, Arch, Installed
        ('pywbem', 'noarch', True),
        ('hwdata', 'noarch', True),
        ('tog-pegasus', 'x86_64', False),
        ('python-docopt', 'noarch', False))

REPOSITORIES = (
        # Name, Enabled
        ('fedora', True),
        ('updates', False))

