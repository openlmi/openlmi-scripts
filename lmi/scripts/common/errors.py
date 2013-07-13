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

class LmiError(Exception):
    pass

class LmiFailed(LmiError):
    pass

class LmiCommandNotFound(LmiError):
    def __init__(self, cmd_name):
        LmiError.__init__(self, 'failed to find command "%s"' % cmd_name)

class LmiNoConnections(LmiError):
    pass

class LmiMissingCommands(LmiError):
    pass

class LmiAlreadyExists(LmiError):
    pass

class LmiInvalidName(LmiError):
    def __init__(self, name):
        LmiError.__init__(self, 'invalid name of egg "%s"' % name)

class LmiCommandError(LmiError):
    def __init__(self, module_name, class_name, msg):
        LmiError.__init__(self, 'wrong declaration of command "%s.%s": %s'
                % (module_name, class_name, msg))

class LmiCommandAlreadyExists(LmiCommandError):
    pass

class LmiCommandInvalidName(LmiCommandError):
    def __init__(self, module_name, class_name, cmd_name):
        LmiCommandError.__init__(self, module_name, class_name,
                'invalid command name "%s"' % cmd_name)

class LmiCommandMissingCallable(LmiCommandError):
    def __init__(self, module_name, class_name):
        LmiCommandError.__init__(self, module_name, class_name,
                'missing CALLABLE property')

class LmiCommandInvalidProperty(LmiCommandError):
    pass

class LmiCommandImportFailed(LmiCommandInvalidProperty):
    def __init__(self, module_name, class_name, callable_prop):
        LmiCommandInvalidProperty.__init__(self, module_name, class_name,
            'failed to import callable "%s"' % callable_prop)

class LmiCommandInvalidCallable(LmiCommandInvalidProperty):
    def __init__(self, module_name, class_name, msg):
        LmiCommandInvalidProperty.__init__(self, module_name, class_name, msg)

