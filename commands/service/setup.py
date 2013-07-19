#!/usr/bin/env python

PROJECT = 'lmi-scripts-service'
VERSION = '0.0.1'

from setuptools import setup, find_packages

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,
    description='LMI command for system service administration.',
    long_description=long_description,
    author='Michal Minar',
    author_email='miminar@redhat.com',
    url='https://github.com/openlmi/openlmi-scripts',
    download_url='https://github.com/openlmi/openlmi-scripts/tarball/master',
    platforms=['Any'],
    license="LGPLv2+",
    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],

    install_requires=['lmi-scripts'],

    namespace_packages=['lmi', 'lmi.scripts'],
    packages=['lmi.scripts.service'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'service = lmi.scripts.service.cmd:Service',
            ],
        },
    )
