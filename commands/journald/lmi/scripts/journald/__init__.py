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

from lmi.scripts.common.errors import LmiFailed
from lmi.shell import LMIIndicationListener
from lmi.scripts.common import get_logger
import socket
import time
import random

NUM_TAIL = 50
LOG = get_logger(__name__)

def list_messages(ns, reverse=False, tail=False):
    """
    List messages from the journal.

    :param boolean reverse: List messages from newest to oldest.
    :param boolean tail: List only the last 50 messages
    """

    inst = ns.LMI_JournalMessageLog.first_instance()
    if not inst:
        raise LmiFailed("Cannot initialize Journald provider. (hint: check if it's installed)")

    if reverse or tail:
        r = inst.PositionToLastRecord()
    else:
        r = inst.PositionToFirstRecord()
    if not 'IterationIdentifier' in r.rparams:
        raise LmiFailed("Cannot initialize Journald iteration. (hint: check SELinux AVCs)")
    iter_id = r.rparams['IterationIdentifier']

    if tail:
        r = inst.PositionAtRecord(IterationIdentifier=iter_id, MoveAbsolute=False, RecordNumber=-NUM_TAIL)
        iter_id = r.rparams['IterationIdentifier']

    try:
        while True:
            r = inst.GetRecord(IterationIdentifier=iter_id, PositionToNext=(not reverse))
            if r.rval != 0:
                break
            iter_id = r.rparams['IterationIdentifier']

            if reverse:
                x = inst.PositionAtRecord(IterationIdentifier=iter_id, MoveAbsolute=False, RecordNumber=-1)
                iter_id = x.rparams['IterationIdentifier']

            print "".join(map(chr, r.rparams['RecordData']))
    except KeyboardInterrupt:
            pass

    inst.CancelIteration(IterationIdentifier=iter_id)

    return 0;


def log_message(ns, message):
    """
    Logs a new message in the journal.

    :param message: A message to log.
    :type message: string
    """
    ns.LMI_JournalLogRecord.create_instance({"CreationClassName": "LMI_JournalLogRecord",
                                             "LogCreationClassName": "LMI_JournalMessageLog",
                                             "LogName": "Journal",
                                             "DataFormat": message})

    LOG().info("Message has been logged.")

    return 0;


def ind_handler(indication, **kwargs):
    exported_objects = indication.exported_objects()
    for i in exported_objects:
        print i["SourceInstance"]["DataFormat"]

def watch(ns):
    """
    Sets up a new indication listener and waits for events.
    """

    indication_port = random.randint(12000, 13000)
    listener = LMIIndicationListener("0.0.0.0", indication_port)
    uniquename = listener.add_handler("lmiscript_journald_watch-XXXXXXXX", ind_handler)
    ret = listener.start()
    if not ret:
        raise LmiFailed("Cannot initialize indication listener on port %d" % indication_port)

    ret = ns.connection.subscribe_indication(
        Name=uniquename,
        Query="SELECT * FROM LMI_JournalLogRecordInstanceCreationIndication WHERE SOURCEINSTANCE ISA LMI_JournalLogRecord",
        Destination="http://%s:%d" % (socket.gethostname(), indication_port)
    )
    if not ret or not ret.rval:
        raise LmiFailed("Failed to register indication: %s\n" % retval.errorstr)

    try:
        LOG().info("Watching journal, press Ctrl+C to abort\n")
        while True:
            time.sleep(1)
            pass

    except KeyboardInterrupt:
            pass

    ns.connection.unsubscribe_indication(uniquename)

    return 0;
