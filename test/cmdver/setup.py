#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='openlmi-scripts-cmdver',
    version='0.1.2',
    description='Test command for versioning.',
    long_description=long_description,
    author=u'Michal Minar',
    author_email='miminar@redhat.com',
    url='https://github.com/openlmi/openlmi-cmdver',
    download_url='https://github.com/openlmi/openlmi-cmdver/tarball/master',
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
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.cmdver'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            # All subcommands of lmi command should go here.
            # See http://pythonhosted.org/openlmi-scripts/script-development.html#writing-setup-py
            'ver-sw = lmi.scripts.cmdver:CmdverSw',
            'ver-hw = lmi.scripts.cmdver:CmdverHw',
            'ver    = lmi.scripts.cmdver:Cmdver',
            ],
        },
    )
