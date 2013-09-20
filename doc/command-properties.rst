.. _command_properties:

Command properties
==================

As noted before in :ref:`end-point_commands`, command at first tries to
process input arguments, calls an associated function and then renders its
result. We'll now introduce properties affecting this process.

Command class properties are written in their bodies and handled by their
metaclasses. After being processed, they are removed from class. So they are
not accessible as class attributes or from their instances.

.. _pre_processing_properties:

Options pre-processing
----------------------
Influencing properties:

    * ``OPT_NO_UNDERSCORES`` (opt_no_underscores_)
    * ``ARG_ARRAY_SUFFIX``   (arg_array_suffix_)
    * ``OWN_USAGE``          (own_usage_)

docopt_ will make a dictionary of options based on usage string such
as the one above (:ref:`usage_string`). Options dictionary matching this
example looks like this: ::

    { 'list'       : bool
    , '--all'      : bool
    , '--disabled' : bool
    , 'start'      : bool
    , '<service>'  : str
    }

Values of this dictionary are passed to an associated function as arguments
with names created out of matching keys. Since argument names can not contain
characters such as `'<'`, `'>'`, `'-'`, etc., these need to be replaced.
Process of renaming of these options can be described by the following pseudo
algorithm:

.. _options_transform_algorithm:

    1. arguments enclosed in brackets are un-surrounded -- brackets get
       removed ::

        "<service>" -> "service"

    2. arguments written in upper case are made lower cased ::

        "FILE" -> "file"

    3. prefix of short and long options made of dashes shall be replaced with
       single underscore ::

        "-a"    -> "_a"
        "--all" -> "_all"

    4. any non-empty sequence of characters not allowed in python's identitier
       shall be replaced with a single underscore ::

        "_long-option"     -> "_long_option"
        "special--cmd-#2"  -> "special_cmd_2"

Points 3 and 4 could be merged into one. But we separate them due to effects
of ``OPT_NO_UNDERSCORES`` property described below.

Property descriptions
~~~~~~~~~~~~~~~~~~~~~
.. _opt_no_underscores:

``OPT_NO_UNDERSCORES`` : ``bool`` (defaults to ``False``)
    Modifies point 3 of options pre-processing. It causes the prefix of dashes
    to be completely removed with no replacement: ::

        "--long-options" -> "long-option"

    This may not be save if there is a command with the same name as the
    option being removed. Setting this property to ``True`` will cause
    overwriting the command with the value of option. A warning shall be
    echoed if such a case occurs.

.. _arg_array_suffix:

``ARG_ARRAY_SUFFIX`` : ``str`` (defaults to ``""``)
    Adds additional point (5) to `options_transform_algorithm`_. All
    repeatable arguments, resulting in a ``list`` of items, are renamed to
    ``<original_name><suffix>`` [#]_. Repeatable argument in usage string
    looks like this: ::

        """
        Usage: %(cmd)s start <service> ...
        """

    Causing all of the ``<service>`` arguments being loaded into a ``list``
    object.

.. _own_usage:

``OWN_USAGE`` : ``bool`` (defaults to ``False``)
    Says whether the documentation string of this class is a usage string.
    Each command in hierarchy can have its own usage string.

    This can also be assigned a usage string directly: ::

        class MySubcommand(LmiCheckResult):
            """
            Class doc string.
            """
            OWN_USAGE = "Usage: %(cmd)s --opt1 --opt1 <file> <args> ..."
            EXPECT = 0

    But using a boolean value is more readable: ::

        class MySubcommand(LmiCheckResult):
            """
            Usage: %(cmd)s --opt1 --opt1 <file> <args> ...
            """
            OWN_USAGE = True
            EXPECT = 0

    .. note::
        
        Using own usage strings in subcommands of top-level commands is not
        recommended. It brings a lot of redundancy and may prove problematic
        to modify while keeping consistency among hierarchically nested
        usages.

        Therefore try to have just one usage string in a top-level command.
        And one top-level command in a single module. Resulting in one usage
        string per one command wrappers module. This makes it easier to read
        and modify.

.. _associating_a_function:

Associating a function
----------------------
Influencing properties:

    * ``CALLABLE`` (callable_)

When command is invoked, its method
:py:meth:`~lmi.scripts.common.command.endpoint.LmiEndPointCommand.execute` will
get verified and transformed options as positional and keyword arguments.
This method shall pass them to an associated function residing in script
library and return its result on completition.

One way to associate a function is to use ``CALLABLE`` property. The other
is to define very own ``execute()`` method like this: ::

    class Lister(command.LmiInstanceLister):
        PROPERTIES = ('Name', "Started", 'Status')

        def execute(self, ns, _all, _disabled, _oneshot):
            kind = 'enabled'
            if _all:
                kind = 'all'
            elif _disabled:
                kind = 'disabled'
            elif _oneshot:
                kind = 'oneshot'
            for service_inst in service.list_services(ns, kind):
                yield service_inst

This may come handy if the application object [#]_ needs to be accessed or
if we need to decide which function to call based on command line options.

.. _property_descriptions:

Property descriptions
~~~~~~~~~~~~~~~~~~~~~
.. _callable:

``CALLABLE`` : ``str`` (defaults to ``None``)
    This is a mandatory option if
    :py:meth:`~lmi.scripts.common.command.endpoint.LmiEndPointCommand.execute`
    method is not overriden. It may be a string composed of a full path of
    module and its callable delimited with ``':'``: ::

        CALLABLE = 'lmi.scripts.service:start'

    Causes function ``start()`` of ``'lmi.scripts.service'`` module to be
    associated with command.

    Callable may also be assigned directly like this: ::

        from lmi.scripts import service
        class Start(command.LmiCheckResult):
            CALLABLE = service.start
            EXPECT = 0

    The first variant (by assigning string) comes handy if the particular
    module of associated function is not yet imported. Thus delaying the
    import until the point of function's invocation - if the execution comes
    to this point at all. In short it speeds up execution of ``lmi``
    meta-command by reducing number of module imports that are not needed.

.. _function_invocation:

Function invocation
-------------------
Influencing properties:

    * ``NAMESPACE`` (namespace_)

Property descriptions
~~~~~~~~~~~~~~~~~~~~~

.. _namespace:

``NAMESPACE`` : ``str`` (defaults to ``None``)
    This property affects the first argument passed to an associated function.
    Various values have different impact:

    +-----------+---------------------------------------+-------------------------------------+
    | Value     | Value of first argument.              | Its type                            |
    +===========+=======================================+=====================================+
    | ``None``  | Same impact as value ``"root/cimv2"`` | :py:class:`lmi.shell.LMINamespace`  |
    +-----------+---------------------------------------+-------------------------------------+
    | ``False`` | Raw connection object                 | :py:class:`lmi.shell.LMIConnection` |
    +-----------+---------------------------------------+-------------------------------------+
    | any path  | Namespace object with given path      | :py:class:`lmi.shell.LMINamespace`  |
    +-----------+---------------------------------------+-------------------------------------+

    This usually won't need any modification. Sometimes perhaps associated
    function might want to access more than one namespace, in that case an
    instance of :py:class:`lmi.shell.LMIConnection` might provide more useful.

    Namespace can also be overriden globally in a configuration file or with
    an option on command line.

Command specific properties
---------------------------
Each command class can have its own specific properties. Let's take a look on
them.

``LmiCommandMultiplexer``
~~~~~~~~~~~~~~~~~~~~~~~~~
.. _commands:

``COMMANDS`` : ``dict`` (mandatory)
    Dictionary assigning subcommands to their names listed in usage string.
    Example follows: ::

        class MyCommand(LmiCommandMultiplexer):
            '''
            My command description.

            Usage: %(cmd)s mycommand (subcmd1 | subcmd2)
            '''
            COMMANDS = {'subcmd1' : Subcmd1, 'subcmd2' : Subcmd2}
            OWN_USAGE = True

    Where ``Subcmd1`` and ``Subcmd2`` are some other ``LmiBaseCommand``
    subclasses. Documentation string must be parseable with docopt_.

    ``COMMANDS`` property will be translated to
    :py:meth:`~lmi.scripts.common.command.multiplexer.LmiCommandMultiplexer.child_commands`
    class method by
    :py:class:`~lmi.scripts.common.command.meta.MultiplexerMetaClass`.

.. _lmi_lister_properties:

``LmiLister`` properties
~~~~~~~~~~~~~~~~~~~~~~~~
.. _columns:

``COLUMNS`` : ``tuple`` (mandatory)
    Column names. It's a tuple with name for each column. Each row of data
    shall then contain the same number of items as this tuple. If omitted,
    associated function is expected to provide them in the first row of
    returned list. It's translated to
    :py:meth:`~lmi.scripts.common.command.lister.LmiBaseListerCommand.get_columns`
    class method.

.. _lmi_instance_commands_properties:
.. _lmi_show_instance_properties:
.. _lmi_instance_lister_properties:

``LmiShowInstance`` and ``LmiInstanceLister`` properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
These two classes expect, as a result of their associated function, an instance
or a list of instances of some CIM class. They take care of rendering them to
standard output. Thus their properties affect the way how their properties
are rendered. 

.. _properties:

``PROPERTIES`` : ``tuple``
    Property names in the same order as the properties shall be listed. Items
    of this tuple can take multiple forms:

    Property Name : ``str``
        Will be used for the name of column/property in output table and the
        same name will be used when obtaining the value from instance. Thus
        this form may be used only if the property name of instance can appear
        as a name of column.

    (Column Name, Property Name) : ``(str, str)``
        This pair allows to render value of property under different name
        (*Column Name*).

    (Column Name, getter) : ``(str, callable)``
        This way allows the value to be arbitrarily computed. The second
        item is a callable taking one and only argument -- the instance of
        class to be rendered.

    Example below shows different ways of rendering attributes for instances
    of ``LMI_Service`` CIM class: ::

        class Show(command.LmiShowInstance):
            CALLABLE = 'lmi.scripts.service:get_instance'
            PROPERTIES = (
                    'Name',
                    ('Enabled', lambda i: i.EnabledDefault == 2),
                    ('Active', 'Started'))

    First property will be shown with the same label as the name of property.
    Second one modifies the value of ``EnabledDefault`` from ``int`` to
    ``bool`` representing enabled state. The last one uses different label for
    property name ``Started``.

.. _dynamic_properties:

``DYNAMIC_PROPERTIES`` : ``bool`` (defaults to ``False``)
    Whether the associated function is expected to return the properties tuple
    itself. If ``True``, the result of associated function must be in form: ::

        (properties, data)

    Where ``properties`` have the same inscription and meaning as a
    ``PROPERTIES`` property of class.

    Otherwise, only the ``data`` is expected.

    .. note::
        Both :py:class:`~lmi.scripts.common.command.show.LmiShowInstance`
        and :py:class:`~lmi.scripts.common.command.lister.LmiInstanceLister`
        expect different ``data`` to be returned. See :ref:`lmi_show_instance`
        and :ref:`lmi_instance_lister` for more information.

.. note::

    Omitting both ``PROPERTIES`` and ``DYNAMIC_PROPERTIES`` makes the
    ``LmiShowInstance`` render all attributes of instance. For
    ``LmiInstanceLister`` this is not allowed, either ``DYNAMIC_PROPERTIES``
    must be ``True`` or ``PROPERTIES`` must be filled.


.. _lmi_check_result_properties:

``LmiCheckResult`` properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This command typically does not produce any output if operation succeeds.
The operation succeeds if the result of associated function is
expected. There are more ways how to say what is an expected result.
One way is to use ``EXPECT`` property. The other is to provide very own
definition of ``check_result()`` method.

.. _expect:

``EXPECT``: (mandatory)
    Any value can be assigned to this property. This value is then expected
    to be returned by associated function. Unexpected result is treated
    as an error.

    A callable object assigned here has special meaning. This object must
    accept exactly two parameters:

        1. options - Dictionary with parsed command line options returned by
           docopt_ after being processed by
           :py:meth:`~lmi.scripts.common.command.endpoint.LmiEndPointCommand.transform_options`.
        2. result - Return value of associated function.

.. seealso::

    Docopt_ home page and its git: http://github.org/docopt/docopt.
    
-------------------------------------------------------------------------------

.. [#] Angle brackets here just mark the boundaries of name components. They
       have nothing to do with arguments.
.. [#] Application object is accessible through ``app`` property of each command instance.

.. ****************************************************************************

.. _CIM:            http://dmtf.org/standards/cim
.. _OpenLMI:        http://fedorahosted.org/openlmi/
.. _openlmi-tools:  http://fedorahosted.org/openlmi/wiki/shell
.. _docopt:         http://docopt.org/
.. _docopt-git:     http://github.org/docopt

