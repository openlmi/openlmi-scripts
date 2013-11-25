#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='openlmi-scripts-mylf',
    version='0.0.1',
    description='OpenLMI scripts for LogicalFile profile',
    long_description=long_description,
    author=u'Michal',
    author_email='Minar',
    url='https://github.com/openlmi/openlmi-mylf',
    download_url='https://github.com/openlmi/openlmi-mylf/tarball/master',
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
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.mylf'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'mylf = lmi.scripts.mylf.cmd:MyLF',
            ],
        },
    )
