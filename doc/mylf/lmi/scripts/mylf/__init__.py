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
import os

from lmi.shell import LMIInstance, LMIInstanceName
from lmi.scripts.common import errors
from lmi.scripts.common import get_logger

LOG = get_logger(__name__)

def logical_file_type_name(file_identity):
    """
    Get a name of file type for supplied instance of ``CIM_LogicalFile``.
    """
    namemap = {
            'lmi_datafile'       : 'file',
            'lmi_unixdevicefile' : 'device',
            'lmi_unixdirectory'  : 'directory',
            'lmi_fifopipefile'   : 'fifo',
            'lmi_symboliclink'   : 'symlink',
            'lmi_unixsocket'     : 'socket'
    }
    try:
        return namemap[file_identity.classname.lower()]
    except KeyError:
        LOG().warn('Unhandled logical file class "%s".',
                file_identity.classname)
        return 'unknown'

def permission_string(file_identity):
    """
    Make a ls-like permission string for supplied instance of
    ``CIM_LogicalFile``.
    """
    return ''.join(l if getattr(file_identity, a) else '-'
              for l, a in zip('rwx', ('Readable', 'Writeable', 'Executable')))

def get_computer_system(ns):
    """
    :returns: Instance of ``Linux_ComputerSystem``.
    """
    if not hasattr(get_computer_system, 'instance'):
        get_computer_system.instance = ns.Linux_ComputerSystem.first_instance()
    return get_computer_system.instance

def get_unix_file_instance(ns, path, dereference=False):
    """
    :param boolean dereference: Whether to follow symbolic links
    :returns: Instance of ``LMI_UnixFile`` corresponding to given *path*.
    """
    cs = get_computer_system(ns)
    uf_name = ns.LMI_UnixFile.new_instance_name({
        'CSCreationClassName' : cs.classname,
        'CSName'              : cs.name,
        'LFName'              : path,
        'LFCreationClassName' : 'ignored',
        'FSCreationClassName' : 'ignored',
        'FSName'              : 'ignored',
    })
    try:
        uf = uf_name.to_instance()
        if dereference:
            lf = get_logical_file_instance(ns, uf, False)
            if logical_file_type_name(lf) == 'symlink':
                try:
                    target = lf.TargetFile
                    if not os.path.isabs(target):
                        target = os.path.abspath(
                                os.path.join(os.path.dirname(lf.Name), target))
                    # recursively try to dereference
                    uf = get_unix_file_instance(ns, target, dereference)
                except Exception as err:
                    LOG.warn('failed to get link target "%s": %s',
                            lf.TargetLink, err)
        return uf
    except:
        raise errors.LmiFailed('No such file or directory: "%s".' % path)

def get_logical_file_instance(ns, file_ident, dereference=False):
    """
    Get an instance of ``CIM_LogicalFile`` corresponding to given file
    identity.

    :param file_ident: Either a file path or an instance of ``LMI_UnixFile``.
    :param boolean dereference: Whether to follow symbolic links
    """
    if isinstance(file_ident, basestring):
        uf = get_unix_file_instance(ns, file_ident, dereference)
    elif isinstance(file_ident, LMIInstanceName):
        uf = file_ident.to_instance()
    else:
        uf = file_ident
    return uf.first_associator(AssocClass='LMI_FileIdentity')

def make_directory_instance_name(ns, directory):
    """
    Retrieve object path of a directory.

    :type directory: string
    :param directory: Full path to the directory.
    :rtype: :py:class:`lmi.shell.LMIInstanceName`
    """
    if directory != '/':
        directory = directory.rstrip('/')
    cs = get_computer_system(ns)
    return ns.LMI_UnixDirectory.new_instance_name(
            { 'CSCreationClassName' : cs.classname
            , 'CSName'              : cs.name
            , 'CreationClassName'   : 'LMI_UnixDirectory'
            , 'FSCreationClassName' : 'LMI_LocalFileSystem'
            , 'FSName'              : ''
            , 'Name'                : directory})

def get_directory_instance(ns, directory):
    """
    Retrieve instance of `LMI_UnixDirectory`.

    :type directory: string of :py:class:`lmi.shell.LMIInstanceName`
    :param directory: Full path to the directory or its instance name.
    :rtype: :py:class:`lmi.shell.LMIInstance`
    """
    if isinstance(directory, basestring):
        directory = make_directory_instance_name(ns, directory)
    if isinstance(directory, LMIInstanceName):
        directory = directory.to_instance()
    return directory

def list_directory(ns, directory, file_type='any'):
    """
    Yields instances of ``CIM_LogicalFile`` representing direct children of the
    given directory.

    :param directory: Either a file path or an instance of
        ``LMI_UnixDirectory``.
    :param file_type: Filter of files made by checking their type. One of: ::
        
        {'any', 'file', 'device', 'directory', 'fifo', 'symlink', 'socket'}
    """
    def _generate_children():
        for child in get_directory_instance(ns, directory).associators(
                AssocClass='LMI_DirectoryContainsFile',
                Role='GroupComponent',
                ResultRole='PartComponent'):
            if (   file_type and file_type != 'any'
               and logical_file_type_name(child) != file_type):
                continue
            yield child
    return sorted(_generate_children(), key=lambda i: i.Name)

def create_directory(ns, directory):
    """
    Create a directory.

    :type directory: string
    :param directory: Full path to the directory.
    """
    ns.LMI_UnixDirectory.create_instance(
            make_directory_instance_name(ns, directory).path.keybindings)

def delete_directory(ns, directory):
    """
    Delete an empty directory.

    :param directory: Either a file path or an instance of
        ``LMI_UnixDirectory``.
    """
    get_directory_instance(ns, directory).delete()
