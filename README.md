openlmi-scripts
===============
Client-side python modules and command line utilities.

It comprises of one binary called `lmi` and a common library. `lmi`
meta-command allows to run commands on a set of OpenLMI providers. These
commands can be installed separately in a modular way.

`lmi` is a command line application allowing to run single command on a set
of hosts with just one statement from `shell` or it can run in an
interactive way.

For more information please refer to online documentation on [pythonhosted][]
or build your own in `doc/` directory.

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

 * openlmi-tools ([PyPI][])
 * python-docopt

### Uploading to PyPI
Since *PyPI* expects README file to be in a *reStructuredText* markup
language and the one present is written in *markdown*, it needs to be
converted to it. So please make sure you have `pandoc` installed before
running:

    $ python setup.py sdist upload

Installation
------------
Use standard `setuptools` script for installation:

    $ cd openlmi-scripts
    $ python setup.py install --user

This installs just the *lmi meta-command* and client-side library. To install
subcommands, you need to do the same procedure for each particular command
under `commands/` directory.

Script eggs are also available on *PyPI*, install them with:

    $ pip install --user openlmi-scripts
    $ # add any provider you want to interact with
    $ pip install --user openlmi-scripts-service openlmi-scripts-software

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

  1. Create a workspace directory for current `$USER` (let's call it a `WSP`).
     This is a place, where our eggs and binaries will be "installed".
     It can be located anywhere, for example:

        $ WSP=~/.python_workspace
        $ mkdir $WSP

  2. Add workspace to your python path to make all modules installed there
     importable (you can add this to your `~/.bashrc`):

        $ export PYTHONPATH=$WSP:$PYTHONPATH

  3. Add workspace to your PATH, so the installed binaries can be run:

        $ export PATH=$WSP:$PATH

  4. Now let's "install" to our workspace. First `cd` to checked out
     openlmi-scripts repository.
  5. Install them and any commands you want -- possibly your own

        $ python setup.py develop --install-dir=$WSP
        $ for cmd in service storage; do
        >     pushd commands/$cmd
        >     python setup.py develop --install-dir=$WSP
        >     popd
        > done

Now any change made to openlmi-scripts is immediately reflected in `lmi`
meta-command.

------------------------------------------------------------------------------
[git]:           https://github.com/openlmi/openlmi-scripts                 "openlmi-scripts"
[providers-git]: https://fedorahosted.org/openlmi/browser/openlmi-providers "openlmi-providers"
[pythonhosted]:  http://pythonhosted.org/openlmi-scripts/index.html         "python hosted"
[PyPI]:          https://pypi.python.org/pypi/openlmi-tools                 "PyPI"
