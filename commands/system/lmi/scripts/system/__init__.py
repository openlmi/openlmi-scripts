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
LMI system client library.
"""

from lmi.scripts.common import get_computer_system

def _cache_replies(ns, class_name, method):
    """
    Get the reply from cimom and cache it. Cache is cleared
    once the namespace object changes.

    :param str class_name: Name of class to operate on.
    :param str method_name: Name of method to invoke on lmi class object.
    :returns: Whatever the requested method returns.
    """
    if not hasattr(_cache_replies, 'cache'):
        _cache_replies.cache = (ns, {})
    old_ns, cache = _cache_replies.cache
    if old_ns is not ns:
        # keep the cache until namespace object changes
        cache.clear()
        _cache_replies.cache = (ns, cache)
    if not (class_name, method) in cache:
        i = getattr(ns, class_name)
        cache[(class_name, method)] = getattr(i, method)()
    return cache[(class_name, method)]

def get_single_instance(ns, class_name):
    """
    Returns single instance of instance_name.

    :param instance_name: Instance name
    :type instance_name: String
    :returns: Instance of instance_name
    :rtype: :py:class:`lmi.shell.LMIInstance`
    """
    return _cache_replies(ns, class_name, 'first_instance')

def get_all_instances(ns, class_name):
    """
    Returns all instances of instance_name.

    :param instance_name: Instance name
    :type instance_name: String
    :returns: List of instances of instance_name
    :rtype: List of :py:class:`lmi.shell.LMIInstance`
    """
    return _cache_replies(ns, class_name, 'instances')

def get_system_info(ns):
    """
    :returns: Tabular data of all general system information.
    :rtype: List of tuples
    """
    result = get_hostname(ns)
    return result

def get_hostname(ns):
    """
    :returns: Tabular data of system hostname.
    :rtype: List of tuples
    """
    i = get_computer_system(ns)
    return [('Computer Name:', i.Name)]
