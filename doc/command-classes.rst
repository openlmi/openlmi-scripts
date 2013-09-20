.. _command_classes:

Command classes
===============
Before reading this, please make sure you're familiar with
:ref:`command_wrappers_overview`.

We focus here on commands intended for subclassing in command wrapper modules.
*OpenLMI Scripts* defines and uses other kinds of commands internally. But
the script developer does not need to know about them.

.. seealso::
    General and class specific properties in :ref:`command_properties`.

.. _end-point_commands:

End-point commands
------------------
Were already introduced before (see :ref:`end-point_commands_introduction`).
We'll dive into details here.

Every end-point command allows to verify and transform options parsed by
docopt_ before they are passed to associated function. This can happen in
methods:

``verify_options(self, options)``
    Taking pre-processed options dictionary as a first argument.
    Properties affecting this pre-processing can be found in
    :ref:`pre_processing_properties`. This method shall check option values or
    their combination and raise ``lmi.scripts.common.errors.LmiInvalidOptions``
    if any inconsistency is discovered.

    Example usage: ::

        class FileLister(command.LmiInstanceLister):
            DYNAMIC_PROPERTIES = True

            def verify_options(self, options):
                file_types = { 'all', 'file', 'directory', 'symlink'
                             , 'fifo', 'device'}
                if (   options['--type'] is not None
                   and options['--type'] not in file_types):
                    raise errors.LmiInvalidOptions(
                            'invalid file type given, must be one of %s' %
                                 file_types)

    .. seealso::
        API doccumentation on
        :py:meth:`~lmi.scripts.common.command.endpoint.LmiEndPointCommand.verify_options`

``transform_options(self, options)``
    Takes verified options dictionary. It modifies this dictionary in
    arbitrary way in place. Its return value is ignored.

    Example usage: ::

        class Lister(command.LmiLister):
            COLUMNS = ('Device', 'Name', "ElementName", "Type")

            def transform_options(self, options):
                """
                Rename 'device' option to 'devices' parameter name for better
                readability.
                """
                options['<devices>'] = options.pop('<device>')

    .. seealso::
        API documentation on
        :py:meth:`~lmi.scripts.common.command.endpoint.LmiEndPointCommand.transform_options`

Above methods can be used to process options in a way that any script library
function can be called. In case we need more control over what is called or
when we want to decide at runtime which function shall be called, we may override
:py:meth:`~lmi.scripts.common.command.endpoint.LmiEndPointCommand.execute` method
instead. Example of this may be found at :ref:`associating_a_function`.

.. _lmi_check_result:

``LmiCheckResult``
~~~~~~~~~~~~~~~~~~
This command invokes associated function on hosts in session, collects results
from them and compares them to an expected value. It does not produce any
output, when all returned values are expected.

This command class is very useful when wrapping up some CIM class's method
such as ``LMI_Service::StartService()``. Example can be seen in
:ref:`property_descriptions`.

Its specific properties are listed in :ref:`lmi_check_result_properties`.

.. seealso::
    API documentation on
    :py:class:`~lmi.scripts.common.command.checkresult.LmiCheckResult`

.. _lmi_lister:

``LmiLister``
~~~~~~~~~~~~~
Prints tablelike data. It expects associated function to return its result
in form: ::

    [row1, row2, ...]

Where ``rowX`` is a tuple containing row values. Each such row is ``list`` or
``tuple`` of the same length. There is a property ``COLUMNS`` defining column
names [#]_ (see :ref:`lmi_lister_properties`). Generator is prefered over
a ``list`` of rows. If ``COLUMNS`` property is omitted, returned value shall
take the following form instead: ::

    (columns, data)

Where ``columns`` has the same meaning as ``COLUMNS`` as a class property and
``data`` is the result of previous case [#]_.

.. seealso::
    API documentation on
    :py:class:`~lmi.scripts.common.command.lister.LmiLister`

.. _lmi_instance_lister:

``LmiInstanceLister``
~~~~~~~~~~~~~~~~~~~~~
Is a variant of ``LmiLister``. Instead of rows being tuples, here they are
instances of some CIM class. Instead of using ``COLUMNS`` property for
specifying columns labels, ``PROPERTIES`` is used for the same purpose here.
Its primary use is in specifying which properties of instances shall be
rendered in which column. This is described in detail in
:ref:`lmi_instance_lister_properties`.

The expected output of associated function is therefore: ::

    [instance1, instance2, ...]

Again, usage of generators is preferred.

.. seealso::
    API documentation on
    :py:class:`~lmi.scripts.common.command.lister.LmiInstanceLister`

.. _lmi_show_instance:

``LmiShowInstance``
~~~~~~~~~~~~~~~~~~~
Renders a single instance of some CIM class. It's rendered in a form of
two-column table, where the first column contains property names and
the second their corresponding values. Rendering is controlled in the same
way as for ``LmiInstanceLister`` (see :ref:`lmi_show_instance_properties`).

.. seealso::
    API documentation on
    :py:class:`lmi.scripts.common.command.show.LmiShowInstance`

.. ****************************************************************************

.. _CIM:            http://dmtf.org/standards/cim
.. _OpenLMI:        http://fedorahosted.org/openlmi/
.. _openlmi-tools:  http://fedorahosted.org/openlmi/wiki/shell
.. _docopt:         http://docopt.org/

-------------------------------------------------------------------------------

.. [#] Having the same length as each row in returned data.
.. [#] Generator or a ``list`` of rows.
