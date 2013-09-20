.. _configuration:

Configuration
=============
``lmi`` meta-command has the main configuration file located in: ::

    /etc/openlmi/scripts/lmi.conf

User can have his own configuration file overriding anything in global one above: ::
    
    $HOME/.lmirc

Configuration is written in MS Windows INI files fashion. Please refer to
corresponding `RFC 822`_ and to `ConfigParser`_ for python specific
interpretation language.

Follows a list of sections with their list of options. Most of the options
listed here can be overriden with command line parameters.

.. seealso::
    :py:mod:`~lmi.scripts.common.configuration`

Section [Main]
--------------
.. _main_command_namespace:

CommandNamespace : ``string``
    Python namespace, where command entry points will be searched for.

    Defaults to ``lmi.scripts.cmd``.

.. _main_trace:

Trace : ``boolean``
    Whether the exceptions should be logged with tracebacks.

    Defaults to ``False``.

.. _main_verbosity:

Verbosity: ``integer``
    A number within 0-2 range saying, how verbosive the output
    shall be. This differs from `log_level`_, which controls the logging
    messages. This option is recognized by commands alone making them
    print more information on stdout.

    Defaults to 0.

Section [CIM]
-------------
.. _cim_namespace:

Namespace : ``string``
    Allows to override default CIM namespace, which will be passed to
    script library functions.

    Defaults to ``root/cimv2``.

Section [SSL]
-------------
.. _ssl_verify_server_certificate:

VerifyServerCertificate : ``boolean``
    Whether to verify server-side certificate, when making secured
    connection over https.

    Defaults to ``True``.


Section [Format]
----------------
.. _format_human_friendly:

HumanFriendly : ``boolean``
    Whether to print values in human readable forms (e.g. with units).

    Defaults to ``False``.

.. _format_lister_format:

ListerFormat : one of {``csv``, ``table``}
    What format to use, when listing tabular data. ``csv`` format allows for
    easy machine parsing, the second one is more human friendly.

    Defaults to ``table``.

.. _format_no_headings:

NoHeadings : ``boolean``
    Whether to suppress headings (column names) when printing tables.

    Defaults to ``False``.

Section [Log]
-------------
.. _log_level:

Level : one of {``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``}
    Minimal serverity level of messages to log. Affects only logging to a
    file.

    Defaults to ``ERROR``.

.. _log_console_format:

ConsoleFormat : ``string``
    Format string used when logging to a console. 

    Defaults to ``%(levelname)s: %(message)s``.

.. _log_file_format:

FileFormat : ``string``
    Format string used, when logging to a console. This applies only when
    *OutputFile* is set (see below).

    Defaults to 
        ``%(asctime)s:%(levelname)-8s:%(name)s:%(lineno)d - %(message)s``

.. _log_output_file:

OutputFile : ``string``
    Allows to set a path to file, where messages will be logged. No log
    file is written at default.

    Defaults to empty string.

.. ****************************************************************************

.. _`RFC 822`: http://tools.ietf.org/html/rfc822.html
.. _`ConfigParser`:        http://docs.python.org/2/library/configparser.html
