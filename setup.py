#!/usr/bin/env python

PROJECT = 'openlmi-scripts'
VERSION = '0.2.1'

# Bootstrap installation of Distribute
from setuptools import setup, find_packages

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,
    description='Client-side library and command-line client',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],

    namespace_packages=['lmi', 'lmi.scripts'],
    packages=[
        'lmi',
        'lmi.scripts',
        'lmi.scripts.common',
        'lmi.scripts.common.command',
        'lmi.scripts.common.formatter',
        'lmi.scripts._metacommand'],
    install_requires=['openlmi-tools', 'docopt >= 0.6'],
    include_package_data=True,
    #data_files=[('/etc/openlmi/scripts', ['config/lmi.conf'])],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'lmi = lmi.scripts._metacommand:main'
            ],
        'lmi.scripts.cmd': [],
        },
    )
