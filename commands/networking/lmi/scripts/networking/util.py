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
# Authors: Radek Novacek <rnovacek@redhat.com>
#
"""
LMI networking script utilities library.
"""

from lmi.scripts.common.errors import LmiInvalidOptions
import IPy

class IPCheckFailed(LmiInvalidOptions):
    pass

def address_check(address):
    '''
    Check if the IP address is valid.

    :param str address: IP address to check
    :return: tuple of (address, version), where address is cleaned up IP address
             and version is 4 for IPv4 and 6 for IPv6
    :rtype: tuple of (str, int)
    :raises: IPCheckFailed
    '''
    try:
        address_int, version = IPy.parseAddress(address)
    except ValueError:
        raise IPCheckFailed("Invalid IP address: %s" % address)
    address = IPy.intToIp(address_int, version)
    return (address, version)

def prefix_check(prefix, version):
    '''
    Check if the IP prefix is valid

    :param prefix: IP prefix
    :type prefix: str or int
    :param int version: IP version for which is the prefix aimed
    :return: IP prefix
    :rtype: int
    :raises: IPCheckFailed
    '''
    # Check the prefix
    try:
        prefix_int = int(prefix)
    except ValueError:
        raise IPCheckFailed("Invalid prefix: %s" % prefix)
    if (version == 4 and prefix_int > 32) or (version == 6 and prefix_int > 128):
        raise IPCheckFailed("Invalid prefix: %s" % prefix)
    return prefix_int

def netmask_from_prefix(prefix):
    '''
    Convert IPv4 prefix to the netmask

    :param int prefix: IPv4 prefix
    :return: network mask
    :rtype: str
    '''
    try:
        return IPy.IP("0.0.0.0/%s" % prefix).netmask().strFullsize()
    except ValueError:
        raise IPCheckFailed("Invalid prefix: %s" % prefix)

def compare_address(address1, address2):
    address_int1, version1 = IPy.parseAddress(address1)
    address_int2, version2 = IPy.parseAddress(address2)
    if version1 != version2:
        return False
    return address_int1 == address_int2
