# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Michal Minar <miminar@redhat.com>
# -*- coding: utf-8 -*-

class LmiBaseCommand(object):

    @classmethod
    def is_end_point(cls):
        return True

    def __init__(self, args, kwargs):
        self._cmd_name_args = None
        self.parent = kwargs.pop('parent', None)

    @property
    def cmd_name(self):
        """ Name of this subcommand without as a single word. """
        return self._cmd_name_args[-1]

    @property
    def cmd_full_name(self):
        """
        Name of this subcommand with all prior commands included.
        It's the sequence of commands as given on command line up to this
        subcommand without any options present. In interactive mode
        this won't contain the name of binary (``sys.argv[0]``).

        :rtype: (``str``) Concatenation of all preceding commands with
            ``cmd_name``.
        """
        return ' '.join(self._cmd_name_args)

    @property
    def cmd_name_args(self):
        return self._cmd_name_args[:]
    @cmd_name_args.setter
    def cmd_name_args(self, args):
        if isinstance(args, basestring):
            args = args.split(' ')
        else:
            args = list(args)
        if not isinstance(args, (list, tuple)):
            raise TypeError("args must be a list")
        self._cmd_name_args = args

    @property
    def docopt_cmd_name_args(self):
        """
        Arguments array for docopt parser.
        
        :rtype: (``list``)
        """
        if self.app.interactive_mode:
            return self._cmd_name_args[:]
        return self._cmd_name_args[1:]
