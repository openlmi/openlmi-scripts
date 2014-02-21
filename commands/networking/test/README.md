Tests Description
=================
Here are tests for 'lmi net' commands.

Dependencies
------------
 * bash
 * beakerlib
 * openlmi-tools
 * tested openlmi-scripts

Run
---
Install and run any CIM broker on this or any remote host. Ensure that lmishell
can connect to it. Export these variables:

 * LMI_CIMOM_URL
 * LMI_CIMOM_USERNAME
 * LMI_CIMOM_PASSWORD
 * LMI_NETWORKING_PORTS

See https://fedorahosted.org/openlmi/wiki/TestGuidelines for details.

Execute:
    $ ./test_net.sh
