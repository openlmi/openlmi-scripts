# Storage Management Providers
#
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
# Authors: Jan Safranek <jsafrane@redhat.com>
#
"""
OpenLMI Storage Scripts module is a standard python module, which provides
high-level functions to manage storage on remote hosts with installed
|OpenLMI-Storage provider|.

It is built on top of |LMIShell|, however only very little knowledge about the
|LMIShell| and CIM model are required.

All |LMI metacommands| are implemented using this python module. I.e. everything
that LMI metacommand can do with storage you can do also in python using
this module, which makes it a good start for LMI scripting.

Example::

    # Connect to a remote system using lmishell
    import lmi.shell
    conn = lmi.shell.connect("remote.host.org", "root", "opensesame")

    # Find a namespace we want to operate on, root/cimv2 is the most used.
    ns = conn.root.cimv2

    # Now use lmi.scripts.storage functions.

    # For example, let's partition /dev/vda disk
    from lmi.scripts.storage import partition
    partition.create_partition_table(ns, 'vda', partition.PARTITION_TABLE_TYPE_GPT)
    # Create one large partition on it
    new_partition = partition.create_partition(ns, 'vda')

    # Create a volume group with the partition
    from lmi.scripts.storage import lvm
    new_vg = lvm.create_vg(ns, ['vda1'], 'my_vg')
    print 'New VG name: ', new_vg.Name

    # Create a 100 MB logical volume on the volume group
    MEGABYTE = 1024*1024
    new_lv = lvm.create_lv(ns, new_vg, 'my_lv', 100 * MEGABYTE)

    # Format the LV
    from lmi.scripts.storage import fs
    fs.create_fs(ns, [new_lv], 'xfs')

It is important to note that most of the module functions accept both ``string``
or ``LMIInstance`` as parameters. For example, these two lines would have the
same effect in the example above: ::

    new_lv = lvm.create_lv(ns, 'my_vg', 100*MEGABYTE)

    new_lv = lvm.create_lv(ns, new_vg,  100*MEGABYTE)

The first one use plain ``string`` as a volume group name, while the other uses
LMIShell's ``LMIInstance`` previously returned from ``lvm.create_vg()``.



.. |OpenLMI-Storage provider| replace:: :ref:`OpenLMI-Storage provider <openlmi-storage-provider>`

.. |LMIShell| replace:: :ref:`LMIShell <lmi_shell>`

.. |LMI metacommands| replace:: :ref:`LMI metacommands <openlmi-scripts-storage-cmd>`

"""
