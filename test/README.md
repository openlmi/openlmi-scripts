Tests Description
=================
Here are tests for lmi meta-command.
Interactive and non-interactive modes are tested.

Dependencies
------------
 * bash
 * beakerlib
 * expect
 * openlmi-tools

Openlmi scripts need not be installed.
 
Run
---
Install and run any CIM broker on this or any remote host. Ensure that lmishell
can connect to it. Export these variables:

 * LMI_CIMOM_URL
 * LMI_CIMOM_USERNAME
 * LMI_CIMOM_PASSWORD

Execute:
    $ ./run.sh
