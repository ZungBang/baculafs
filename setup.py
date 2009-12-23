#!/usr/bin/python

# FIXME: use python-distribute?

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup

import imp
baculafs = imp.load_source('baculafs', 'baculafs')

setup(
    name='BaculaFS',
    version=baculafs.__version__,
    description='Bacula FUSE File System',
    long_description=open('README.rst').read(),
    author='Avi Rozen',
    author_email='avi.rozen@gmail.com',
    url='http://www.example.com',
    scripts=['baculafs'],
    license='GPL',
    platforms=['Linux'],
    install_requires=['fuse_python>=0.2','pexpect>=2.3'],
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: System :: Archiving :: Backup",
        "Intended Audience :: System Administrators",
        "Environment :: No Input/Output (Daemon)",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        ],
    zip_safe = False,
    )

