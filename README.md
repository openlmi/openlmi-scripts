openlmi-scripts
===============
Client-side python modules and command line utilities.

It comprises of one binary called `lmi` and a common library. `lmi`
meta-command allows to run commands on a set of OpenLMI providers. These
commands can be installed separately in a modular way.

`lmi` is a command line application allowing to run single command on a set
of hosts with just one statement from `shell` or it can run in an
interactive way.

Structure
---------
Following diagram depicts directory structure.

    openlmi-tools
    ├── commands        # base directory for lmi subcommands
    │   ├── service     # service provider comand (service)
    │   │   └── lmi
    │   │       └── scripts
    │   │           └── service
    │   └── software    # software provider command (sw)
    │       └── lmi
    │           └── scripts
    │               └── software
    ├── config          # configuration files for lmi meta-command
    └── lmi             # common client-side library
        └── scripts
            ├── common
            └── _metacommand    # functionality of lmi meta-command

Each subdirectory of `commands/` contains library for interfacing with
particular set of OpenLMI providers. Each contains its own `setup.py` file,
that handles its installation and registration of command. They have one
command thing. Each such `setup.py` must pass `entry_points` dictionary to
the `setup()` function, wich associates commands defined in command library
with its name under `lmi` meta-command.

Dependencies
------------
Code base is written for `python 2.7`.
There are following python dependencies:

 * openlmi-tools
 * python-cliff
 * python-docopt

Installation
------------
Use standard `setuptools` script for installation:

    $ cd openlmi-scripts
    $ python setup.py install --user

This installs just the *lmi meta-command* and client-side library. To install
subcommands, you need to do the same procedure for each particular command
under `commands/` directory.

Usage
-----
To get a help and see available commands, run:

    $ lmi help

To get a help for particular command, run:

    $ lmi help service

To issue single command on a host, run:

    $ lmi --host ${hostname} service list

To start the app in interactive mode:

    $ lmi --host ${hostname}
    > service list --disabled
    ...
    > service start svnserve.service
    ...
    > quit
