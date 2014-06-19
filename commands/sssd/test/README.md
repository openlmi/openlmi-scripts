Tests Description
=================
Here are tests for 'lmi sssd'.

Dependencies
------------
 * bash
 * beakerlib
 * openlmi-tools
 * tested openlmi-scripts, incl. openlmi-scripts-service
 * sssd, libsss_simpleifp and sssd-dbus, all >= 1.12.0-beta2

Run
---
Install and run any CIM broker on this or any remote host. Ensure that lmishell
can connect to it. Export these variables:

 * LMI_CIMOM_URL
 * LMI_CIMOM_USERNAME
 * LMI_CIMOM_PASSWORD


See https://fedorahosted.org/openlmi/wiki/TestGuidelines for details.

Execute:
    $ ./test_sssd.sh


SSSD setup
----------
The tests will destroy any existing sssd configuration!

The tests will prepare sssd in this way:
* configure it: copy etc/sssd.conf to /etc/sssd/sssd.conf
* fill its cache: copy var/* to /var/lib/sss/db
* start it: service sssd start; service sssd-dbus start
-> from now on, sssd uses local cache only with known entries,
   as it cannot reach remote (dummy) LDAP.

