LMI command line reference
==========================

These commands allow listing and manipulation with block devices.


device
------

Basic device information.

Usage:
    device list [<devices>]...
    device show [<devices>]...
    device depends [ --deep ] [<devices>]...
    device provides [ --deep ] [<devices>]...
    device tree [<device>]

Commands:
    list        List short information about given device. If no devices
                are given, all devices are listed.

    show        Show detailed information about given devices. If no devices
                are provided, all of them are displayed.

    provides    Show devices, which are created from given devices
                (= show children of the devices).

                For example, if disk is provided, all partitions on it are
                returned. If 'deep' is used, all RAIDs, Volume Groups and
                Logical Volumes indirectly allocated from it are returned too.

    depends     Show devices, which are required by given devices to operate
                correctly (= show parents of the devices).

                For example, if a Logical Volume is provided, its Volume Group
                is returned. If 'deep' is used, also all Physical Volumes and
                disk are returned.

    tree        Show tree of devices, similar to lsblk.
                (Note that the output is really crude and needs to be worked
                on).

                If no device is provided, all devices are shown, starting
                with physical disks.

                If a device is provided, tree starts with the device
                and all dependent devices are shown.

partition-table
---------------

Partition management.

Usage:
    lmi partition-table list [<devices>]...
    lmi partition-table create [ --gpt | --msdos ] <devices>...
    lmi partition-table show  [<devices>]...

Commands:
    list        List partition tables on given device.
                If no devices are provided, all partition tables are listed.

    create      Create a partition table on given devices. The devices must be
                empty, i.e. must not have any partitions on them. GPT partition
                table is created by default.

    show        Show detailed information about partition table on given
                devices. If no devices are provided, all of them are displayed.


partition
---------

Partition management.

Usage:
    lmi partition list [<devices>]...
    lmi partition create [ --logical | --extended ] <device> [<size>]
    lmi partition delete <partitions>...
    lmi partition show [<partitions>]...

Commands:
    list        List available partitions on given devices.
                If no devices are provided, all partitions are listed.

    create      Create a partition on given device.

                If no size is given, the resulting partition will occupy the
                largest available space on disk.

                The command automatically creates extended and logical
                partitions using these rules:

                * If no partition type (logical or extended) is provided and
                MS-DOS partition is requested and there is extended partition
                already on the device, a logical partition is created.

                * If there is no extended partition on the device and there are
                at most two primary partitions on the device, primary partition
                is created.

                * If there is no extended partition and three primary partitions
                already exist, new extended partition with all remaining space
                is created and a logical partition with requested size is
                created.

    delete      Delete given partitions.

    show        Show detailed information about given partitions. If no
                partitions are provided, all of them are displayed.

Options:
    size        Size of the partition in sectors.
    --logical   Override the automatic behavior and request logical partition.
    --extended  Override the automatic behavior and request extended partition.


raid
----

MD RAID management.

Usage:
    lmi raid list
    lmi raid create [ --name=<name> ] <level> <devices>...
    lmi raid delete <devices>...
    lmi raid show [<devices>]...

Commands:
    list        List all MD RAID devices on the system.

    create      Create MD RAID array with given RAID level from list of devices.

    delete      Delete given MD RAID devices.

    show        Show detailed information about given MD RAID devices. If no
                devices are provided, all MD RAID devices are displayed.


vg
--

Volume Group management.

Usage:
    lmi vg list
    lmi vg create [ --extent-size=<size> ] <name> <devices>...
    lmi vg delete <vgs>...
    lmi vg show [<vgs>]...

Commands:
    list        List all volume groups on the system.

    create      Create Volume Group with given name from list of devices.

    delete      Delete given Volume Groups.

    show        Show detailed information about given Volume Groups. If no
                Volume Groups are provided, all of them are displayed.


lv
---

Logical Volume management.

Usage:
    lmi lv list [<vgs>]...
    lmi lv create <vg> <name> <size>
    lmi lv delete <lvs>...
    lmi lv show [<lvs>]...

Commands:
    list        List available logical volumes on given volume groups.
                If no volume groups are provided, all logical volumes are
                listed.

    create      Create a logical volume on given volume group.

                Size can be specified as number of extents using 'e' suffix,
                e.g. '100e' is 100 extents.

    delete      Delete given logical volume.

    show        Show detailed information about given Logical Volumes. If no
                Logical Volumes are provided, all of them are displayed.


fs
--

Filesystem and other data format management.

Usage:
    lmi fs list [--all] [<devices>]...
    lmi fs create [ --label=<label> ] <type> [<devices>]...
    lmi fs delete <devices>...
    lmi fs list-supported

Commands:
    list        List filesystems and and other data formats (RAID metadata, ...)
                on given devices.
                If no devices are provided, all filesystems are listed.
                If --all option is set, all filesystem, including system ones
                like tmpfs, cgroups, procfs, sysfs etc are listed.

    create      Format device(s) with given filesystem.
                If more devices are given, the filesystem will span
                over these devices (currently supported only by btrfs).

                For list of available filesystem types, see output of
                %(cmd)s list-supported.

    delete      Delete given filesystem or data format (like partition table,
                RAID metadata, LUKS, physical volume metadata etc)
                on given devices.

    list-supported
                List supported filesystems, which can be used as
                %(cmd)s create <type> option.
