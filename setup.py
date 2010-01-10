#!/usr/bin/python

# BaculaFS - Bacula Filesystem in USErspace
# Copyright (C) 2009, 2010 Avi Rozen <avi.rozen@gmail.com>
#
# BaculaFS contains SQL queries that were adapted from Bacula
# Copyright (C) 2000-2010 Free Software Foundation Europe e.V.
#
# This file is part of BaculaFS.
#
# BaculaFS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Bacula is a registered trademark of Kern Sibbald.

from setuptools import setup, find_packages
from baculafs import __version__

author='Avi Rozen'
author_email='avi.rozen@gmail.com'

setup(
    name='BaculaFS',
    version=__version__,
    description='Bacula Filesystem in USErspace',
    long_description=open('README.rst').read(),
    author=author,
    author_email=author_email,
    maintainer=author,
    maintainer_email=author_email,
    url='http://code.google.com/p/baculafs',
    entry_points = { 'console_scripts': [ 'baculafs = baculafs:main' ] },
    packages = find_packages(),
    license='GPL',
    platforms=['Linux'],
    install_requires=['fuse-python>=0.2','pexpect>=2.3','MySQL-python>=1.2.2','psycopg2>=2.0.13'],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Topic :: System :: Filesystems",
        "Topic :: System :: Archiving :: Backup",
        "Intended Audience :: System Administrators",
        "Environment :: No Input/Output (Daemon)",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        ],
    zip_safe = False,
    )

