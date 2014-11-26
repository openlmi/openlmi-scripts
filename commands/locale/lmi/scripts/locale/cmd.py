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
System locale and time management.

Usage:
    %(cmd)s show [(--locale | --vc-keyboard | --x11-keymap | --timedate)]
    %(cmd)s set-locale (<locale> <value>) ...
    %(cmd)s set-vc-keyboard [--convert] <keymap> [<keymap-toggle>]
    %(cmd)s set-x11-keymap [--convert] <layouts> [<model> <variant> <options>]
    %(cmd)s set-time [(--add| --subtract)] <time>
    %(cmd)s set-timezone <timezone>
    %(cmd)s set-local-rtc [--fix-system] (on | off)
    %(cmd)s set-ntp (on | off)

Commands:
    show              Show detailed information about system locale
                      cathegory (locale variables, key mapping on the
                      virtual console, default key mapping of
                      the X11 server, timedate settings).
                      If no cathegory is provided via option, all
                      locale information is displayed.

    set-locale        Set locale variables.

    set-vc-keyboard   Set the key mapping on the virtual console.

    set-x11-keymap    Set the default key mapping of the X11 server.

    set-time          Set the system clock to the specified time. This will
                      also update the RTC time accordingly. The time may be
                      specified in the format "2012-10-30 18:17:16" or as
                      a difference in seconds from current time
                      (see --add/--subtract options).

    set-timezone      Set the system timezone. If the RTC is configured to be
                      maintained in local time it will be updated accordingly.

    set-local-rtc     Set that the RTC is maintained in local time/UTC.

    set-ntp           Enable/disable synchronization of the system clock
                      with a remote NTP server using systemd-timesyncd.

Show options:
    --locale          Display locale variables.
    --vc-keyboard     Display key mapping on the virtual console.
    --x11-keymap      Display default key mapping of the X11 server.
    --timedate        Display timedate settings (system timezone, whether
                      RTC is in local time and whether the system clock is
                      synchronized with with a remote NTP server using
                      systemd-timesyncd).

Set options:
    --convert         Try to set the nearest console keyboard/X11 keyboard
                      setting for the chosen X11 keyboard/console keyboard
                      setting.
    --add             The passed time value is expected to be in seconds and
                      will be added to the current system time.
    --subtract        The passed time value is expected to be in seconds and
                      will be subtracted from the current system time.
    --fix-system      The time from the RTC is read again and the system clock
                      adjusted according to the new setting. (This is useful
                      in cases where the RTC is probably more reliable than the
                      system time.)
"""

from lmi.scripts import locale as loc
from lmi.scripts.common import command

class Show(command.LmiShowInstance):
    DYNAMIC_PROPERTIES = True
    columns = {
        'all': ('Lang', 'LCCType', 'LCNumeric', 'LCTime', 'LCCollate',
                'LCMonetary', 'LCMessages', 'LCPaper', 'LCName', 'LCAddress',
                'LCTelephone', 'LCMeasurement', 'LCIdentification',
                'VConsoleKeymap', 'VConsoleKeymapToggle',
                'X11Layouts', 'X11Model', 'X11Variant', 'X11Options',
                'Timezone', 'NTP', 'LocalRTC'
        ),
        'locale': ('Lang', 'LCCType', 'LCNumeric', 'LCTime', 'LCCollate',
                   'LCMonetary', 'LCMessages', 'LCPaper', 'LCName', 'LCAddress',
                   'LCTelephone', 'LCMeasurement', 'LCIdentification'
        ),
        'vc_keyboard': ('VConsoleKeymap', 'VConsoleKeymapToggle'),
        'x11_keymap': ('X11Layouts', 'X11Model', 'X11Variant', 'X11Options'),
        'timedate': ('Timezone', 'NTP', 'LocalRTC'),
    }

    def execute(self, ns, _locale, _vc_keyboard, _x11_keymap, _timedate):
         cathegory = 'all'
         if _locale:
             cathegory = 'locale'
         elif _vc_keyboard:
             cathegory = 'vc_keyboard'
         elif _x11_keymap:
             cathegory = 'x11_keymap'
         elif _timedate:
             cathegory = 'timedate'
         return self.columns[cathegory], loc.get_locale(ns)

class SetLocale(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'locale' and 'value' options to 'locales' and 'values' parameter
        name for better readability.
        """
        options['<locales>'] = options.pop('<locale>')
        options['<values>'] = options.pop('<value>')

    def execute(self, ns, locales, values):
        loc.set_locale(ns, locales, values)

class SetX11Keymap(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, layouts, model, variant, options, _convert=False):
        if not model:
            model = ''
        if not variant:
            variant = ''
        if not options:
            options = ''
        loc.set_x11_keymap(ns, layouts, model, variant, options, _convert)

class SetVCKeyboard(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, keymap, keymap_toggle, _convert=False):
        if not keymap_toggle:
            keymap_toggle = ''
        loc.set_vc_keyboard(ns, keymap, keymap_toggle, _convert)

class SetTime(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, time, _add=False, _subtract=False):
        loc.set_time(ns, time, _add, _subtract)

class SetTimezone(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, timezone):
        loc.set_timezone(ns, timezone)

class SetLocalRTC(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, on, off, _fix_system=False):
        value=False
        if on:
            value=True
        loc.set_local_rtc(ns, value, _fix_system)

class SetNTP(command.LmiCheckResult):
    EXPECT = None

    def execute(self, ns, on, off):
        value=False
        if on:
            value=True
        loc.set_ntp(ns, value)

Locale = command.register_subcommands(
        'Locale', __doc__,
        { 'show' : Show,
          'set-locale' : SetLocale,
          'set-x11-keymap' : SetX11Keymap,
          'set-vc-keyboard' : SetVCKeyboard,
          'set-time' : SetTime,
          'set-timezone' : SetTimezone,
          'set-local-rtc' : SetLocalRTC,
          'set-ntp' : SetNTP,
        },
    )
