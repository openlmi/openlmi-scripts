Subcommands
===========
Each provider has a set of subcommands represented by entry points in
`setup.py` script. They are installed as python eggs. Each such command is
located in its own subdirectory under `commands/`.

Structure
---------
This directory contains all subcommands of LMI Meta-command.
It has the following structrure:

    commands
    ├── <provider_prefix>
    │   ├── lmi
    │   │   ├── __init__.py
    │   │   └── scripts                 # namespace package for all subcommands
    │   │       ├── __init__.py
    │   │       └── <provider_prefix>   # library as an interface to providers
    │   │           ├── cmd.py          # definitions of commands
    │   │           └── __init__.py
    │   ├── doc                         # usage and developer documentation
    │   │   ├── cmdline.generated
    │   │   ├── cmdline.rst             # source in reStructured text [rst]
    │   │   ├── conf.py.skel            # documentation configuration
    │   │   ├── index.rst               # top-level documentation source
    │   │   ├── Makefile
    │   │   └── python.rst              # library reference source
    │   ├── README.md
    │   ├── Makefile
    │   └── setup.py.skel
    │   ... ...

Single library under `commands/<provider_prefix>/lmi/scripts` may implement one
or more commands for LMI Meta-command. To let it know of them, they must be
listed in `entry_points` in setup file (see below).

There is no limit for complexity of particular script, it should provide an
easy to use interface for any third party python application for system
management of remote hosts. Part of the interface is exported via commands to
LMI Meta-command. These, by a convention, are defined in
`lmi.scripts.<provider_prefix>.cmd` module.

### Documentation directory
Please stick to the structure presented above. It makes it easy to include
library documents in a global documentation.

 * `cmdline.generated` is a file in [*reStructuredText*][see rst] format generated
   with `tools/help2rst` script from command's usage string.
 * `cmdline.rst` is a file including the one above and providing some additional
   informations related to command's invocation.
 * `python.rst` just lists the modules from `lmi.scripts.<provider_prefix>` to
   document for python reference.
 * `index.rst` binds all the other files together.
 * `conf.py.skel` contains a configuration template with macros replaced
   with correct values when the `Makefile` is being processed.

### Generating it
You may use `make_new.py` script to generate whole directory structure with
regard to provided data. See its help message:

    $ ./make_new.py --help

Setup file
----------
Allows to install command python egg and register their exported commands to
particular namespace for LMI Meta-command. The minimal script can look like
this:

    from setuptools import setup
    setup(
        name="<PROJECT>",
        version="@@VERSION@@",
        install_requires=['openlmi-tools'],
        namespace_packages=['lmi', 'lmi.scripts'],
        packages=['lmi', 'lmi.scripts', 'lmi.scripts.<provider_prefix>'],
        entry_points={
            'lmi.scripts.cmd': [
                '<CMD_NAME> = lmi.scripts.<provider_prefix>.cmd:<CMD>',
                ],
            },
        )

This text needs to be store in `setup.py.skel` file. Regular `setup.py` will be
created out of it when `make setup` is run. `@@VERSION@@` string will be
replaced during this operation with correct version common to all the scripts.

It's advisable to fill more information about your command package like
*description* and *author*. Please refer to python documentation for
setuptools and see already created scripts under `commands/` directory for
examples.

`<CMD>` is a subclass of `lmi.scripts.common.LmiCommandMultiplexer` which
serves as a top-level entry point for particular command entry. See the
description of *Command module* below.

`<CMD_NAME`> is a name of subcommand matching the following regular expression
(python flavor):

    [a-z]+(-[a-z]+)*(\.py)?

For more information please refer to documentation at [script-development][].

[script-development]: http://pythonhosted.org/openlmi-scripts/script-development.html# "Script Development"
[rst]: http://sphinx-doc.org/rest.html "reStructuredText"
