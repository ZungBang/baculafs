
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

from datetime import datetime
from SQL import *

class Catalog :
    '''
    This class represents the Bacula catalog, and provides an interface
    for generating a list of files for a given set of user supplied
    query parameters.
    '''

    datetime_format = '%Y-%m-%d %H:%M:%S'
    
    def __init__(self, database) :
        '''
        Catalog initialization: DATABASE is a Database driver
        object.
        '''
        self.db = database

        
    def query(self, client, fileset = None, timespec = None, select_recent_job = False, joblist = None ) :
        '''
        Query bacula database, get list of files that match
        backup prior to given TIMESPEC, for a given CLIENT, FILESET.

        If the date/time is not specified (i.e. it's None) then use
        the current date/time.

        File records include file path, file name, and stat info.

        Security note: query parameters are never taken from user supplied
        input, but rather are verified against the catalog. This allows us to
        use formatted strings for building parametrized queries.
        '''
        # validate client
        self.client = client
        clients = dict(self.db.query(SQL.clients))
        if len(clients) == 1 and not self.client :
            self.client = clients.keys()[0]
        if self.client not in clients :
            raise ValueError, 'client must be one of %s' % clients.keys()
        self.client_id = clients[self.client]
        # validate fileset
        filesets = [f[0] for f in self.db.query(SQL.filesets % (self.client_id, self.client_id))]
        if len(filesets) == 1 and not fileset :
            fileset = filesets[0]
        elif len(filesets) == 0 :
            raise RuntimeError, 'no filesets found for %s' % self.client
        elif fileset not in filesets :
            raise ValueError, 'fileset must be one of %s' % filesets
        self.fileset = self.db.query(SQL.fileset % fileset)[0]
        # validate timespec
        if timespec :
            self.datetime = datetime.strftime(datetime.strptime(timespec, Catalog.datetime_format), Catalog.datetime_format)
        else :
            self.datetime = datetime.strftime(datetime.now(), Catalog.datetime_format)
        # create temporary tables
        self.db.query(SQL.create_temp[self.db.driver], fetch=False)
        self.db.query(SQL.create_temp1[self.db.driver], fetch=False)
        # get list of jobs
        if joblist :
            # select from specific jobs
            self.joblist = ','.join(list(set([str(int(s.strip())) for s in joblist.split()])))
            self.db.query(SQL.selected_jobs_temp % (self.joblist, self.client_id, self.fileset[1]), fetch=False)
        else :
            # select backup before specified datetime
            self.db.query(SQL.full_jobs_temp1 %
                          (self.client_id, self.client_id, self.datetime, self.fileset[1]), fetch=False)
            self.db.query(SQL.full_jobs_temp, fetch=False)
            full_jobs = self.db.query(SQL.temp1)
            if len(full_jobs) == 0 :
                raise RuntimeError, 'no full jobs found'
            self.db.query(SQL.diff_jobs_temp % (full_jobs[0][1], self.datetime, self.client_id, self.fileset[1]), fetch=False)
            diff_jobs = self.db.query(SQL.temp)
            self.db.query(SQL.incr_jobs_temp % (diff_jobs[-1][1], self.datetime, self.client_id, self.fileset[1]), fetch=False)
        jobs = self.db.query(SQL.jobs)
        self.most_recent_jobid = jobs[-1][0] if jobs[-1][1] != 'F' else -1
        # select files from the most recent job only
        if select_recent_job and self.most_recent_jobid > 0 :
            jobs = [jobs[-1]]
        jobs_csl = ','.join([str(job[0]) for job in jobs])
        base_jobs = self.db.query(SQL.base_jobs % jobs_csl)
        all_jobs = jobs + base_jobs
        all_jobs_csl = ','.join([str(job[0]) for job in all_jobs])
        # abort if any job in the list has been purged
        purged = self.db.query(SQL.purged_jobs % all_jobs_csl)
        if purged[0][0] > 0 :
            raise RuntimeError, 'purged jobs in list (%s)' % all_jobs_csl
        # get job records
        self.jobs = self.db.query(SQL.job_records % all_jobs_csl)
        # get relevant volume records
        self.volumes = self.db.query(SQL.volumes % all_jobs_csl)
        # get files
        self.files = self.db.query(SQL.files % (SQL.with_basejobs[self.db.driver] % (jobs_csl, jobs_csl, jobs_csl, jobs_csl)))
        # delete temporary tables
        self.db.query(SQL.del_temp, fetch=False)
        self.db.query(SQL.del_temp1, fetch=False)

        return self.files


