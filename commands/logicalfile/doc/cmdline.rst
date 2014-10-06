.. _openlmi-scripts-logicalfile-cmd:

Logical File command line reference
===================================

``lmi file`` is a command for LMI metacommand, which allows to query file system
structure on a remote host with installed
:ref:`OpenLMI logicalfile provider <openlmi-logicalfile-provider>`. It can also
create and delete empty directories -- mount points.

It's aim is to provide just that. It is not and won't ever be a general purpose
file manipulation tool. It does not allow to read, write or copy regular files
for security reasons.

.. include:: cmdline.generated
