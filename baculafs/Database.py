
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

import os

from Base64 import *
from SQL import *

class Database :
    '''
    This class shields the rest of the code from the pesky details of
    actually accessing one of the supported databases.
    '''
    drivers = [SQL.MYSQL, SQL.POSTGRESQL, SQL.SQLITE, SQL.SQLITE3]

    default_database = {
        SQL.MYSQL: 'bacula',
        SQL.POSTGRESQL: 'bacula',
        SQL.SQLITE: '/var/lib/bacula/bacula.db',
        SQL.SQLITE3: '/var/lib/bacula/bacula.db'
        }
    
    def __init__(self, driver, host, port, database, username, password, logger) :
        '''
        Initialize database driver: connect the database,
        create connection and cusror objects.
        '''
        self.logger = logger
        self.connection = None
        self.cursor = None
        self.driver = driver
        if not database :
            database = Database.default_database[self.driver]
        if self.driver == SQL.MYSQL :
            from MySQLdb import connect
            self.connection = connect(host=host, port=port, user=username, passwd=password, db=database)
        elif self.driver == SQL.POSTGRESQL :
            from psycopg2 import connect
            self.connection = connect(host=host, port=port, user=username, password=password, database=database)
        elif self.driver == SQL.SQLITE :
            from sqlite import connect
            database = os.path.expanduser(database)
            if not os.path.isfile(database) or not os.access(database, os.R_OK) :
                raise RuntimeError, 'cannot read from file %s' % database
            self.connection = connect(database)
        elif self.driver == SQL.SQLITE3 :
            from sqlite3 import connect
            database = os.path.expanduser(database)
            if not os.path.isfile(database) or not os.access(database, os.R_OK) :
                raise RuntimeError, 'cannot read from file %s' % database
            self.connection = connect(database)
            self.connection.text_factory = str # fixes sqlite3.OperationalError: Could not decode to UTF-8
        else :
            raise ValueError, 'unknown database driver %s.' % self.driver
        self.cursor = self.connection.cursor()

    def close(self) :
        '''
        Close database connection
        '''
        if self.cursor :
            self.cursor.close()
            self.cursor = None
        if self.connection :
            self.connection.close()
            self.connection = None

    def query(self, sql, fetch = True) :
        '''
        Execute SQL and fetch all results
        '''
        self.logger.debug(sql)
        self.cursor.execute(sql)
        if fetch :
            return self.cursor.fetchall()
    
