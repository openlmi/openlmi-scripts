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

"""
Read informations about file system structure.

Usage:
    %(cmd)s list [options] <directory>
    %(cmd)s show [-L] <file>
    %(cmd)s create <directory>
    %(cmd)s delete <directory>

Options:
    -t --type <type>    Filter listed files by their type. One of:
                        any, file, device, directory, fifo, symlink, socket.
                        Defaults to any.
    -L --dereference    Causes symlink to be followed.
"""

from lmi.scripts import mylf
from lmi.scripts.common import command
from lmi.scripts.common import errors

class Show(command.LmiLister):
    COLUMNS = ('Attribute', 'Value')

    def transform_options(self, options):
        options['<path>'] = options.pop('<file>')

    def execute(self, ns, path, _dereference):
        uf = mylf.get_unix_file_instance(ns, path, _dereference)
        lf = mylf.get_logical_file_instance(ns, uf, _dereference)
        return [
            ('Path'        , lf.Name),
            ('Type'        , mylf.logical_file_type_name(lf)),
            ('User ID'     , uf.UserID),
            ('Group ID'    , uf.GroupID),
            ('Size'        , lf.FileSize),
            ('Permissions' , mylf.permission_string(lf))
        ]

class List(command.LmiInstanceLister):
    CALLABLE = mylf.list_directory
    PROPERTIES = (
            'Name',
            ('Type', mylf.logical_file_type_name),
            ('Permissions', mylf.permission_string),
            ('Size', 'FileSize'))

    def verify_options(self, options):
        if (   options['--type'] is not None
           and not options['--type'].lower() in {
               'any', 'file', 'directory', 'symlink', 'dev', 'socket', 'fifo'}):
            raise errors.LmiInvalidOptions(
                    'Unsupported type: %s' % options['--type'])

    def transform_options(self, options):
        file_type = options.pop('--type')
        if file_type is None:
            file_type = 'any'
        options['file-type'] = file_type

class Create(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = mylf.create_directory

class Delete(command.LmiCheckResult):
    EXPECT = None
    CALLABLE = mylf.delete_directory

MyLF = command.register_subcommands('MyLF', __doc__,
        { 'show' : Show
        , 'list' : List
        , 'create' : Create
        , 'delete' : Delete
        })
