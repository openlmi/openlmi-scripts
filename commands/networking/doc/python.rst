Python reference for OpenLMI client scripts
===========================================

Main interface functions wrapped with ``lmi`` commands are:

    * :py:func:`~lmi.scripts.networking.get_device_by_name`
    * :py:func:`~lmi.scripts.networking.get_setting_by_caption`
    * :py:func:`~lmi.scripts.networking.list_devices`
    * :py:func:`~lmi.scripts.networking.list_settings`
    * :py:func:`~lmi.scripts.networking.get_mac`
    * :py:func:`~lmi.scripts.networking.get_ip_addresses`
    * :py:func:`~lmi.scripts.networking.get_default_gateways`
    * :py:func:`~lmi.scripts.networking.get_dns_servers`
    * :py:func:`~lmi.scripts.networking.get_available_settings`
    * :py:func:`~lmi.scripts.networking.get_active_settings`
    * :py:func:`~lmi.scripts.networking.get_setting_type`
    * :py:func:`~lmi.scripts.networking.get_setting_ip4_method`
    * :py:func:`~lmi.scripts.networking.get_setting_ip6_method`
    * :py:func:`~lmi.scripts.networking.get_sub_setting`
    * :py:func:`~lmi.scripts.networking.get_applicable_devices`
    * :py:func:`~lmi.scripts.networking.activate`
    * :py:func:`~lmi.scripts.networking.deactivate`
    * :py:func:`~lmi.scripts.networking.create_setting`
    * :py:func:`~lmi.scripts.networking.delete_setting`
    * :py:func:`~lmi.scripts.networking.add_ip_address`
    * :py:func:`~lmi.scripts.networking.remove_ip_address`
    * :py:func:`~lmi.scripts.networking.replace_ip_address`

All of these accept :abbr:`ns (namespace)` object as the first argument.
It is an instance of :py:class:`lmi.shell.LMINamespace`.

Networking Module API
---------------------
.. automodule:: lmi.scripts.networking
    :members:

