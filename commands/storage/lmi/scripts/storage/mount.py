# Storage Management Providers
#
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
# Authors: Jan Synacek <jsynacek@redhat.com>
#

"""
Mounting management functions.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
LOG = get_logger(__name__)
from lmi.scripts.storage import common

_OPTS = ['AllowExecution',
         'AllowMandatoryLock',
         'AllowSUID',
         'AllowUserMount',
         'AllowWrite',
         'Auto',
         'Dump',
         'FileSystemCheckOrder',
         'InterpretDevices',
         'OtherOptions',
         'Silent',
         'SynchronousDirectoryUpdates',
         'SynchronousIO',
         'UpdateAccessTimes',
         'UpdateDirectoryAccessTimes',
         'UpdateFullAccessTimes',
         'UpdateRelativeAccessTimes']

def build_opts_str(mnt):
    """
    Build option strings from an LMI_MountedFileSystem instance.

    :type mnt: an LMIInstance of LMI_MountedFileSystem
    :rtype: tuple of option strings
    """
    opts = []
    otheropts = []
    setting = mnt.associators(ResultClass='LMI_MountedFileSystemSetting')[0]
    for k, v in setting.properties_dict().iteritems():
        if v is None: continue
        if k == 'OtherOptions':
            otheropts = v
        elif k in _OPTS:
            opts.append(k + ':' + unicode(v))
    return (', '.join(sorted(opts)), ', '.join(sorted(otheropts)))

def get_setting_from_opts(ns, options, other_options):
    """
    Create a setting instance from option strings.

    :type options: string of comma-separated options
    :type other_options: string of comma-separated options
    :rtype: an instance of LMI_MountedFileSystemSetting
    """
    cap = ns.LMI_MountedFileSystemCapabilities.first_instance()

    (ret, outparams, _err) = cap.CreateSetting()
    if ret != 0:
        raise LmiFailed('Could not create setting')

    setting = outparams['setting'].to_instance()

    if other_options is not None:
        setting.OtherOptions = other_options.split(',')

    if options is None:
        return setting

    for opt_pair in options.split(','):
        opts = map(lambda o: o.strip(), opt_pair.split(':'))
        # bail out if the option is not in 'Option:Value' format
        # or if the Option is not in supported options
        if len(opts) != 2 or opts[0] not in _OPTS:
            raise LmiFailed('Invalid option: %s' % opt_pair)
        # ignore OtherOptions, there is a separate cmdline option for it
        if opts[0] == 'OtherOptions':
            continue
        # insist on using a number with FileSystemCheckOrder
        if opts[0] == 'FileSystemCheckOrder':
            if not opts[1].isdigit():
                raise LmiFailed('Value of FileSystemCheckOrder must be a number')
            opts[1] = int(opts[1])
        else:
            # otherwise check for true/false possibilities
            opts[1] = opts[1].lower()

            if opts[1] not in ['t', 'true', 'f', 'false']:
                raise LmiFailed('Invalid option value: %s' % opts[1])

            # sanitize the boolean option values
            if opts[1] in ['t', 'true']:
                opts[1] = True
            else:
                opts[1] = False

        setattr(setting, opts[0], opts[1])

    return setting

def get_mounts(ns):
    """
    Return all instances of LMI_MountedFileSystem.

    :rtype: list of LMI_MountedFileSystem
    """
    return ns.LMI_MountedFileSystem.instances()
