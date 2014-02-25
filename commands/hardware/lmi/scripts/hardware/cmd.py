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
# Author: Peter Schiffer <pschiffe@redhat.com>
#
"""
Display hardware information.

Usage:
    %(cmd)s [all]
    %(cmd)s system
    %(cmd)s motherboard
    %(cmd)s cpu
    %(cmd)s memory

Commands:
    all          Display all available information.
    system       Display system information.
    motherboard  Display motherboard information.
    cpu          Display processor information.
    memory       Display memory information.
"""

from lmi.scripts.common import command

class HwBase(command.LmiLister):
    COLUMNS = []

class All(HwBase):
    CALLABLE = 'lmi.scripts.hardware:get_all_info'

class System(HwBase):
    CALLABLE = 'lmi.scripts.hardware:get_system_info'

class Motherboard(HwBase):
    CALLABLE = 'lmi.scripts.hardware:get_motherboard_info'

class Cpu(HwBase):
    CALLABLE = 'lmi.scripts.hardware:get_cpu_info'

class Memory(HwBase):
    CALLABLE = 'lmi.scripts.hardware:get_memory_info'

Hardware = command.register_subcommands(
        'Hardware', __doc__,
        { 'all'          : All
        , 'system'       : System
        , 'motherboard'  : Motherboard
        , 'cpu'          : Cpu
        , 'memory'       : Memory
        },
        fallback_command=All
    )
