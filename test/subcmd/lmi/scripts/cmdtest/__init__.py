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
    %(cmd)s log <cmd> [<args> ...]
"""

from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common import command
from lmi.scripts.common import configuration

LOG = get_logger(__name__)

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

    def execute(self, ns, enabled, disabled):
        fltr = lambda a: True
        if enabled:
            fltr = lambda a: a[1]
        elif disabled:
            fltr = lambda a: not a[1]
        if self.app.config.verbose:
            props = ('Name', 'Enabled')
        else:
            props = ('Name', )
        yield props
        for repo in REPOSITORIES:
            if not fltr(repo):
                continue
            yield tuple(v for _, v in zip(props, repo))

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
            raise errors.LmiFailed('No such package "%s".' % name)
        for n, v in zip(('Name', 'Architecture', 'Installed'), pkgd[name]):
            yield n, v

class ShowRepository(command.LmiLister):

    def execute(self, ns, name):
        repod = { r[0] : r for r in REPOSITORIES }
        if not name in repod:
            raise errors.LmiFailed('No such repository "%s".' % name)
        if self.app.config.verbose:
            props = ('Name', 'Enabled', 'Packages')
        else:
            props = ('Name', 'Enabled')
        value_map = {n: v for n, v in zip(props, repod[name])}

        return (props, tuple(value_map[p] for p in props))

class Show(command.LmiCommandMultiplexer):
    COMMANDS = {
            'pkg' : ShowPackage,
            'repo' : ShowRepository
    }

class LogLevel(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, _debug, _info, _warn, _error, _critical,
            message=None, args=None):
        for level in ('debug', 'info', 'warn', 'error', 'critical'):
            if locals()['_' + level]:
                break
        if not message:
            message = "This is %s message." % level
        if not args:
            args = []
        getattr(LOG(), level)(message, *args)

class LogAll(command.LmiCheckResult):
    EXPECT = None
    POEM = (
            'One Ring to rule them all.',
            'One Ring to find them.',
            'One Ring to bring them all',
            'and in the darkness bind them.',
            'In the land of Mordor where the Shadows lie.')

    def execute(self, ns, _with_traceback):
        for verse, level in zip(LogAll.POEM,
                ('debug', 'info', 'warn', 'error', 'critical')):
            if _with_traceback:
                try:
                    raise RuntimeError('S**t happens!')
                except RuntimeError as err:
                    getattr(LOG(), level)(verse, exc_info=err)
            else:
                getattr(LOG(), level)(verse)
        if self.app.config.verbose:
            self.app.stdout.write('Additional information.\n')
        if self.app.config.silent:
            self.app.stdout.write("Let's be silent.\n")
        if self.app.config.trace:
            self.app.stdout.write('Enjoy tracebacks.\n')
        if self.app.config.verbosity >= self.app.config.OUTPUT_DEBUG:
            self.app.stdout.write('I can not be more verbose than this!\n')

class LogRaise(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, _lmi_failed=False):
        if _lmi_failed:
            raise errors.LmiFailed("You asked for it!")
        raise RuntimeError("This shall make a nice traceback.")

class Logger(command.LmiCommandMultiplexer):
    """
    Command for logging testing.

    Usage:
        %(cmd)s level (--debug | --info | --warn | --error | --critical)
                [<message> <args>...]
        %(cmd)s all [--with-traceback]
        %(cmd)s raise [--lmi-failed]
    """
    COMMANDS = {
            'level' : LogLevel,
            'all'   : LogAll,
            'raise' : LogRaise
    }
    OWN_USAGE = True

Test = command.register_subcommands(
        'Test', __doc__,
        { 'list'    : Lister,
          'show'    : Show,
          'log'     : Logger,
        },
    )

PACKAGES = (
        # Name, Arch, Installed
        ('pywbem', 'noarch', True),
        ('hwdata', 'noarch', True),
        ('tog-pegasus', 'x86_64', False),
        ('python-docopt', 'noarch', False))

REPOSITORIES = (
        # Name, Enabled, Packages
        ('fedora', True, 1000),
        ('updates', False, 500))

