========
BaculaFS
========

BaculaFS_ - Exposes the Bacula_ catalog and storage as a Filesystem in
USErspace (FUSE_).

.. _BaculaFS: http://code.google.com/p/baculafs
.. _Bacula: http://www.bacula.org
.. _FUSE: http://fuse.sourceforge.net/

Copyright (C) 2009, 2010 Avi Rozen <avi.rozen@gmail.com>

INTRODUCTION
------------

**BaculaFS** is a tool, independent of Bacula, that represents the
Bacula catalog and backup storage media as a read-only filesystem in
userspace.

**BaculaFS** is specifically designed to cater for the following
use-cases:

- maintaining a remote snapshot of the files in the backup storage
  using `rsync`_
- auditing the contents of backup jobs, without resorting to SQL
  queries
- comparing backup jobs (using several mount points)

Note that **BaculaFS** is a maintenance tool - it's operation may
interfere with the normal operation of a live Bacula setup (see the
LIMITATIONS_ section below).


.. _rsync: http://samba.anu.edu.au/rsync/


REQUIREMENTS
------------

**BaculaFS** has been tested with the following set of required
software packages:

+ Bacula 3.0.2 with one of the following database backends:

  * SQLite_ 3.6.21
  * MySQL_ 5.4.1
  * PostgreSQL_ 8.3.9
  
+ FUSE_ components:

  * Python FUSE 0.2
  * FUSE library 2.8.1
  * fusermount 2.8.1
  * FUSE kernel interface 7.12

+ Python_ 2.5.4, with the following additional libraries:

  * MySQLdb_ 1.2.2
  * psycopg2_ 2.0.13
  * pexpect_ 2.3 
  
+ attr_ extended attributes utilities 2.4.44

**BaculaFS** requires the following in order to function:

+ access to the database that's used to store the Bacula catalog
+ access to the Bacula storage device
+ access to the Bacula ``bextract`` utility (bundled with the Bacula
  storage daemon installation)

.. _SQLite: http://www.sqlite.org/
.. _MySQL: http://www.mysql.com/
.. _PostgreSQL: http://www.postgresql.org/
.. _Python: http://www.python.org
.. _FUSE: http://fuse.sourceforge.net/
.. _psycopg2: http://initd.org/projects/psycopg
.. _MySQLdb: http://mysql-python.sourceforge.net/
.. _pexpect: http://www.noah.org/wiki/Pexpect
.. _attr: http://savannah.nongnu.org/projects/attr


INSTALLATION
------------

Extract the source code archive to a temporary directory, ``cd`` to
this directory and run

::

        python setup.py install

USAGE
-----

::

   baculafs [mountpoint] [options]
   
   Options:
       --version              show program's version number and exit
       -h, --help             show this help message and exit
       -o opt,[opt...]        mount options
       -o driver=mysql|postgresql|sqlite|sqlite3
                              database driver [default: sqlite3]
       -o host=HOST           database server address [default: localhost]
       -o port=PORT           database server port
       -o database=PATH       database name [default: bacula]
       -o username=USERNAME   database user name [default: bacula]
       -o password=PASSWORD   database password
       -o conf=PATH           storage daemon configuration file [default:
                              /etc/bacula/bacula-sd.conf]
       -o client=CLIENT       file daemon name
       -o fileset=FILESET     backup fileset
       -o device=DEVICE       storage device name [default: FileStorage]
       -o datetime='YYYY-MM-DD hh:mm:ss'
                              snapshot date/time [default: now]
       -o recent_job          select contents of most recent job only [default:
                              False]
       -o joblist='JOBID1 JOBID2 ...'
                              select contents of specified list of jobs
       -o cleanup             clean cache directory upon umount  [default: False]
       -o move_root           make absolute path symlinks point to path under
                              mount point  [default: False]
       -o prefetch_attrs      read and parse attributes for all files upon
                              filesystem initialization  [default: False]
       -o prefetch_symlinks   extract all symbolic links upon filesystem
                              initialization (implies prefetch_attrs) [default:
                              False]
       -o prefetch_regex=REGEX
                              extract all objects that match REGEX upon
                              filesystem initialization (implies prefetch_attrs)
       -o prefetch_recent     extract contents of most recent non-full job upon
                              filesystem initialization (implies
                              prefetch_symlinks) [default: False]
       -o prefetch_diff=PATH  extract files that do not match files at PATH
                              (hint: speeds up rsync; implies prefetch_symlinks)
       -o prefetch_everything
                              extract everything upon filesystem initialization
                              (complete restore to cache) [default: False]
       -o user_cache_path=PATH
                              user specified cache path (hint: combine this with
                              one of the prefetch options) [default: none]
       -o logging=debug|info|warning|critical|error
                              logging level [default: warning]
       -o syslog              log to both syslog and console [default: False]
   
   FUSE options:
       -d   -o debug          enable debug output (implies -f)
       -f                     foreground operation
       -s                     disable multi-threaded operation
   
       -o allow_other         allow access to other users
       -o allow_root          allow access to root
       -o nonempty            allow mounts over non-empty file/dir
       -o default_permissions enable permission checking by kernel
       -o fsname=NAME         set filesystem name
       -o subtype=NAME        set filesystem type
       -o large_read          issue large read requests (2.4 only)
       -o max_read=N          set maximum size of read requests
   
       -o hard_remove         immediate removal (don't hide files)
       -o use_ino             let filesystem set inode numbers
       -o readdir_ino         try to fill in d_ino in readdir
       -o direct_io           use direct I/O
       -o kernel_cache        cache files in kernel
       -o [no]auto_cache      enable caching based on modification times (off)
       -o umask=M             set file permissions (octal)
       -o uid=N               set file owner
       -o gid=N               set file group
       -o entry_timeout=T     cache timeout for names (1.0s)
       -o negative_timeout=T  cache timeout for deleted names (0.0s)
       -o attr_timeout=T      cache timeout for attributes (1.0s)
       -o ac_attr_timeout=T   auto cache timeout for attributes (attr_timeout)
       -o intr                allow requests to be interrupted
       -o intr_signal=NUM     signal to send on interrupt (10)
       -o modules=M1[:M2...]  names of modules to push onto filesystem stack
   
       -o max_write=N         set maximum size of write requests
       -o max_readahead=N     set maximum readahead
       -o async_read          perform reads asynchronously (default)
       -o sync_read           perform reads synchronously
       -o atomic_o_trunc      enable atomic open+truncate support
       -o big_writes          enable larger than 4kB writes
       -o no_remote_lock      disable remote file locking
   
   Module options:
   
   [subdir]
       -o subdir=DIR	    prepend this directory to all paths (mandatory)
       -o [no]rellinks	    transform absolute symlinks to relative
   
   [iconv]
       -o from_code=CHARSET   original encoding of file names (default: UTF-8)
       -o to_code=CHARSET	    new encoding of the file names (default: UTF-8)
   

OPERATION
---------

INITIALIZATION
~~~~~~~~~~~~~~

**BaculaFS** starts by running several SQL queries against the Bacula
catalog. This is done to determine the list of files that belong to
the most recent backup for a given client and fileset.

**BaculaFS** can also be told to represent a backup snapshot
corresponding to a specified date and time, or a list of backup job
ids.

Following this, **BaculaFS** may run ``bextract`` *once* to prefetch
and cache symbolic links and actual file contents, depending on user
specified command line options.

At this point the filesystem is ready.

CACHE
~~~~~

Opening a file for reading causes **BaculaFS** to run ``bextract`` in
order to extract the file from the storage device. If this operation
succeeds, the file is cached for subsequent read operations.

Bacula storage is not designed for random access file retrieval, so it
is important to select a suitable cache prefetch strategy beforehand.
Running ``bextract`` once, during filesystem initialization, to
extract several files, is much more efficient than running it several
times to extract each individual file, when accessed at a later stage.

For example:

- use ``-o prefetch_attrs`` for storage space usage analysis
  (e.g. with Baobab_)
- use ``-o prefetch_symlinks`` for any manual filesystem traversal
  with command line or GUI tools (``find``, ``mc``, etc.)
- use ``-o prefetch_diff`` with ``rsync``

.. _Baobab: http://www.marzocca.net/linux/baobab/

The cache may be cleaned up automatically upon un-mounting the
filesystem, with ``-o cleanup``. It may also be reused between mount
operations with ``-o user_cache_path``.

EXTENDED ATTRIBUTES
~~~~~~~~~~~~~~~~~~~

**BaculaFS** uses extended file attributes to expose Bacula specific
information for each file in the filesystem. These extended attributes
are all grouped in the ``user.baculafs`` namespace:

::

   user.baculafs.FileIndex
   user.baculafs.JobId
   user.baculafs.LStat
   user.baculafs.MD5

The root directory has several more attributes, that expose filesystem
instance-specific information:

::

   user.baculafs.cache_prefix
   user.baculafs.client
   user.baculafs.datetime
   user.baculafs.fileset
   user.baculafs.joblist

and several more attributes for monitoring the file extraction
process:
 
::

   user.baculafs.bextract.failures
   user.baculafs.bextract.path
   user.baculafs.bextract.pending
   user.baculafs.bextract.retries
   user.baculafs.bextract.state
   user.baculafs.bextract.volume

MISSING VOLUMES
~~~~~~~~~~~~~~~

If the storage device is a tape drive then it's possible that
**BaculaFS** will attempt to retrieve a file from a volume that's on
an unmounted tape. **BaculaFS** will then set
``user.baculafs.bextract.state`` to ``*user intervention required*``,
and will wait for user intervention.

The user should then mount the tape containing the missing volume and
set the state to ``run``, to make **BaculaFS** retry the operation:

::

   attr -s baculafs.bextract.state -V run <mount-point>

Please note that this feature has undergone only rudimentary
testing. Expect breakage.


LIMITATIONS
-----------

LOCKING
~~~~~~~

Access to the storage device by different instances of **BaculaFS** is
serialized by locking the storage daemon configuration file. This
means that you can mount several views of the backup catalog
(e.g. accessing backup snapshots of different clients or snapshots
from the same client but from different dates).

There are at least two issues with this locking mechanism that you
should note:

- the lock is *advisory*, meaning that it does not prevent the Bacula
  storage daemon itself from accessing the storage device while in use
  by **BaculaFS**
- depending on your setup, the lock may not work if the storage daemon
  configuration file is accessed via NFS



WINDOWS FILESETS
~~~~~~~~~~~~~~~~

**BaculaFS** can be used with Windows backup filesets, but it does not
reproduce any Windows specific file attributes. This is because
``bextract`` does not extract Windows specific file attributes on
Linux.

BUGS
----

Please report problems via the **BaculaFS** issue tracking system:
`<http://code.google.com/p/baculafs/issues/list>`_

LICENSE
-------

**BaculaFS** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see
`<http://www.gnu.org/licenses/>`_.



