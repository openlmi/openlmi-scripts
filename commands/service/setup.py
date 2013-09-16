#!/usr/bin/env python

PROJECT = 'openlmi-scripts-service'
VERSION = '0.1.0'

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
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.service'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'service = lmi.scripts.service.cmd:Service',
            ],
        },
    )
