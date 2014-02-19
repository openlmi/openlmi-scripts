Tests Description
=================
Tests for storage subcommand of lmi meta-command.

Dependencies
------------
 * bash
 * beakerlib
 * openlmi-tools
 * openlmi-scripts-storage, which will be tested

Run
---
Install and run any CIM broker on this or any remote host. Ensure that lmishell
can connect to it. Export these variables:

Export these variables:

 * LMI_CIMOM_URL
 * LMI_CIMOM_USERNAME
 * LMI_CIMOM_PASSWORD
 * LMI_STORAGE_DISK
 * LMI_STORAGE_PARTITIONS

See https://fedorahosted.org/openlmi/wiki/TestGuidelines for details.

Execute:
    $ ./run.sh
