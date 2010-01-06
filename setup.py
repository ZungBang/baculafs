#!/usr/bin/python

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
        "Topic :: System :: Archiving :: Backup",
        "Intended Audience :: System Administrators",
        "Environment :: No Input/Output (Daemon)",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        ],
    zip_safe = False,
    )

