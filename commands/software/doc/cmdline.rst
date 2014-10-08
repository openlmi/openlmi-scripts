.. _openlmi-scripts-software-cmd:

Software command line reference
===============================

``lmi sw`` is a command for LMI metacommand, which allows to list and manage
rpm packages and repositories on a remote host with installed
:ref:`OpenLMI software provider <openlmi-software-provider>`.

.. note::
    Some operations dealing with many packages can be very time consuming.
    Especially with python implementation of software provider. C
    implementation [#pkgkit]_, using PackageKit as a back-end,  is slightly
    faster. However, the speed is noway near low level tools such as ``YUM``,
    ``DNF``, ``pkcon`` or ``RPM``. Therefore be sure to optimize your queries
    before issuing them.

    For example following commands:

        * ``sw list``
        * ``sw list available``

    may result in several minutes of waiting depending on how many packages are
    available from enabled repositories. If you are interested in specific
    repository, the ``--repoid`` option will give you significant boost.

    The rule of thumb is to shift as much package filtering logic from client
    side to server side as possible. The proper way to achieve this is with
    ``sw search`` command.

.. [#pkgkit] Available since ``openlmi-providers 0.6.0+``.

.. include:: cmdline.generated
