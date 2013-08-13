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
    Escape potentially unsafe string for CQL.

    :type s: string
    :param s: String to escape.
    :rtype: string
    """
    return re.sub(r'(["\\])', r'\\\1', s)

def str2device(c, device):
    """
    Convert string with name of device to LMIInstance of the device.
    If LMIInstance is provided, nothing is done and the instance is just
    returned. If string is given, appropriate LMIInstance is looked up and
    returned.
    This functions throws an error when the device cannot be found.

    :type device: LMIInstance/CIM_StorageExtent or string with name of device
    :param device: Device to convert.
    :rtype: LMIInstance/CIM_StorageExtent
    """
    if isinstance(device, LMIInstance):
        return device
    if not isinstance(device, str):
        raise TypeError("string or LMIInstance expected")
    query = 'SELECT * FROM CIM_StorageExtent WHERE DeviceID="%(device)s" OR Name="%(device)s" OR ElementName="%(device)s"' % {'device': escape_cql(device)}
    devices = c.root.cimv2.wql(query)
    if not devices:
        raise LmiFailed("Device '%s' not found" % (device,))
    if len(devices) > 1:
        raise LmiFailed("Too many devices with name '%s' found" % (device,))

    LOG().debug("String %s translated to device '%s'",
            device, devices[0].DeviceID)
    return devices[0]

multipliers = {
    'B': 1,
    'K': 1024,
    'M': 1024 * 1024,
    'G': 1024 * 1024 * 1024,
    'T': 1024 * 1024 * 1024 * 1024
}


def str2size(size, additional_unit_size=None, additional_unit_suffix=None):
    """
    Convert string from human-friendly size to bytes.
    The string is expected to be integer number, optionally with on of these
    suffixes:

      * k, K - kilobytes, 1024 bytes,
      * m, M - megabytes, 1024 * 1024 bytes,
      * g, G - gigabytes, 1024 * 1024 * 1024 bytes,
      * t, T - terabytes, 1024 * 1024 * 1024 * 1024 bytes,

    :type size: string
    :param size: The size to convert.
    :type additional_unit_size: int
    :param additional_unit_size: Additional unit size for
        additional_unit_suffix, e.g. 4 * 1024*1024 for extent size.
    :type additional_unit_suffix: string
    :param additional_unit_suffix: Additional suffix, e.g. 'E' for extents.
    :rtype: int
    """
    if size.isdigit():
        return int(size)
    suffix = size[-1:]
    s = size[:-1]

    if not s.isdigit():
        raise LmiFailed("'%s' is not valid size." % size)

    m = multipliers.get(suffix.upper(), None)
    if not m:
        if additional_unit_suffix and suffix.upper() == additional_unit_suffix.upper():
            m = additional_unit_size
        else:
            # Sort the units by their size
            units = multipliers.items()
            if additional_unit_suffix:
                units.append((additional_unit_suffix, additional_unit_size))
            units = sorted(units, key=lambda x: x[1])
            raise LmiFailed("'%s' has invalid unit. Known units: %s."
                    % (size, ",".join([unit[0] for unit in units])))
    return int(s) * m

def size2str(size):
    """
    Convert size (in bytes) to human-friendly string converted to KB, MB, ...

    :type size: int
    :param size: Size of something in bytes.
    :rtype: string
    """
    # find the highest multiplier, where the size/multiplier > 1
    mul = 1
    suffix = ''
    for (s, m) in multipliers.iteritems():
        if size / m > 1 and m > mul:
            mul = m
            suffix = s

    # integer numbers with 3- or 4- characters are fine, just round them and
    # add suffix
    if size / mul >= 100:
        size = int(round(size / float(mul)))
        return str(size) + suffix

    # 2- or less character numbers - add floating point and make the output
    # rounded to 4 characters (incl. '.')
    size = size / float(mul)
    decimals = len(str(int(size)))  # nr. of characters before '.'
    size = round(size, 3 - decimals)
    ret = str(size)

    # cut trailing zeroes
    while ret.endswith('0'):
        ret = ret[:-1]
    # cut trailing '.'
    if ret.endswith('.'):
        ret = ret[:-1]

    return ret + suffix

def get_devices(c, devices=None):
    """
    Returns list of block devices.
    If no devices are given, all block devices on the system are returned.

    This functions just converts list of strings to list of appropriate
    LMIInstances.

    :type devices: list of LMIInstance/CIM_StorageExtent or list of strings
    :param devices: Devices to list.

    :rtype: list of LMIInstance/CIM_StorageExtent.
    """
    if devices:
        for dev in devices:
            yield str2device(dev)
    else:
        for dev in c.root.cimv2.CIM_StorageExtent.instances():
            yield dev
