#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='openlmi-scripts-hardware',
    version='0.0.2',
    description='Hardware information available in OpenLMI hardware providers',
    long_description=long_description,
    author=u'Peter Schiffer',
    author_email='pschiffe@redhat.com',
    url='https://github.com/openlmi/openlmi-hardware',
    download_url='https://github.com/openlmi/openlmi-hardware/tarball/master',
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

    install_requires=['openlmi-scripts >= 0.2.4'],

    namespace_packages=['lmi', 'lmi.scripts'],
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.hardware'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'hwinfo = lmi.scripts.hardware.cmd:Hardware',
            ],
        },
    )
