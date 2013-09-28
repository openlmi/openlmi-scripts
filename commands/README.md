Subcommands
===========

Each provider has a set of subcommands represented by entry points in
`setup.py` script. They are installed as python eggs. Each such command is
located in its own subdirectory under `commands/`.

Structure
---------
This directory contains all subcommands of lmi metacommand.
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
    │   │   ├── conf.py                 # documentation configuration
    │   │   ├── index.rst               # top-level documentation source
    │   │   ├── Makefile
    │   │   └── python.rst              # library reference source
    │   ├── README.md
    │   └── setup.py
    │   ... ...

Single library under `commands/<provider_prefix>/lmi/scripts` may implement
one or more commands for `lmi` meta-command. To let the meta-command know of
them, they must be listed in `entry_points` in setup file (see below).

There is no limit for complexity of particular command library, it should
provide easy to use interface for any third party python application for
system management of remote hosts. Part of the interface is exported via
commands to `lmi` meta-command. These, by a convention, are defined in
`lmi.scripts.<provider_prefix>.cmd` module.

### Documentation directory
Please stick to the structure presented above. It makes it easy to include
library documents into the global documentation.

 * `cmdline.generated` is a file in [*reStructuredText*][see rst] format generated
   with `tools/help2rst` script from command's usage string.
 * `cmdline.rst` is a file including the one above and providing some additional
   informations related to command's invocation.
 * `python.rst` just lists the modules from `lmi.scripts.<provider_prefix>` to
   document for python reference.
 * `index.rst` binds all the other files together.

### Generating it
You may use `make_new.py` script to generate whole directory structure with
regard to provided data. See its help message:

    $ ./make_new.py --help

Setup file
----------
Allows to install command python egg and register their exported commands to
particular namespace for `lmi` meta-command. The minimal script can look like
this:

    from setuptools import setup
    setup(
        name="<PROJECT>",
        version="<VERSION>",
        install_requires=['openlmi-scripts'],
        namespace_packages=['lmi', 'lmi.scripts'],
        packages=['lmi', 'lmi.scripts', 'lmi.scripts.<provider_prefix>'],
        entry_points={
            'lmi.scripts.cmd': [
                '<CMD_NAME> = lmi.scripts.<provider_prefix>.cmd:<CMD>',
                ],
            },
        )

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

Command module
--------------
Is a python module named (by a convention) `.cmd` under your command library.
It has a documentation string passeable to the `docopt` command line parser
(see `http://docopt.org/`). The structure of this file is following:

    """
    Usage:
       %(cmd)s cmd1 [options]
       %(cmd)s cmd2 [options]

    """
    from lmi.scripts.common import LmiLister, register_subcommands

    class Cmd1(LmiLister):
        CALLABLE = "lmi.scripts.<provider_prefix>:cmd1_func"

    class Cmd2(LmiLister):
        CALLABLE = "lmi.scripts.<provider_prefix>:cmd2_func"

    Entry = register_subcommands(
        'Entry', __doc__,
        { 'cmd1' : Cmd1,
        , 'cmd2' : Cmd2
        },
        requires=["<requirement_string>", ...])

### Usage string
Is very important here. The command line is parsed by
`docopt` according to it. It must conform to POSIX standard for program help.
Please refer to http://docopt.org/ for more information and examples.

One notable detail here is the `%(cmd)s` string for command name. This
is replaced with `lmi CMD_NAME` when running from command line or just
`CMD_NAME` while in interactive mode. It's important to prefix your usage
strings exactly this way. This also means that every `%` character must
be doubled in usage string to avoid collisions in formatting.

### Command classes
Are defined in `lmi.scripts.common.commands` module. They affect the way how
output is rendered to user. Please refer to this module for more information.

### Top level command
Function `register_subcommands` creates top-level command (refered to as
`<CMD>` in section *Setup script* above), which passes control to one
particular subcommand. To let the top-level command know, which command class
instruments which command a mapping must be passed to this function. The
global variable, which holds the result of this call must be listed in
`entry_points` dictionary in `setup.py` script, otherwise it won't be
available in `lmi` meta-command.

### <requirement\_string>
**This is not yet supported feature**

Allows to specify, which profiles and their specific versions are neccessary
to run this command. It's format can be described by following grammar:

    <requirement_string> :
          <instance_id> <op> <version>
        | <instance_id> ;

    <op> : < | > | = | <= | >= | != ;

Where string enclosed in `<>` is a non-terminal symbol. `:` separates
non-terminal symbol from the sequence of possible transcriptions
(right-hand-sides of rules). `|` is a separator of individual transcriptions
and `;` is symbol denoting the end of rules for single symbol.

`<instance_id>` is a value of `LMI_RegisteredProfile::InstanceID` property.

`<version>` is a version that is compared to given comparison operator to the
version of installed profile with matching `InstanceID` on target system. It
must match the following regular expression:

    [0-9]+\.[0-9]+\.[0-9]+

First sequence of digits will be compared with `MajorVersion`, second to
`MinorVersion` and third to the `RevisionNumber` of particular
`LMI_RegisteredProfile` instance.

`class_requirement_string` has equvalent grammar:

    <class_requirement_string> :
          <class_name> <op> <version>
        | <class_name> ;

where `<class_name>` denotes the name of CIM class. And `<version>` the value
of its `Version` qualifier in the mof file.

[rst]: http://sphinx-doc.org/rest.html "reStructuredText"
