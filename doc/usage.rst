`lmi` meta-command usage
========================
``lmi`` meta-command is a command line utility build on top of client-side
libraries. Each library for particular set of providers can declare one or
more commands that will be registered with ``lmi`` meta-command and will be
available to user at command line.

Running from command line
-------------------------
It can run single command given on command line like this: ::

    lmi -h ${hostname} service list --all

Running in interactive mode
---------------------------
Or it can be run in interactive mode when command is omitted: ::

    lmi -h ${hostname}
    lmi> sw search django
    ...
    lmi> sw install python-django
    ...
    lmi> exit

Getting help
------------
For detailed help run: ::

    lmi --help

To get a list of available commands with short descriptions: ::

    lmi help

For help on a particular registered command: ::

    lmi help service

