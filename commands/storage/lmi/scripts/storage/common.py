# Software Management Providers
#
# Copyright (C) 2012-2013 Red Hat, Inc.  All rights reserved.
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#

"""
Common storage functionality
"""

from lmi.scripts.common import get_logger
import re
from lmi.shell import LMIInstance
from lmi.scripts.common.errors import LmiFailed

LOG = get_logger(__name__)

def escape_cql(s):
    """
    Escape potentially unsafe string.

    :param s: (``string``) String to escape.
    :retval: Escaped string.
    """
    return re.sub(r'(["\\])', r'\\\1', s)

def str2device(c, device):
    """
    Convert string with name of device to LMIInstance of the device.

    :param c: (``LmiConnection``)
    :param device: (Either ``LMIInstance`` of ``CIM_StorageExtent`` or
    ``string`` with name of device) If ``LMIInstance`` is given, nothing is
    done and the instance is just returned. If string is given, appropriate
    ``LMIInstance`` is looked up and returned.

    :retval: ``LMIInstance`` of appropriate CIM_StorageExtent.

    This functions throws an error when the device cannot be found.
    """
    if isinstance(device, LMIInstance):
        return device
    if not isinstance(device, str):
        raise TypeError("string or LMIInstance expected")
    query = 'SELECT * FROM CIM_StorageExtent WHERE DeviceID="%(device)s" OR Name="%(device)s" OR ElementName="%(device)s"' % {'device': escape_cql(device)}
    devices = c.root.cimv2.wql(query)
    if not devices:
        raise LmiFailed("Device %s not found", (device,))
    if len(devices) > 1:
        raise LmiFailed("Too many devices with name %s found", (device,))

    LOG().debug("String %s translated to device %s",
            device, devices[0].DeviceID)
    return devices[0]


def str2size(size):
    """
    Convert string from human-friendly size to bytes.
    
    :param size: (``string``) Size. Optionally with these suffixes:
      * k, K - kilobytes, 1024 bytes,
      * m, M - megabytes, 1024 * 1024 bytes,
      * g, G - gigabytes, 1024 * 1024 * 1024 bytes,
      * t, T - terabytes, 1024 * 1024 * 1024 * 1024 bytes,
    
    :retval: ``int`` with the size.
    """
    if size.isdigit():
        return int(size)
    suffix = size[-1:]
    s = size[:-1]

    if not s.isdigit():
        raise LmiFailed("'%s' is not valid size." % size)

    multipliers = {
            'k': 1024,
            'm': 1024 * 1024,
            'g': 1024 * 1024 * 1024,
            't': 1024 * 1024 * 1024 * 1024
    }
    m = multipliers.get(suffix, None)
    if not m:
        raise LmiFailed("'%s' has invalid unit." % size)
    return int(s) * m
