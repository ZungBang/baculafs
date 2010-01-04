#!/usr/bin/python

from setuptools import setup, find_packages

from baculafs import __version__

setup(
    name='BaculaFS',
    version=__version__,
    description='Bacula FUSE File System',
    long_description=open('README.rst').read(),
    author='Avi Rozen',
    author_email='avi.rozen@gmail.com',
    url='http://www.example.com',
    entry_points = { 'console_scripts': [ 'baculafs = baculafs:main' ] },
    packages = find_packages(),
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

