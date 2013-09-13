Python reference for OpenLMI client scripts
===========================================

Main interface functions wrapped with ``lmi`` commands are:

    * :py:func:`~lmi.scripts.software.list_installed_packages`
    * :py:func:`~lmi.scripts.software.list_available_packages`
    * :py:func:`~lmi.scripts.software.find_package`
    * :py:func:`~lmi.scripts.software.list_repositories`
    * :py:func:`~lmi.scripts.software.list_package_files`
    * :py:func:`~lmi.scripts.software.get_repository`
    * :py:func:`~lmi.scripts.software.set_repository_enabled`
    * :py:func:`~lmi.scripts.software.install_package`
    * :py:func:`~lmi.scripts.software.install_from_uri`
    * :py:func:`~lmi.scripts.software.remove_package`
    * :py:func:`~lmi.scripts.software.verify_package`

All of these accept :abbr:`ns (namespace)` object as the first argument.
It is an instance of :py:class:`lmi.shell.LMINamespace`.

Software Module API
-------------------
.. automodule:: lmi.scripts.software
    :members:

    
