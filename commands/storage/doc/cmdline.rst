LMI command line reference
==========================

These commands allow listing and manipulation with block devices.

Common options
--------------

* `<device>` can be specified as one of:

    * DeviceID of appropriate CIM_StorageExtent. This is internal OpenLMI ID of
      the device and it should be stable across system reboots.

    * Device name directly in /dev directory, such as `/dev/sda`. This device
      name is available as `Name` property of CIM_StorageExtent.

    * Name of MD RAID or logical volume. This method cannot be used when the
      name is not unique, for example when there are two logical volumes with
      the same name, allocated from different volume groups. This name is
      available as `ElementName` property of CIM_StorageExtent.

* `<vg>` represents name of a volume group, with or without `/dev/` prefix.

* Any `<size>`, such as size of new partition or new logical volume, can
  be specified with 'T', 'G', 'M' or 'K' suffix, which represents appropriate
  unit (terabytes, gigabytes etc.) 1K (kilobyte) is 1024 of bytes.
  The suffix is case insensitive, i.e. 1g = 1G.

.. include:: cmdline.generated
