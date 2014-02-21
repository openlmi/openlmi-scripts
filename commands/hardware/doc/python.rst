Python reference for OpenLMI client scripts
===========================================

Main interface functions wrapped with ``lmi`` commands are:

    * :py:func:`~lmi.scripts.hardware.get_all_info`
    * :py:func:`~lmi.scripts.hardware.get_system_info`
    * :py:func:`~lmi.scripts.hardware.get_motherboard_info`
    * :py:func:`~lmi.scripts.hardware.get_cpu_info`
    * :py:func:`~lmi.scripts.hardware.get_memory_info`
    * :py:func:`~lmi.scripts.hardware.get_disks_info`

All of these accept :abbr:`ns (namespace)` object as the first argument,
an instance of :py:class:`lmi.shell.LMINamespace`.

Hardware Module API
-------------------
.. automodule:: lmi.scripts.hardware
    :members:
