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
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Utility functions used in command sub-package.
"""

import re

RE_OPT_BRACKET_ARGUMENT = re.compile('^<(?P<name>[^>]+)>$')
RE_OPT_UPPER_ARGUMENT = re.compile('^(?P<name>[A-Z]+(?:[_-][A-Z]+)*)$')
RE_OPT_SHORT_OPTION = re.compile('^-(?P<name>[a-z])$', re.IGNORECASE)
RE_OPT_LONG_OPTION = re.compile('^--(?P<name>[a-z_-]+)$', re.IGNORECASE)

def is_abstract_method(clss, method, missing_is_abstract=False):
    """
    Check, whether the given method is abstract in given class or list of
    classes. May be used to check, whether we should override particular
    abstract method in a meta-class in case that no non-abstract
    implementation is defined.

    :param clss: Class or list of classes that is
        searched for non-abstract implementation of particular method.
        If the first class having particular method in this list contain
        non-abstract implementation, ``False`` is returned.
    :type clss: type or tuple
    :param string method: Name of method to look for.
    :param boolean missing_is_abstract: This is a value returned, when
        not such method is defined in a set of given classes.
    :returns: Are all occurences of given method abstract?
    :rtype: boolean
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

