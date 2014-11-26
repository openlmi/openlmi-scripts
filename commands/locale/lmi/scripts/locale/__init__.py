# Copyright (C) 2014 Red Hat, Inc. All rights reserved.
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
# Authors: Vitezslav Crhonek <vcrhonek@redhat.com>
#
"""
LMI Locale Provider client library.
"""

from lmi.scripts.common.errors import LmiFailed
from lmi.scripts.common import get_logger
from datetime import datetime
from calendar import timegm
import time

LOG = get_logger(__name__)

def get_locale(ns):
    """
    Get locale.

    :rtype: LMIInstance/LMI_Locale
    """

    inst = ns.LMI_Locale.first_instance()

    if inst is None:
        raise LmiFailed('Failed to get system locale.')

    return inst

def set_locale(ns, locales, values):
    """
    Set given locale variables with new values.

    :param list locales: List of locale variable names to be set.
    :param list values: List of new values for locale variables.
    """

    inst = get_locale(ns)
    args = {l: v for l, v in zip(locales, values)}

    (rval, _, errorstr) = inst.SetLocale(**args)
    if rval != 0:
        if errorstr:
            raise LmiFailed("Cannot set locale: %s.", errorstr)
        raise LmiFailed("Cannot set locale.")

    for locale in locales:
        LOG().info("Locale variable '%s' set to '%s'.", locale, args[locale])

def set_vc_keyboard(ns, keymap, keymap_toggle, convert):
    """
    Set the key mapping on the virtual console.

    :param string keymap: Requested keyboard mapping for the
        virtual console.
    :param string keymap_toggle: Requested toggle keyboard
        mapping for the virtual console.
    :param bool convert: Whether also X11 keyboard should be set
        to the nearest X11 keyboard setting for the chosen
        console keyboard setting.
    """

    inst = get_locale(ns)

    (rval, _, errorstr) = inst.SetVConsoleKeyboard(
        Keymap=keymap,
        KeymapToggle=keymap_toggle,
        Convert=convert
    )

    LOG().info("Virtual console keyboard set to '%s'.", keymap)
    if keymap_toggle:
        LOG().info("Virtual console toggle keyboard set to '%s'.", keymap_toggle)
    if convert:
        LOG().info("Default X11 keyboard setting may have also changed, "
            "'convert' flag was used.")

def set_x11_keymap(ns, layouts, model, variant, options, convert):
    """
    Set the default key mapping of the X11 server.

    :param string layouts: Requested X11 keyboard mappings.
    :param string model: Requested X11 keyboard model.
    :param string variant: Requested X11 keyboard variant.
    :param string options: Requested X11 keyboard options.
    :param bool convert: Whether also console keyboard should be set
        to the nearest console keyboard setting for the chosen
        X11 keyboard setting.
    """

    inst = get_locale(ns)

    (rval, _, errorstr) = inst.SetX11Keyboard(
        Layouts=layouts,
        Model=model,
        Variant=variant,
        Options=options,
        Convert=convert,
    )

    LOG().info("Default X11 keyboard mapping set to '%s'.", layouts)
    if model:
        LOG().info("Default X11 keyboard model set to '%s'.", model)
    if variant:
        LOG().info("Default X11 keyboard variant set to '%s'.", variant)
    if options:
        LOG().info("Default X11 keyboard options set to '%s'.", options)
    if convert:
        LOG().info("Virtual console keyboard setting may have also changed, "
            "'convert' flag was used.")

def set_time(ns, timeval, add, subtract):
    """
    Set the system clock.

    :param string timeval: New system time or difference in seconds
        from current system time (if relative is True).
    :param bool add: If True, passed time value is expected to be
        in seconds and will be added to the current system time.
    :param bool subtract: If True, passed time value is expected to be
        in seconds and will be subtracted from the current system time.
    """

    inst = get_locale(ns)

    relative = True
    if add:
        usec = int(timeval) * 1000000
    elif subtract:
        usec = int(timeval) * -1000000
    else:
        # time should be specified in the format "2012-10-30 18:17:16"
        try:
            dt = datetime.strptime(timeval, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise LmiFailed("Passed time is not in the correct format "
                "(e. g. '2012-10-30 18:17:16').")
        usec = (timegm(dt.timetuple()) + time.timezone) * 1000000
        relative = False

    (rval, _, errorstr) = inst.SetTime(
        UsecUTC=usec,
        Relative=relative,
    )

    if rval != 0:
        if errorstr:
            raise LmiFailed("Cannot set new system time: %s.", errorstr)
        raise LmiFailed("Cannot set new system time.")

    dt = datetime.now()
    format = dt.strftime("%Y-%m-%d %H:%M:%S")
    LOG().info("System time set to '%s'.", format)

def set_timezone(ns, timezone):
    """
    Set the system timezone.

    :param string timezone: New system timezone.
    """

    inst = get_locale(ns)

    (rval, _, errorstr) = inst.SetTimezone(
        Timezone=timezone)

    if rval != 0:
        if errorstr:
            raise LmiFailed("Cannot set timezone: %s.", errorstr)
        raise LmiFailed("Cannot set timezone.")

    LOG().info("System timezone set to '%s'.", timezone)

def set_local_rtc(ns, value, fix_system):
    """
    Set whether the RTC is maintained in local time/UTC.

    :param bool value: True/False for RTC maintained in localtime/UTC.
    :param bool fix_system: If set, the time is read again from the RTC
        and the system clock adjusted according to the new setting.
    """

    inst = get_locale(ns)

    (rval, _, errorstr) = inst.SetLocalRTC(
        LocalRTC=value,
        FixSystem=fix_system,
    )

    if rval != 0:
        if errorstr:
            raise LmiFailed("Cannot enable/disable NTP: %s.", errorstr)
        raise LmiFailed("Cannot enable/disable NTP.")

    if value:
        LOG().info("RTC is maintained in local time.")
    else:
        LOG().info("RTC is maintained in UTC.")

    if fix_system:
        LOG().info("The time was read again from the RTC and the system "
            "clock adjusted according to the new setting.")

def set_ntp(ns, value):
    """
    Enable/disable synchronization of the system clock
    with a remote NTP server using systemd-timesyncd.

    :param bool value: True/False for NTP enabled/disabled.
    """

    inst = get_locale(ns)

    (rval, _, errorstr) = inst.SetNTP(
        UseNTP=value,
    )

    if rval != 0:
        if errorstr:
            raise LmiFailed("Cannot enable/disable NTP: %s.", errorstr)
        raise LmiFailed("Cannot enable/disable NTP.")

    if value:
        LOG().info("NTP enabled.")
    else:
        LOG().info("NTP disabled.")
