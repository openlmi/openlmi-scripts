Tests Description
=================
Here are tests for 'lmi user' and 'lmi group' commands.

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
 * LMI_ACCOUNT_USER
 * LMI_ACCOUNT_GROUP

See https://fedorahosted.org/openlmi/wiki/TestGuidelines for details.

Execute:
    $ ./test_user.sh
    $ ./test_group.sh
