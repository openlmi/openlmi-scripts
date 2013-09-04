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

Developing lmi scripts.
-----------------------

This documents how to quickly develop lmi scripts without the need to
reinstall python eggs, when anything is changed. This presumes, that the
development process takes place in a git repotory checked out from [git][].
It can be located anywhere on system.

Before we start with setting up an environment, please double check, that you
don't have installed anything from openlmi-scripts in system path
(`/usr/lib/python2.7/site-packages/lmi/scripts` should not exist). And make
sure, that user path is also cleared:

    $ rm -rf $HOME/.local/lib/python2.7/site-packages/lmi*
    $ rm -rf $HOME/.local/lib/python2.7/site-packages/openlmi*

Install all dependencies:

  * python-docopt
  * openlmi-python-base
  * openlmi-tools

Either via rpms or from respective git repositories. For openlmi-python-base
package contained in [providers-git][] repository the setup script is
located at `src/python/setup.py`. In future these will be available from PyPi.

Let's setup an environment:

  1. create a workspace directory for current `$USER` (`WSP`)

      * let's call it a `WSP`
      * this is a place, where our eggs and binaries will be "installed"
      * it can be located anywhere, for example:

            $ WSP=~/.python_workspace
            $ mkdir $WSP

  2. add workspace to your python path to make all modules installed there
     importable (you can add this to your `~/.bashrc`):

        $ export PYTHONPATH=$WSP:$PYTHONPATH

  3. add workspace to your PATH, so the installed binaries can be run:

        $ export PATH=$WSP:$PATH

  4. now let's "install" to our workspace:

      * change to checked out openlmi-scripts repository

            $ cd openlmi-scripts

      * install them and any commands you want -- possibly your own

            $ python setup.py develop --install-dir=$WSP
            $ for cmd in service storage; do
            >     pushd commands/$cmd
            >     python setup.py develop --install-dir=$WSP
            >     popd
            > done

Now any change made to openlmi-scripts is immediately reflected in lmi
meta-command.

------------------------------------------------------------------------------
[git]:           https://github.com/openlmi/openlmi-scripts            "openlmi-scripts"
[providers-git]: ssh://git.fedorahosted.org/git/openlmi-providers.git/ "openlmi-providers"
