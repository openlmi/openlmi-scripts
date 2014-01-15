#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='openlmi-scripts-networking',
    version='0.0.1',
    description='LMI command for network administration.',
    long_description=long_description,
    author=u'Radek Novacek',
    author_email='rnovacek@redhat.com',
    url='https://github.com/openlmi/openlmi-networking',
    download_url='https://github.com/openlmi/openlmi-networking/tarball/master',
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
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.networking'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
                'net = lmi.scripts.networking.cmd:Networking',
            ],
        },
    )
