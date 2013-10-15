Python reference for OpenLMI client scripts
===========================================

Main interface functions wrapped with ``lmi`` commands are:

    * :py:func:`~lmi.scripts.hardware.get_all_info`
    * :py:func:`~lmi.scripts.hardware.get_system_info`
    * :py:func:`~lmi.scripts.hardware.get_chassis_info`
    * :py:func:`~lmi.scripts.hardware.get_cpu_info`
    * :py:func:`~lmi.scripts.hardware.get_memory_info`

All of these accept :abbr:`ns (namespace)` object as the first argument.
It is an instance of :py:class:`lmi.shell.LMINamespace`.

Hardware Module API
-------------------
.. automodule:: lmi.scripts.hardware
    :members:
