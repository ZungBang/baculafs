
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

class SQL :
    '''
    Holds all SQL statements used by baculafs.
    Adapted from Bacula source code.
    '''

    MYSQL = 'mysql'
    POSTGRESQL = 'postgresql'
    SQLITE = 'sqlite'
    SQLITE3 = 'sqlite3'
    
    clients = 'SELECT Client.Name,ClientId FROM Client'
    
    filesets = '''
    SELECT DISTINCT FileSet.FileSet FROM Job,
    Client,FileSet WHERE Job.FileSetId=FileSet.FileSetId
    AND Job.ClientId=%s AND Client.ClientId=%s 
    ORDER BY FileSet.FileSet
    '''

    fileset = '''
    SELECT FileSetId,FileSet,MD5,CreateTime FROM FileSet
    WHERE FileSet='%s' ORDER BY CreateTime DESC LIMIT 1
    '''

    create_temp = {
        MYSQL: '''
    CREATE TEMPORARY TABLE temp (
    JobId INTEGER UNSIGNED NOT NULL,
    JobTDate BIGINT UNSIGNED,
    ClientId INTEGER UNSIGNED,
    Level CHAR,
    JobFiles INTEGER UNSIGNED,
    JobBytes BIGINT UNSIGNED,
    StartTime TEXT,
    VolumeName TEXT,
    StartFile INTEGER UNSIGNED,
    VolSessionId INTEGER UNSIGNED,
    VolSessionTime INTEGER UNSIGNED)
    ''',
        
        POSTGRESQL: '''
    CREATE TEMPORARY TABLE temp (
    JobId INTEGER NOT NULL,
    JobTDate BIGINT,
    ClientId INTEGER,
    Level CHAR,
    JobFiles INTEGER,
    JobBytes BIGINT,
    StartTime TEXT,
    VolumeName TEXT,
    StartFile INTEGER,
    VolSessionId INTEGER,
    VolSessionTime INTEGER)
    ''',
        
        SQLITE: '''
    CREATE TEMPORARY TABLE temp (
    JobId INTEGER UNSIGNED NOT NULL,
    JobTDate BIGINT UNSIGNED,
    ClientId INTEGER UNSIGNED,
    Level CHAR,
    JobFiles INTEGER UNSIGNED,
    JobBytes BIGINT UNSIGNED,
    StartTime TEXT,
    VolumeName TEXT,
    StartFile INTEGER UNSIGNED,
    VolSessionId INTEGER UNSIGNED,
    VolSessionTime INTEGER UNSIGNED)
    ''',
        
        SQLITE3: '''
    CREATE TEMPORARY TABLE temp (
    JobId INTEGER UNSIGNED NOT NULL,
    JobTDate BIGINT UNSIGNED,
    ClientId INTEGER UNSIGNED,
    Level CHAR,
    JobFiles INTEGER UNSIGNED,
    JobBytes BIGINT UNSIGNED,
    StartTime TEXT,
    VolumeName TEXT,
    StartFile INTEGER UNSIGNED,
    VolSessionId INTEGER UNSIGNED,
    VolSessionTime INTEGER UNSIGNED)
    ''' }

    create_temp1 = {
        MYSQL: '''
    CREATE TEMPORARY TABLE temp1 (
    JobId INTEGER UNSIGNED NOT NULL,
    JobTDate BIGINT UNSIGNED)
    ''',
        
        POSTGRESQL: '''
    CREATE TEMPORARY TABLE temp1 (
    JobId INTEGER NOT NULL,
    JobTDate BIGINT)
    ''',
        
        SQLITE: '''
    CREATE TEMPORARY TABLE temp1 (
    JobId INTEGER UNSIGNED NOT NULL,
    JobTDate BIGINT UNSIGNED)
    ''',
        
        SQLITE3: '''
    CREATE TEMPORARY TABLE temp1 (
    JobId INTEGER UNSIGNED NOT NULL,
    JobTDate BIGINT UNSIGNED)
    ''' }

    temp  = 'SELECT * FROM temp'

    temp1 = 'SELECT * FROM temp1'

    del_temp = 'DROP TABLE temp'
    
    del_temp1 = 'DROP TABLE temp1'

    full_jobs_temp1 = '''
    INSERT INTO temp1 SELECT Job.JobId,JobTdate 
    FROM Client,Job,JobMedia,Media,FileSet WHERE Client.ClientId=%s
    AND Job.ClientId=%s
    AND Job.StartTime < '%s'
    AND Level='F' AND JobStatus IN ('T','W') AND Type='B' 
    AND JobMedia.JobId=Job.JobId 
    AND Media.Enabled=1 
    AND JobMedia.MediaId=Media.MediaId 
    AND Job.FileSetId=FileSet.FileSetId 
    AND FileSet.FileSet='%s'
    ORDER BY Job.JobTDate DESC LIMIT 1
    '''

    full_jobs_temp = '''
    INSERT INTO temp SELECT Job.JobId,Job.JobTDate,
    Job.ClientId,Job.Level,Job.JobFiles,Job.JobBytes,
    StartTime,VolumeName,JobMedia.StartFile,VolSessionId,VolSessionTime 
    FROM temp1,Job,JobMedia,Media WHERE temp1.JobId=Job.JobId 
    AND Level='F' AND JobStatus IN ('T','W') AND Type='B' 
    AND Media.Enabled=1 
    AND JobMedia.JobId=Job.JobId 
    AND JobMedia.MediaId=Media.MediaId
    '''

    diff_jobs_temp = '''
    INSERT INTO temp SELECT Job.JobId,Job.JobTDate,Job.ClientId,
    Job.Level,Job.JobFiles,Job.JobBytes,
    Job.StartTime,Media.VolumeName,JobMedia.StartFile,
    Job.VolSessionId,Job.VolSessionTime 
    FROM Job,JobMedia,Media,FileSet 
    WHERE Job.JobTDate>%d AND Job.StartTime<'%s'
    AND Job.ClientId=%d 
    AND JobMedia.JobId=Job.JobId 
    AND Media.Enabled=1 
    AND JobMedia.MediaId=Media.MediaId 
    AND Job.Level='D' AND JobStatus IN ('T','W') AND Type='B' 
    AND Job.FileSetId=FileSet.FileSetId 
    AND FileSet.FileSet='%s'
    ORDER BY Job.JobTDate DESC LIMIT 1
    '''

    incr_jobs_temp = '''
    INSERT INTO temp SELECT Job.JobId,Job.JobTDate,Job.ClientId,
    Job.Level,Job.JobFiles,Job.JobBytes,
    Job.StartTime,Media.VolumeName,JobMedia.StartFile,
    Job.VolSessionId,Job.VolSessionTime 
    FROM Job,JobMedia,Media,FileSet 
    WHERE Job.JobTDate>%d AND Job.StartTime<'%s' 
    AND Job.ClientId=%d
    AND Media.Enabled=1 
    AND JobMedia.JobId=Job.JobId 
    AND JobMedia.MediaId=Media.MediaId 
    AND Job.Level='I' AND JobStatus IN ('T','W') AND Type='B' 
    AND Job.FileSetId=FileSet.FileSetId 
    AND FileSet.FileSet='%s'
    '''

    selected_jobs_temp = '''
    INSERT INTO temp SELECT Job.JobId,Job.JobTDate,Job.ClientId,
    Job.Level,Job.JobFiles,Job.JobBytes,
    Job.StartTime,Media.VolumeName,JobMedia.StartFile,
    Job.VolSessionId,Job.VolSessionTime 
    FROM Job,JobMedia,Media,FileSet 
    WHERE Job.JobId IN (%s)
    AND Job.ClientId=%d
    AND Media.Enabled=1 
    AND JobMedia.JobId=Job.JobId 
    AND JobMedia.MediaId=Media.MediaId 
    AND JobStatus IN ('T','W') AND Type='B' 
    AND Job.FileSetId=FileSet.FileSetId 
    AND FileSet.FileSet='%s'
    '''

    jobs = 'SELECT DISTINCT JobId,Level,StartTime FROM temp ORDER BY StartTime ASC'

    base_jobs = '''
    SELECT DISTINCT BaseJobId
    FROM Job JOIN BaseFiles USING (JobId)
    WHERE Job.HasBase = 1
    AND Job.JobId IN (%s)
    '''

    purged_jobs = '''
    SELECT SUM(PurgedFiles) FROM Job WHERE JobId IN (%s)
    '''
    
    files = '''
    SELECT Path.Path, Filename.Name, Temp.FileIndex, Temp.JobId, LStat, MD5 
     FROM ( %s ) AS Temp 
     JOIN Filename ON (Filename.FilenameId = Temp.FilenameId) 
     JOIN Path ON (Path.PathId = Temp.PathId) 
    WHERE FileIndex > 0 
    ORDER BY Temp.JobId, FileIndex ASC
    '''

    with_basejobs = {
        MYSQL: '''
     SELECT FileId, Job.JobId AS JobId, FileIndex, File.PathId AS PathId, 
            File.FilenameId AS FilenameId, LStat, MD5 
     FROM Job, File, ( 
         SELECT MAX(JobTDate) AS JobTDate, PathId, FilenameId 
           FROM ( 
             SELECT JobTDate, PathId, FilenameId 
               FROM File JOIN Job USING (JobId) 
              WHERE File.JobId IN (%s) 
               UNION ALL 
             SELECT JobTDate, PathId, FilenameId 
               FROM BaseFiles 
                    JOIN File USING (FileId) 
                    JOIN Job  ON    (BaseJobId = Job.JobId) 
              WHERE BaseFiles.JobId IN (%s) 
            ) AS tmp GROUP BY PathId, FilenameId 
         ) AS T1 
     WHERE (Job.JobId IN ( 
             SELECT DISTINCT BaseJobId FROM BaseFiles WHERE JobId IN (%s)) 
             OR Job.JobId IN (%s)) 
       AND T1.JobTDate = Job.JobTDate 
       AND Job.JobId = File.JobId 
       AND T1.PathId = File.PathId 
       AND T1.FilenameId = File.FilenameId
     ''',
        
        POSTGRESQL: '''
      SELECT DISTINCT ON (FilenameId, PathId) StartTime, JobId, FileId, 
              FileIndex, PathId, FilenameId, LStat, MD5 
        FROM 
            (SELECT FileId, JobId, PathId, FilenameId, FileIndex, LStat, MD5 
               FROM File WHERE JobId IN (%s) 
              UNION ALL 
             SELECT File.FileId, File.JobId, PathId, FilenameId, 
                    File.FileIndex, LStat, MD5 
               FROM BaseFiles JOIN File USING (FileId) 
              WHERE BaseFiles.JobId IN (%s) 
             ) AS T JOIN Job USING (JobId) 
        ORDER BY FilenameId, PathId, StartTime DESC
        -- dummy comment for chomping extra parameter: %s
        -- dummy comment for chomping extra parameter: %s
     ''',
        
        SQLITE: '''
     SELECT FileId, Job.JobId AS JobId, FileIndex, File.PathId AS PathId, 
            File.FilenameId AS FilenameId, LStat, MD5 
     FROM Job, File, ( 
         SELECT MAX(JobTDate) AS JobTDate, PathId, FilenameId 
           FROM ( 
             SELECT JobTDate, PathId, FilenameId 
               FROM File JOIN Job USING (JobId) 
              WHERE File.JobId IN (%s) 
               UNION ALL 
             SELECT JobTDate, PathId, FilenameId 
               FROM BaseFiles 
                    JOIN File USING (FileId) 
                    JOIN Job  ON    (BaseJobId = Job.JobId) 
              WHERE BaseFiles.JobId IN (%s) 
            ) AS tmp GROUP BY PathId, FilenameId 
         ) AS T1 
     WHERE (Job.JobId IN ( 
            SELECT DISTINCT BaseJobId FROM BaseFiles WHERE JobId IN (%s)) 
            OR Job.JobId IN (%s)) 
       AND T1.JobTDate = Job.JobTDate 
       AND Job.JobId = File.JobId 
       AND T1.PathId = File.PathId 
       AND T1.FilenameId = File.FilenameId
     ''',
        
        SQLITE3: '''
     SELECT FileId, Job.JobId AS JobId, FileIndex, File.PathId AS PathId, 
            File.FilenameId AS FilenameId, LStat, MD5 
     FROM Job, File, ( 
         SELECT MAX(JobTDate) AS JobTDate, PathId, FilenameId 
           FROM ( 
             SELECT JobTDate, PathId, FilenameId 
               FROM File JOIN Job USING (JobId) 
              WHERE File.JobId IN (%s) 
               UNION ALL 
             SELECT JobTDate, PathId, FilenameId 
               FROM BaseFiles 
                    JOIN File USING (FileId) 
                    JOIN Job  ON    (BaseJobId = Job.JobId) 
              WHERE BaseFiles.JobId IN (%s) 
            ) AS tmp GROUP BY PathId, FilenameId 
         ) AS T1 
     WHERE (Job.JobId IN ( 
              SELECT DISTINCT BaseJobId FROM BaseFiles WHERE JobId IN (%s)) 
             OR Job.JobId IN (%s)) 
       AND T1.JobTDate = Job.JobTDate 
       AND Job.JobId = File.JobId 
       AND T1.PathId = File.PathId 
       AND T1.FilenameId = File.FilenameId
    ''' }

    job_records = '''
    SELECT JobId,VolSessionId,VolSessionTime,
    PoolId,StartTime,EndTime,JobFiles,JobBytes,JobTDate,Job,JobStatus,
    Type,Level,ClientId,Name,PriorJobId,RealEndTime,FileSetId,
    SchedTime,RealEndTime,ReadBytes,HasBase 
    FROM Job WHERE JobId IN (%s)
    '''

    volumes = '''
    SELECT JobMedia.JobId,VolumeName,MediaType,FirstIndex,LastIndex,StartFile,
    JobMedia.EndFile,StartBlock,JobMedia.EndBlock,Copy,
    Slot,StorageId,InChanger
     FROM JobMedia,Media WHERE JobMedia.JobId IN (%s)
     AND JobMedia.MediaId=Media.MediaId ORDER BY JobMedia.JobId,VolIndex,JobMediaId
    '''
