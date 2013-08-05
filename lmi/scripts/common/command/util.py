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
Utility functions used in command sub-package.
"""

def is_abstract_method(clss, method, missing_is_abstract=False):
    """
    Check, whether the given method is abstract in given class or list of
    classes. May be used to check, whether we should override particular
    abstract method in a meta-class in case that no non-abstract
    implementation is defined.

    :param clss: (``type`` or ``tuple``) Class or list of classes that is
        searched for non-abstract implementation of particular method.
        If the first class having particular method in this list contain
        non-abstract implementation, ``False`` is returned.
    :param method: (``str``) Name of method to look for.
    :param missing_is_abstract: (``bool``) This is a value returned, when
        not such method is defined in a set of given classes.
    :rtype: (``bool``) Are all occurences of given method abstract?
    """
    if (   not isinstance(clss, (list, tuple, set))
       and not isinstance(clss, type)):
        raise TypeError("clss must be either a class or a tuple of classes")
    if not isinstance(method, basestring):
        raise TypeError("method must be a string")
    if isinstance(clss, type):
        clss = [clss]
    for cls in clss:
        if hasattr(cls, method):
            if getattr(getattr(cls, method), "__isabstractmethod__", False):
                return True
            else:
                return False
    return missing_is_abstract

