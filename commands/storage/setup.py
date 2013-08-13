#!/usr/bin/env python

PROJECT = 'lmi-scripts-storage'
VERSION = '0.0.1'

from setuptools import setup, find_packages

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,
    description='LMI command for system storage administration.',
    long_description=long_description,
    author='Jan Safranek',
    author_email='jsafrane@redhat.com',
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
    packages=['lmi.scripts.storage'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'fs = lmi.scripts.storage.fs_cmd:Fs',
            'partition = lmi.scripts.storage.partition_cmd:Partition',
            'partition-table = lmi.scripts.storage.partitiontable_cmd:PartitionTable',
            'raid = lmi.scripts.storage.raid_cmd:Raid',
            ],
        },
    )
