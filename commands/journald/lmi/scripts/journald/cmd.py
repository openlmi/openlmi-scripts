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
# Authors: Tomas Bzatek <tbzatek@redhat.com>
#
"""
Journald message log management.

Usage:
    %(cmd)s list [(--reverse | --tail)]
    %(cmd)s logger <message>
    %(cmd)s watch

Commands:
    list        Lists messages logged in the journal
    logger      Logs a new message in the journal
    watch       Watch for newly logged messages

Options:
    --reverse   List messages from newest to oldest
    --tail      List only the last 50 messages
"""
import functools

from lmi.scripts import journald as journ
from lmi.scripts.common import command
from lmi.scripts.common.command import LmiSelectCommand

class Lister(command.LmiCheckResult):
    CALLABLE = journ.list_messages
    EXPECT = 0

    def transform_options(self, options):
        options['reverse'] = options.pop('--reverse')
        options['tail'] = options.pop('--tail')

class Logger(command.LmiCheckResult):
    CALLABLE = journ.log_message
    EXPECT = 0

class Watcher(command.LmiCheckResult):
    CALLABLE = journ.watch
    EXPECT = 0


Journald = command.register_subcommands(
        'Journald', __doc__,
        { 'list'   : Lister
        , 'logger' : Logger
        , 'watch'  : Watcher
        },
    )

class JournaldCMD(LmiSelectCommand):
        """
        Test for provider version requirements
        """
        SELECT = [
                ( 'OpenLMI-Journald >= 0.4.2',
                  # command already defined with register_subcommands()
                  Journald )
                 ]
