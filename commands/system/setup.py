#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='openlmi-scripts-system',
    version='0.0.2',
    description='Display general system information',
    long_description=long_description,
    author=u'Peter Schiffer',
    author_email='pschiffe@redhat.com',
    url='https://github.com/openlmi/openlmi-system',
    download_url='https://github.com/openlmi/openlmi-system/tarball/master',
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

    install_requires=['openlmi-scripts >= 0.2.7', 'openlmi-scripts-service'],

    namespace_packages=['lmi', 'lmi.scripts'],
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.system'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'system = lmi.scripts.system.cmd:System',
            ],
        },
    )
