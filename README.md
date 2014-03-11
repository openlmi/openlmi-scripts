openlmi-scripts
===============
Client-side python libraries for system management through OpenLMI providers.

It comprises of small python eggs targeted on one or more OpenLMI providers. We
call these eggs scripts. They are installed separately although they can depend
on each other.

They contain python library itself as well as command line interface. This
interface is registered with LMI Meta-command which is a part of OpenLMI Tools.
LMI Meta-command loads it and offers to interface with broker through command
line.

For more information please refer to online documentation on [pythonhosted][].

Structure
---------
Each subdirectory of `commands/` contains library for interfacing with
particular set of OpenLMI providers. Each contains its own `setup.py` file,
that handles its installation and registration of script. They have one common
feature. Each such `setup.py` must pass `entry_points` dictionary to the
`setup()` function, wich associates commands defined in script with its name
with LMI Meta-command.

Dependencies
------------
Code base is written for `python 2.7`.
There are following python dependencies:

 * openlmi-tools >= 0.9.1 ([tools-PyPI][PyPI])
 * python-docopt
 * pandoc

Installation
------------
Use standard `setuptools` script for installation:

    $ cd openlmi-scripts/commands/$CMD
    $ make setup
    $ python setup.py install --user

This installs particular client library and command line interface for
LMI Meta-command.

Script eggs are also available on *PyPI*, install them with:

    $ # add any provider you want to interact with
    $ pip install --user openlmi-scripts-service openlmi-scripts-software

Developing lmi scripts.
-----------------------
This documents how to quickly develop lmi scripts without the need to reinstall
python eggs, when anything is changed. This presumes, that the development
process takes place in a git repository checked out from [git][]. It can be
located anywhere on system.

Before we start with setting up an environment, please double check that you
don't have installed anything from openlmi-scripts in system path
(`/usr/lib/python2.7/site-packages/lmi/scripts` should not exist). And make
sure, that user path is also cleared:

    $ rm -rf $HOME/.local/lib/python2.7/site-packages/lmi*
    $ rm -rf $HOME/.local/lib/python2.7/site-packages/openlmi*

Install all dependencies (named above).

Either via rpms (on Fedora or RHEL) or from respective git repositories or from
[PyPI][].

Let's setup an environment:

  1. Create a workspace directory for current `$USER` (let's call it a `WSP`).
     This is a place, where our eggs and binaries will be "installed".
     It can be located anywhere, for example:

        $ WSP=~/.python_workspace
        $ mkdir $WSP

  2. Add workspace to your python path to make all modules installed there
     importable (you can add this to your `~/.bashrc`):

        $ export PYTHONPATH="$WSP:$PYTHONPATH"

  3. Add workspace to your PATH, so the installed binaries can be run:

        $ export PATH="$WSP:$PATH"

  4. Now let's "install" to our workspace. First `cd` to checked out
     `openlmi-scripts` repository.
  5. Install them and any commands you want -- possibly your own

        $ DEVELOPDIR="$WSP" make develop-all

Now any change made to openlmi-scripts is immediately reflected in LMI
Meta-command.

### Uploading to PyPI
Since *PyPI* expects README file to be in a *reStructuredText* markup
language and the one present is written in *markdown*, it needs to be
converted to it. So please make sure you have `pandoc` installed before
running:

    $ make upload

### Versioning
All the scripts share the same version. Version string resides in `VERSION`
file in root directory. When changed, all `setup.py` scripts need to be
regenerated. This is done with:

    $ make setup-all

### Makefile rules
There are various rules provided to ease the development. Most of them may
be applied to all commands/libraries at once. They are:

  * `clean` - remove temporary and generated files
  * `develop` - install library in developing mode
  * `doc` - build documentation
  * `readme` - create `README.txt` file out of `README.md`
  * `sdist` - creates source tarball in `dist` directory
  * `setup` - writes a `setup.py` and `doc/conf.py` files from their skeletons
  * `upload` - upload to *PyPI*
  * `upload_docs` - upload documentation to [pythonhosted]

Each script's `Makefile` has the same interface. The root `Makefile` is an
exception. It takes care of command libraries. It defines all the rules above
with `-all` suffix. They operate on all subcommands at once. Such rules are:

  * `clean-all`
  * `develop-all`
  * `setup-all`
  * `upload-all`
  * `upload\_docs-all`

To limit the set of commands that shall be processed, the `COMMANDS`
environment variable may be used. For example following command:

    $ COMMANDS='storage software networking' make clean-all

Will clean storage, software and networking directories.

------------------------------------------------------------------------------
[git]:           https://github.com/openlmi/openlmi-scripts                  "openlmi-scripts"
[pythonhosted]:  http://pythonhosted.org/openlmi-tools/index.html            "Python Hosted"
[tools-PyPI]:    https://pypi.python.org/pypi/openlmi-tools                  "Tools on PyPI"
[PyPI]:          https://pypi.python.org/pypi?%3Aaction=search&term=openlmi-scripts&submit=search "Scripts on PyPI"
