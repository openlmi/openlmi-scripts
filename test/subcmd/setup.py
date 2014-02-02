#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="openlmi-scripts-cmdtest",
    version="0.0.1",
    description='Test command for lmi',
    author='Michal Minar',
    author_email='miminar@redhat.com',
    url='http://openlmi.org',
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

    install_requires=['openlmi-scripts >= 0.2.6'],

    namespace_packages=['lmi', 'lmi.scripts'],
    packages=['lmi', 'lmi.scripts', 'lmi.scripts.cmdtest'],
    include_package_data=True,

    entry_points={
        'lmi.scripts.cmd': [
            'test = lmi.scripts.cmdtest:Test',
            ],
        },
    )
