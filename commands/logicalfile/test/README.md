Tests Description
=================
Tests for file subcommand of lmi meta-command.

Dependencies
------------
 * bash
 * beakerlib
 * openlmi-tools

Openlmi scripts need not be installed.
 
Run
---
Install and run any CIM broker on the host where tests are going to be
executed. Install openlmi-logicalfile provider.


*Optionally* export these variables:

 * LMI_CIMOM_URL
 * LMI_CIMOM_USERNAME
 * LMI_CIMOM_PASSWORD

If omitted, local unix socket will be used.

Execute:
    $ ./run.sh
