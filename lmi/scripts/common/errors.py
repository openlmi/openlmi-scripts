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
"""
Module with predefined exceptions for use in scripts.
"""

class LmiError(Exception):
    """
    The base Lmi scripts error.
    All the other exceptions inherit from it.
    """
    pass

class LmiFailed(LmiError):
    """
    Raised, when operation on remote host failes.
    It's supposed to be used especially in command libraries.
    """
    pass

class LmiInvalidOptions(LmiError):
    """
    Raised in end point command's ``verify_options()`` method if the options
    given are not valid.
    """
    pass

class LmiCommandNotFound(LmiError):
    """ Raised, when user requests not registered command. """
    def __init__(self, cmd_name):
        LmiError.__init__(self, 'failed to find command "%s"' % cmd_name)

class LmiNoConnections(LmiError):
    """ Raised, when no connection to remote hosts could be made. """
    pass

class LmiCommandError(LmiError):
    """ Generic exception related to command declaration. """
    def __init__(self, module_name, class_name, msg):
        LmiError.__init__(self, 'wrong declaration of command "%s.%s": %s'
                % (module_name, class_name, msg))

class LmiCommandInvalidName(LmiCommandError):
    """ Raised, when command gets invalid name. """
    def __init__(self, module_name, class_name, cmd_name):
        LmiCommandError.__init__(self, module_name, class_name,
                'invalid command name "%s"' % cmd_name)

class LmiCommandMissingCallable(LmiCommandError):
    """ Raised, when command declaration is missing callable object. """
    def __init__(self, module_name, class_name):
        LmiCommandError.__init__(self, module_name, class_name,
                'missing CALLABLE property')

class LmiCommandInvalidProperty(LmiCommandError):
    """ Raised, when any command property contains unexpected value. """
    pass

class LmiCommandImportFailed(LmiCommandInvalidProperty):
    """ Raised, when callable object of command could not be imported. """
    def __init__(self, module_name, class_name, callable_prop):
        LmiCommandInvalidProperty.__init__(self, module_name, class_name,
            'failed to import callable "%s"' % callable_prop)

class LmiCommandInvalidCallable(LmiCommandInvalidProperty):
    """ Raised, when given callback is not callable. """
    def __init__(self, module_name, class_name, msg):
        LmiCommandInvalidProperty.__init__(self, module_name, class_name, msg)

class LmiTerminate(Exception):
    """
    Raised to cleanly terminate interavtive shell.
    """
    def __init__(self, exit_code=0):
        Exception.__init__(self, exit_code)
