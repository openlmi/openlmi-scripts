# LogicalFile Management Providers
#
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
# Authors: Jan Synacek <jsynacek@redhat.com>
#

"""
Logicalfile management functions.
"""

from pywbem import CIMError

from lmi.scripts.common import get_computer_system
from lmi.scripts.common import get_logger
from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common.formatter import command as fcmd
LOG = get_logger(__name__)

def get_file_identification(file_instance):
    """
    Retrieve file identification.

    :type file_instance: LMIInstance
    :param file_instance: The file's instance object.
    :rtype: string
    """
    _CLASSES = {'lmi_datafile':'F',
                'lmi_unixdevicefile':'Dev',
                'lmi_unixdirectory':'Dir',
                'lmi_fifopipefile':'P',
                'lmi_symboliclink':'L',
                'lmi_unixsocket':'S'}
    try:
        return _CLASSES[file_instance.classname.lower()]
    except KeyError:
        return 'Unk'

def get_directory_name_properties(ns, directory):
    """
    Retrieve object path of a directory.

    :type directory: string
    :param directory: Full path to the directory.
    :rtype: LMIInstanceName
    """
    system = get_computer_system(ns)
    return {'CSCreationClassName':system.classname,
            'CSName':system.name,
            'CreationClassName':'LMI_UnixDirectory',
            'FSCreationClassName':'LMI_LocalFileSystem',
            'FSName':'',
            'Name':directory}


def get_directory_instance(ns, directory):
    """
    Retrieve LMIInstance of a directory.

    :type directory: string
    :param directory: Full path to the directory.
    :rtype: LMIInstance
    """
    name = ns.LMI_UnixDirectory.new_instance_name(get_directory_name_properties(ns, directory))
    return name.to_instance()

def walk_cim_directory(directory, depth=0):
    """
    Retrieve all files in a directory.

    If depth is positive, directory is walked recursively up to the given depth.
    Files and directories are yielded as they are encountered.
    This function does not return, it is a generator.

    :type directory: string
    :param directory: Full path to the directory.
    :type depth: integer
    :param depth: Maximum depth to be recursed to.
    """
    content = directory.associators(AssocClass='LMI_DirectoryContainsFile', Role='GroupComponent')
    content = sorted(content, key=lambda x: x.Name)
    dirs = filter(lambda f: f.classname == 'LMI_UnixDirectory', content)

    for f in content:
        yield (f, depth)
        if depth > 0 and f in dirs:
            for i in walk_cim_directory(f, depth - 1):
                yield i

def lf_list(ns, directory, depth=None):
    """
    List all files in a directory.

    If depth is positive, directory is walked recursively up to the given depth.

    :type directory: string
    :param directory: Full path to the directory.
    :type depth: integer
    :param depth: Maximum depth to be recursed to.
    """
    if directory != '/':
        directory = directory.rstrip('/')
    try:
        d = get_directory_instance(ns, directory)
    except:
        raise LmiFailed("Can't list directory: %s" % directory)
    if depth:
        try:
            depth = int(depth)
        except ValueError:
            raise LmiFailed("Depth must be integer.")
    else:
        depth = 0

    for (f, lvl) in walk_cim_directory(d, depth):
        rwx = ''
        rwx += 'r' if f.Readable else '-'
        rwx += 'w' if f.Writeable else '-'
        rwx += 'x' if f.Executable else '-'
        prefix = '  ' * (depth-lvl)
        ident = f.associators(AssocClass='LMI_FileIdentity')[0]
        yield(get_file_identification(f), prefix+f.Name, rwx, ident.SELinuxCurrentContext)

def lf_createdir(ns, directory):
    """
    Create a directory.

    The parent directory must exist.

    :type directory: string
    :param directory: Full path to the directory.
    """
    if directory != '/':
        directory = directory.rstrip('/')
    ns.LMI_UnixDirectory.create_instance(get_directory_name_properties(ns, directory))

def lf_deletedir(ns, directory):
    """
    Delete a directory.

    The directory must be empty.

    :type directory: string
    :param directory: Full path to the directory.
    """
    if directory != '/':
        directory = directory.rstrip('/')
    get_directory_instance(ns, directory).delete()

def lf_show(ns, target):
    """
    Show detailed information about the target.

    Target can be either a file or a directory.

    :type target: string
    :param target: Full path to the target.
    """
    system = get_computer_system(ns)
    uf_name = ns.LMI_UnixFile.new_instance_name(
        {'CSCreationClassName':system.classname,
         'CSName':system.name,
         'LFCreationClassName':'ignored',
         'FSCreationClassName':'ignored',
         'FSName':'ignored',
         'LFName':target})
    try:
        uf = uf_name.to_instance()
    except CIMError as err:
        raise LmiFailed('Could not get target "%s": %s' % (target, err))

    ident = uf.associators(AssocClass='LMI_FileIdentity')[0]

    yield fcmd.NewTableCommand(title=uf.Name)
    yield('Type', get_file_identification(ident))
    yield('Readable', ident.Readable)
    yield('Writeable', ident.Writeable)
    yield('Executable', ident.Executable)
    yield('UserID', uf.UserID)
    yield('GroupID', uf.GroupID)
    yield('SaveText', uf.SaveText)
    yield('SetGid', uf.SetGid)
    yield('SetUid', uf.SetUid)
    yield('FileSize', ident.FileSize)
    yield('LastAccessed', ident.LastAccessed)
    yield('LastModified', ident.LastModified)
    yield('FileInodeNumber', uf.FileInodeNumber)
    yield('SELinuxCurrentContext', uf.SELinuxCurrentContext)
    yield('SELinuxExpectedContext', uf.SELinuxExpectedContext)
