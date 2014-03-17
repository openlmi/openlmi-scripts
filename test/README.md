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

Remote host shall have `openlmi-software` and `openlmi-hardware` installed. If
not, `LMI_SOFTWARE_PROVIDER_VERSION` and `LMI_HARDWARE_PROVIDER_VERSION` needs
to be set to `none`.
 
Run
---
Install and run any CIM broker on this or any remote host. Ensure that lmishell
can connect to it. Export these variables:

 * LMI_CIMOM_URL
 * LMI_CIMOM_USERNAME
 * LMI_CIMOM_PASSWORD
 * LMI_SOFTWARE_PROVIDER_VERSION    - version of software provider registered
                                      with CIMOM
 * LMI_HARDWARE_PROVIDER_VERSION

Execute:
    $ ./run.sh
