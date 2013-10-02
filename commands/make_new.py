#!/usr/bin/python

"""
Create a new command directory structure.

Usage:
    {cmd} [options] <command>

Options:
    -v --version <version>  Version of script library.
                            Defaults to {default_version}.
    -a --author <author>    Full name of library's author.
    -e --email <email>      Author's email address.
    -d --description <description>
                            Short description string.
    -p --project-name <project_name>
"""

from docopt import docopt
from functools import partial
import os
import re
import shutil
import sys
from sphinx import quickstart

RE_COMMAND_NAME = re.compile(r'^([a-z]+(_[a-z]+)*)$')
RE_RST_STATEMENT = re.compile(r'^\s*(:[^:]+:.*)')

DEFAULT_VERSION = '0.0.1'

SETUP_TEMPLATE = \
u"""#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='openlmi-scripts-{name}',
    version={version!r},
    {_description}description={description!r},
    long_description=long_description,
    {_author}author=u'{author}',
    {_email}author_email={email!r},
    url='https://github.com/openlmi/openlmi-{name}',
    download_url='https://github.com/openlmi/openlmi-{name}/tarball/master',
    platforms=['Any'],
    license="BSD",
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],

    install_requires=['openlmi-scripts'],

    namespace_packages=['lmi', 'lmi.scripts'],
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.{name}'],
    include_package_data=True,

    entry_points={{
        'lmi.scripts.cmd': [
            # All subcommands of lmi command should go here.
            # See http://pythonhosted.org/openlmi-scripts/script-development.html#writing-setup-py
            # '<cmd_name> = lmi.scripts.{name}.cmd:<CmdClassName>',
            ],
        }},
    )
"""

BSD_LICENSE_HEADER = \
"""# Copyright (c) 2013, Red Hat, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of the FreeBSD Project.
"""

NAMESPACE_INIT = "__import__('pkg_resources').declare_namespace(__name__)"

DOC_CMDLINE = \
"""LMI command line reference
==========================
..
    Write some description here.

.. include:: cmdline.generated
"""

DOC_PYTHON_REFERENCE = \
"""Python reference for OpenLMI client scripts
===========================================
.. automodule:: lmi.scripts.{name}
    :members:
"""

CMDREGEN_RULE = \
u"""\t@echo " "
\t@echo "  cmdregen   to regenerate cmdline.generated with actual content from installed lmi help"

cmdregen: cmdline.generated

cmdline.generated:
\tif ! python -c 'import lmi.scripts.$(COMMAND_NAME)' >/dev/null; then \\
\t\techo "Please install install the command library first." >&2; \\
\t\texit 1; \\
\tfi
\t( \\
\techo ".."; \\
\techo "    !!!!!!!!!"; \\
\techo -n "    This is generated file. Use 'make cmdregen' to regenerate it"; \\
\techo " from installed 'lmi help <CMD_NAME>'"; \\
\techo "    !!!!!!!!!"; \\
\techo ; \\
\tfor i in `sed -n '/entry_points/,/)/p' ../setup.py | \\
\t\t\tsed -n "s/\\s*,\\?['\\"]\\s*\\([a-z-]\\+\\)\\s*=.*/\\1/p"`; do \\
\t\tlmi help $$i | python ../../../tools/help2rst $$i | \\
\t\t\ttr -d '\\033' |sed 's/..1034h//';  \\
\tdone \\
\t) > $@
"""

def die(msg, *args, **kwargs):
    output = msg.format(*args, **kwargs)
    if isinstance(output, unicode):
        output = output.encode('utf-8')
    sys.stderr.write(output)
    sys.stderr.write('\n')
    sys.exit(1)

try:
    ask = raw_input     # pylint: disable-msg=C0103
except:
    ask = input         # pylint: disable-msg=C0103

def write_init(config, output_path, namespace_package=False):
    with open(output_path, 'w') as init_file:
        init_file.write(BSD_LICENSE_HEADER)
        if namespace_package:
            init_file.write(NAMESPACE_INIT)
            init_file.write('\n')

def write_setup(config, output_path):
    values = { 'name' : str(config['command']) }
    for key, value in config.items():
        if key != 'author' and isinstance(value, unicode):
            value = value.encode('utf-8')
        elif key == 'author' and isinstance(value, str):
            value = value.decode('utf-8')
        values[key] = value
        # comment out arguments with missing value
        values['_' + key] = '#' if not value else ''

    with open(output_path, 'w') as setup_file:
        setup_file.write(SETUP_TEMPLATE.format(**values).encode('utf-8'))

def write_empty(config, output_path):
    with open(output_path, 'w'):
        pass

def write_cmdline(config, output_path):
    with open(output_path, 'w') as cmdline_file:
        cmdline_file.write(DOC_CMDLINE)

def modify_doc_makefile(config, path):
    s_add_cmd, s_add_phony, s_add_cmdregen, s_wait_help_end, s_done = range(5)
    state = s_add_cmd
    new_path = path + '_new'
    with open(path, 'r') as orig:
        with open(new_path, 'w') as new:
            for line in orig.readlines():
                if state == s_add_cmd and line.startswith('BUILDDIR'):
                    new.write(line)
                    new.write(u'COMMAND_NAME := {}\n'.format(
                        config['command']).encode('utf-8'))
                    state = s_add_phony
                elif state == s_add_phony and line.startswith('.PHONY:'):
                    new.write(line[:-1] + ' cmdregen cmdline.generated\n')
                    state = s_add_cmdregen
                elif state == s_add_cmdregen and line.startswith('help:'):
                    new.write(line)
                    state = s_wait_help_end
                elif state == s_wait_help_end and line == '\n':
                    text = CMDREGEN_RULE.format(command=config['command'])+"\n"
                    new.write(text.encode('utf-8'))
                    state = s_done
                else:
                    new.write(line)
    os.remove(path)
    shutil.move(new_path, path)

def modify_doc_index(config, path):
    s_wait_toc, s_wait_empty_line, s_done = range(3)
    state = s_wait_toc
    new_path = path + '_new'
    with open(path, 'r') as orig:
        with open(new_path, 'w') as new:
            for line in orig.readlines():
                if state == s_wait_toc and line.startswith('.. toctree::'):
                    state = s_wait_empty_line
                    new.write(line)
                elif state == s_wait_empty_line and RE_RST_STATEMENT.match(line):
                    new.write('    ' +
                            RE_RST_STATEMENT.match(line).group(1) + '\n')
                elif state == s_wait_empty_line and line == '\n':
                    new.write('\n    cmdline\n    python\n')
                    state = s_done
                else:
                    new.write(line)
    os.remove(path)
    shutil.move(new_path, path)

def make_doc_directory(config, path):
    sphinx_conf = {
            'path'           : path,   # root path
            'sep'            : False,
            'dot'            : '_',
            'project'        : config['project_name'],
            'author'         : config['author'],
            'version'        : config['version'],
            'release'        : config['version'],
            'suffix'         : '.rst',
            'master'         : 'index',
            'epub'           : True,
            'ext_autodoc'    : True,
            'ext_doctest'    : False,
            'ext_interspinx' : True,
            'ext_todo'       : True,
            'ext_coverage'   : False,
            'ext_pngmath'    : True,
            'ext_mathjax'    : False,
            'ext_ifconfig'   : True,
            'ext_viewcode'   : True,
            'makefile'       : True,
            'batchfile'      : True}
    quickstart.generate(sphinx_conf)
    write_cmdline(config, os.path.join(path, 'cmdline.rst'))
    modify_doc_makefile(config, os.path.join(path, 'Makefile'))
    modify_doc_index(config, os.path.join(path, 'index.rst'))

STRUCTURE = {
        'doc' : make_doc_directory,
            # {
            #     'conf.py'     : ...,
            #     'cmdline.rst' : ...,
            #     'python.rst'  : ...,
            #     'index.rst'   : ...,
            #     'Makefile'    : ...,
            # }
        'lmi' : {
            '__init__.py' : partial(write_init, namespace_package=True),
            'scripts' : {
                '__init__.py' : partial(write_init, namespace_package=True),
                '{command}' : {
                    '__init__.py' : write_init
                }
            }
        },
        'setup.py' : write_setup,
        'README.md' : write_empty
}

def make_file(config, filepath, prescription):
    filepath = filepath.format(**config)
    if isinstance(prescription, dict):
        os.mkdir(filepath)
        for filename, presc in prescription.items():
            make_file(config, os.path.join(filepath, filename), presc)
    else:
        prescription(config, filepath)

def make_command(config, base_dir):
    cmd_dir = os.path.join(base_dir, config['command'])
    if os.path.exists(cmd_dir):
        die(u'Command directory "{}" already exists.', config['command'])
    make_file(config, cmd_dir, STRUCTURE)

def parse_command_line(args=None):
    if args is None:
        args = sys.argv[1:]
    usage = __doc__.format(
            cmd=os.path.basename(sys.argv[0]),
            default_version=DEFAULT_VERSION)
    options = docopt(usage, args)
    for opt_name in ('version', 'author', 'email', 'description'):
        options[opt_name] = options.pop('--' + opt_name)
    options['command'] = options.pop('<command>')
    options['project_name'] = options.pop('--project-name')

    if not RE_COMMAND_NAME.match(options['command']):
        die("command name must match regular expression {!r}", RE_COMMAND_NAME.pattern)

    for info, question, default_value in (
            ('version', 'Library version [{default_version}]: ',
                DEFAULT_VERSION),
            ('author',      'Your name:  ', None),
            ('email',       'Your email: ', None),
            ('description', 'Description: ', None)):
        if options.get(info, None):
            continue
        try:
            options[info] = ask(
                    question.format(default_version=DEFAULT_VERSION))
        except EOFError:
            pass
        if not options[info]:
            if default_value is None:
                options[info] = ''
            else:
                options[info] = default_value
    if options['project_name'] is None:
        default = 'OpenLMI {command} scripts'.format(
                command=options['command'].capitalize())
        try:
            options['project_name'] = ask(
                'Project name [{default}]: '.format(default=default))
        except EOFError:
            pass
        if not options['project_name']:
            options['project_name'] = default
    options = {   k: (v.decode('utf-8') if isinstance(v, str) else v)
              for k, v in options.items()}
    return options

def main():
    script_directory = os.path.dirname(sys.argv[0])
    config = parse_command_line()
    if not os.path.samefile(script_directory, os.getcwd()):
        script_directory = os.path.normpath(
                os.path.join(os.getcwd(), script_directory))
    make_command(config, script_directory)

if __name__ == '__main__':
    main()

