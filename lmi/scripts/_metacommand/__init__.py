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
Subpackage containing functionality of lmi meta-command.
"""

import argparse
import logging
import sys

from lmi.scripts import common
from lmi.scripts.common import errors
from lmi.scripts._metacommand import util
from lmi.scripts._metacommand.help import Help
from lmi.scripts._metacommand.manager import CommandManager
from lmi.scripts._metacommand.interactive import Interactive
from lmi.scripts._metacommand.toplevel import TopLevelCommand
from lmi.scripts.common.command import LmiCommandMultiplexer, LmiBaseCommand
from lmi.scripts.common.configuration import Configuration
from lmi.scripts.common.session import Session
from lmi.shell import LMIUtil

LOG = common.get_logger(__name__)

# write errors to stderr until logging is configured
logging.getLogger('').addHandler(logging.StreamHandler())

class NullFile(object):
    """
    Mock class implementing toilette for any message passed to it. It mocks
    file object representing standard output stream.

    It implements only the minimum set of methods of ``file`` interface used
    in this application.
    """
    def write(self, *args, **kwargs):
        """ Let's totally ignore what we are given. """
        pass

class MetaCommand(object):
    """
    Main application class. It instantiates configuration object, logging and
    then it passes control to commands.

    Example usage:

        MetaCommand().run()
    """

    def __init__(self):
        # allow exceptions in lmi shell
        LMIUtil.lmi_set_use_exceptions(True)
        # instance of CommandManager, created when first needed
        self._command_manager = None
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.stdin = sys.stdin
        # instance of Session, created when needed
        self._session = None
        # instance of Configuration, created in setup()
        self.config = None
        # dictionary of not yet processed options, it's created in setup()
        self._options = None

    def _configure_logging(self):
        """
        Setup logging. It expects Configuration object to be already
        initialized.

        Logging can be tuned in various ways:

            * In configuration file with options:
                * [Main] Verbosity
                * [Log] OutputFile
                * [Log] FileFormat
                * [Log] ConsoleFormat
                * [Log] LogToConsole
            * With command line options:
                ``-v`` flags :
                    Each such flag increases logging level of what is logged
                    into console. This overrides `[Main] Verbosity` option.
                ``-q`` :
                    Causes supression of any output made to stdout except for
                    critical messages. This overrides ``[Main] Verbosity``.
                    option and ``-v`` flags.
                ``--log-file`` :
                    Output file for logging messages. This overrides ``[Log]
                    OutputFile`` option.

        Implicitly only warnings and errors are logged to the standard error
        stream without any tracebacks.
        """
        util.setup_logging(self.config, self.stderr)
        if self.config.silent:
            self.stdout = NullFile()

    @property
    def command_manager(self):
        """
        Return instance of ``CommandManager``. It's initialized when first
        needed.

        :rtype: (``CommandManager``)
        """
        if self._command_manager is None:
            self._command_manager = CommandManager()
            self._command_manager.add_command('help', Help)
        return self._command_manager

    @property
    def session(self):
        """
        Return instance of Session. Instantiated when first needed.

        :rtype: (``Session``)
        """
        if self._session is None:
            if (   not self._options['--host']
               and not self._options['--hosts-file']):
                LOG().info('no hosts given, using "localhost"')
                self._options['--host'] = ['localhost']
            hostnames = []
            # credentials loaded from file
            credentials = {}
            def add_hosts(hosts, creds):
                """ Update hostnames and credentials for new data. """
                hostnames.extend(hosts)
                credentials.update(creds)
            if self._options['--hosts-file']:
                hosts_path = self._options['--hosts-file']
                try:
                    with open(hosts_path, 'r') as hosts_file:
                        add_hosts(*util.parse_hosts_file(hosts_file))
                except (OSError, IOError) as err:
                    LOG().critical('could not read hosts file "%s": %s',
                            hosts_path, err)
                    sys.exit(1)
            add_hosts(*util.get_hosts_credentials(self._options['--host']))
            if self._options['--user']:
                credentials.update({
                        # credentials in file has precedence over --user option
                        h : credentials.get(h, (self._options['--user'], ''))
                    for h in hostnames if h not in credentials
                })
            self._session = Session(self, hostnames, credentials,
                    same_credentials=self._options['--same-credentials'])
        return self._session

    def print_version(self):
        """ Print version of this egg to stdout. """
        self.stdout.write("%s\n" % util.get_version())

    def setup(self, options):
        """
        Initialise global Configuration object and set up logging.

        :param options: (``dict``) Dictionary of options parsed from command
            line by docopt.
        """
        conf_kwargs = {}
        if options['--config-file']:
            conf_kwargs['user_config_file_path'] = options.pop('--config-file')
        self.config = Configuration.get_instance(**conf_kwargs)
        # two mutually exclusive options
        if options['--trace'] or options['--notrace']:
            self.config.trace = bool(options['--trace'])
        if options.pop('--quiet', False):
            self.config.verbosity = Configuration.OUTPUT_SILENT
        elif options['-v'] and options['-v'] > 0:
            self.config.verbosity = options['-v']
        if options.pop('--noverify', False):
            self.config.verify_server_cert = False
        self._configure_logging()
        del options['--trace']
        del options['--notrace']
        del options['-v']
        self.config.namespace = options.pop('--namespace', None)
        self.config.human_friendly = options.pop('--human-friendly', None)
        self.config.no_headings = options.pop('--no-headings', None)
        self.config.lister_format = options.pop('--lister-format', None)
        self.config.log_file = options.pop('--log-file', None)
        # unhandled options may be used later (for session creation),
        # so let's save them
        self._options = options

    def run(self, argv):
        """
        Equivalent to the main program for the application.

        :param argv: (``list``) Input arguments and options.
            Contains all arguments but the application name.
        """
        cmd = TopLevelCommand(self)
        try:
            retval = cmd.run(argv)
        except Exception as exc:
            trace = True if self.config is None else self.config.trace
            if isinstance(exc, errors.LmiError) or not trace:
                LOG().error(exc)
            else:
                LOG().exception("fatal")
            return 1
        if isinstance(retval, bool) or not isinstance(retval, (int, long)):
            return 0 if bool(retval) or retval is None else 1
        return retval

def main(argv=sys.argv[1:]):
    """
    Main entry point function. It just passes arguments to instantiated
    ``MetaCommand``.
    """
    return MetaCommand().run(argv)

