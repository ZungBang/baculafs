__version__ = '0.1.1'

import os
import stat
import errno
import copy
import tempfile
import shutil
import threading
import traceback
import pexpect
import fcntl

from LogFile import *
from Database import *
from Catalog import *

# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass

import fuse
from fuse import Fuse

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

fuse.feature_assert('stateful_files', 'has_init')

def flag2mode(flags):
    '''
    taken from python-fuse xmp.py example
    '''
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]
    
    if flags | os.O_APPEND:
        m = m.replace('w', 'a', 1)
        
    return m

def makedirs(path):
    '''
    create path like mkdir -p
    taken from: http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python/600612#600612
    '''
    try:
        os.makedirs(path)
    except OSError, exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise
                            
def touch(fname, times = None):
    '''
    touch file
    adapted from: http://stackoverflow.com/questions/1158076/implement-touch-using-python/1160227#1160227
    '''
    fhandle = open(fname, 'a')
    try:
        os.utime(fname, times)
    finally:
        fhandle.close()
        

class FileSystem(Fuse) :

    null_stat = fuse.Stat(st_mode = stat.S_IFDIR | 0755, st_nlink = 2, st_ino = -1)

    bacula_stat_fields = ['st_dev',
                          'st_ino',
                          'st_mode',
                          'st_nlink',
                          'st_uid',
                          'st_gid',
                          'st_rdev',
                          'st_size',
                          'st_blksize',
                          'st_blocks',
                          'st_atime',
                          'st_mtime',
                          'st_ctime',
                          'st_linkfi',
                          'st_flags',
                          'st_streamid']

    fuse_stat_fields = dir(fuse.Stat())

    xattr_prefix = 'user.baculafs.'
    xattr_fields = ['FileIndex', 'JobId', 'LStat', 'MD5']
    xattr_fields_root = ['client', 'fileset', 'datetime', 'joblist', 'cache_prefix']
    xattr_fields_bextract = ['path', 'volume', 'retries', 'state', 'pending', 'failures']
    
    bextract_done = {'path': None,
                     'volume': None,
                     'retries': 0,
                     'state': 'idle'}
    
    def __init__(self, *args, **kw):
        '''
        Initialize filesystem
        '''
        
        self._extract_lock = threading.Lock()
        self._getattr_lock = threading.Lock()
        self._bextract_status_lock = threading.Lock()
        self._bextract_user_intervention_event = threading.Event()

        self._initialized = False
        
        # default option values
        self.logging = 'warning'
        self.syslog = False
        self.driver = 'sqlite3'
        self.database = None
        self.host = 'localhost'
        self.port = 0
        self.username = 'bacula'
        self.password = ''
        self.conf = '/etc/bacula/bacula-sd.conf'
        self.client = ''
        self.fileset = None
        self.device = 'FileStorage'
        self.datetime = None
        self.recent_job = False
        self.joblist = None
        self.user_cache_path = None
        self.cleanup = False
        self.move_root = False
        self.prefetch_attrs = False
        self.prefetch_regex = None
        self.prefetch_symlinks = False
        self.prefetch_recent = False
        self.prefetch_diff = None
        self.prefetch_everything = False
        self.dirs = { '/': { '': (FileSystem.null_stat,) } }

        self._bextract_status = copy.deepcopy(FileSystem.bextract_done)
        self._bextract_status['pending'] = 0
        self._bextract_status['failures'] = 0

        class File (FileSystem._File):
            def __init__(self2, *a, **kw):
                FileSystem._File.__init__(self2, self, *a, **kw)
                
        self.file_class = File

        Fuse.__init__(self, *args, **kw)

    def _split(self, path) :
        '''
        os.path.split wrapper
        '''
        head, tail = os.path.split(path)
        if head and not head.endswith('/') :
            head += '/'
        return head, tail

    def _bacula_stat(self, base64) :
        '''
        Parse base64 encoded lstat info.
        Returns fuse.Stat object with subset of decoded values,
        and dictionary with full list of decoded values
        '''
        st = fuse.Stat()
        lst = dict(zip(FileSystem.bacula_stat_fields, map(self.base64.decode, base64.split())))
        for k in FileSystem.bacula_stat_fields :
            if k in FileSystem.fuse_stat_fields :
                setattr(st, k, lst[k])
        return lst, st

    def _add_parent_dirs(self, path) :
        '''
        add parent directories of path to dirs dictionary
        '''
        head, tail = self._split(path[:-1])
        if not head or head == path:
            return
        if not head in self.dirs :
            self.dirs[head] = { tail: (FileSystem.null_stat,) }
        elif not tail in self.dirs[head] :
            self.dirs[head][tail] = (FileSystem.null_stat,)
        self._add_parent_dirs(head)

    
    def _extract(self, path_list) :
        '''
        extract path list from storage, returns path list of extracted files
        '''

        nitems = len(path_list)
        self._bextract_increment_counter('pending', nitems)
        
        # serialize extractions
        self._extract_lock.acquire()
        
        items = []
        realpath_list = []
        hardlink_targets = []
        
        for path in path_list :
            realpath, symlinkinfo, volumes = self._find_volumes(path)
            realpath_list.append(realpath)
            if volumes :
                items.append((symlinkinfo, path, volumes))
                # collect hard link targets
                hardlink_target = self._hardlink_target(path)
                if (hardlink_target and
                    hardlink_target not in path_list and
                    hardlink_target not in hardlink_targets) :
                    hardlink_targets.append(hardlink_target)

        # add hardlink targets to list
        # bextract will fail to extract the hardlink if its target does not exist
        for path in hardlink_targets :
            realpath, symlinkinfo, volumes = self._find_volumes(path)
            if volumes :
                items.append((symlinkinfo, path, volumes))

        if len(items) > 0 :
            rc, sig = self._bextract(items)
            # it seems that bextract does not restore mtime for symlinks
            # so we create a normal file with same mtime as stored symlink
            # (note that we only use that file if the cache path was
            # supplied by the user)
            if rc == 0 :
                for item in items :
                    if item[0] :
                        symlinkfile = item[0][0]
                        symlinktime = item[0][1:]
                        makedirs(os.path.dirname(symlinkfile))
                        touch(symlinkfile, symlinktime)

        self._extract_lock.release()
        self._bextract_increment_counter('pending', -nitems)
        
        return realpath_list
    
    def _hardlink_target(self, path) :
        '''
        return hard link target of path if it is a hard link
        '''
        head, tail = self._split(path)
        bs = self.dirs[head][tail][-2]
        jobid = self.dirs[head][tail][1]
        if bs['st_nlink'] > 1 and bs['st_linkfi'] > 0 :
            st_linkfi = bs['st_linkfi']
            for file in self.catalog.files :
                if jobid == file[3] and st_linkfi == file[2] :
                    hardlink_target = ('/' if not file[0].startswith('/') else '')+file[0]+file[1]
                    return hardlink_target
        return None        
    
    def _find_volumes(self, path) :
        '''
        return list of volumes that contain path to be extracted, 
        if the path has not been extracted yet
        '''
        realpath = os.path.normpath(self.cache_path + path)
        symlinkpath = os.path.normpath(self.cache_symlinks + path)
        head, tail = self._split(path)
        # sanity check: path should not be a directory
        if tail == '':
            raise RuntimeError, 'trying to extract a directory %s' % path
        # check that path exists in catalog
        if head not in self.dirs or tail not in self.dirs[head] :
            return None, None, None
        # sanity check: path entry is incomplete
        if len(self.dirs[head][tail]) == 1 :
            raise RuntimeError, 'incomplete entry for path %s' % path
        # return if file has already been extracted
        bs = self.getattr(path)
        is_symlink = stat.S_ISLNK(bs.st_mode)
        found = False
        if os.path.exists(realpath) or os.path.lexists(realpath) :
            # make sure that stat info of realpath matches path
            s = os.lstat(realpath)
            conds = [getattr(s, attr) == getattr(bs, attr)
                     for attr in ['st_mode', 'st_uid', 'st_gid', 'st_size', 'st_mtime']]
            if is_symlink :
                conds[-1] = (os.path.exists(symlinkpath) and
                             bs.st_mtime == os.stat(symlinkpath).st_mtime)
            if all(conds) :
                return realpath, None, None
        # generate list of volumes for path
        fileindex, jobid = self.dirs[head][tail][0:2]
        jobs = [job for job in self.catalog.jobs
                if job[0] == jobid]
        volumes = [[volume[1],   # 0-Volume
                    volume[2],   # 1-MediaType
                    self.device, # 2-Device
                    jobs[0][1],  # 3-VolSessionId
                    jobs[0][2],  # 4-VolSessionTime
                    (volume[5] << 32) | volume[7], # 5-VolAddr: StartAddr
                    (volume[6] << 32) | volume[8], # 6-VolAddr: EndAddr
                    fileindex]   # 7-FileIndex
                   for volume in self.catalog.volumes
                   if (volume[0] == jobid and 
                       volume[3] <= fileindex and
                       fileindex <= volume[4])]
        
        return realpath, (symlinkpath, bs.st_atime, bs.st_mtime) if is_symlink else None, volumes

    def _bextract_set_status(self, status) :
        '''
        thread safe modification of bextract status dict
        '''
        self._bextract_status_lock.acquire()
        for key in status :
            self._bextract_status[key] = status[key]
        self._bextract_status_lock.release()

    def _bextract_increment_counter(self, counter, n) :
        '''
        thread safe modification of bextract counters
        '''
        self._bextract_status_lock.acquire()
        self._bextract_status[counter] += n
        self._bextract_status_lock.release()

    def _bextract_get_status(self) :
        '''
        thread safe access to bextract status dict
        '''
        self._bextract_status_lock.acquire()
        status = copy.deepcopy(self._bextract_status)
        self._bextract_status_lock.release()
        return status

    def _bextract_flock(self) :
        '''
        lock the storage daemon configuration file
        '''
        # we allow locking to fail, so as to allow
        # at least a single instance of baculafs,
        # even if we can't lock the sd conf file
        try :
            f = open(self.conf, 'r')
            fcntl.flock(f, fcntl.LOCK_EX)
            return f
        except :
            self.logger.warning(traceback.format_exc())
            return None
        
    def _bextract_funlock(self, f) :
        '''
        unlock the file f
        '''
        if not f :
            return
        try :
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()
        except :
            self.logger.warning(traceback.format_exc())

    def _bextract(self, items) :
        '''
        extract list of items from Bacula storage device
        '''
        bsrpath = self._write_bsr(items)
        cmd = 'bextract -b "%s" -c "%s" "%s" "%s"' % (bsrpath, self.conf, self.device, self.cache_path)
        self.logger.debug(cmd)
            
        self._bextract_set_status({'path': items[0][1],
                                   'volume': items[0][-1][0][0],
                                   'retries': 0,
                                   'state': 'run'})

        # we serialize calls to bextract across instances of baculafs
        # by locking the storage daemon configuration file
        # (note that this may not work over NFS)
        f = self._bextract_flock()
        
        child = pexpect.spawn(cmd)
        child.logfile = self.logfile #sys.stdout

        attempt = 0
        missing = ''
        while True :
            # bextract either finishes or waits for a missing volume
            i = child.expect([self.fail_pattern, pexpect.EOF],
                             timeout=None,
                             searchwindowsize=200)
            if i == 0 :
                # count retries
                if missing == child.match.groups()[0] :
                    attempt += 1
                    self._bextract_set_status({'retries': attempt,
                                               'state': '*user intervention required*'})
                else :
                    attempt = 1
                    missing = child.match.groups()[0]
                    self._bextract_set_status({'volume': missing,
                                               'retries': attempt,
                                               'state': '*user intervention required*'})
                # wait for user
                if not self._initialized :
                    if self.loglevel != logging.DEBUG :
                        sys.stdout.write('Mount Volume "%s" on device "%s" %s and press return when ready: ' % 
                                         (missing, self.device, child.match.groups()[1]))
                        sys.stdout.flush()
                    sys.stdin.read(1)
                else :
                    self.logger.error('Mount volume "%s" on device "%s" %s and run "attr -s baculafs.bextract.state -V run %s" when ready' %
                                      (missing, self.device, child.match.groups()[1], self.fuse_args.mountpoint))
                    self._bextract_user_intervention_event.clear()
                    self._bextract_user_intervention_event.wait()
                    self._bextract_user_intervention_event.clear()                    
                # retry
                self._bextract_set_status({'state': 'run'})
                child.sendline('')
            else :
                child.close()
                break

        # unlock the sd configuration file
        self._bextract_funlock(f)
        
        self._bextract_set_status(FileSystem.bextract_done)
        if child.exitstatus or child.signalstatus :
            self.logger.error('extraction failed (bsr file: %s)' % bsrpath)
            self._bextract_increment_counter('failures', 1)
        return (child.exitstatus, child.signalstatus)

    def _write_bsr(self, items) :
        '''
        generate bsr for items to be extracted
        '''
        bsrfd, bsrpath = tempfile.mkstemp(suffix='.bsr', dir=self.cache_bsrpath, text=True)
        for item in items :
            for volume in item[-1] :
                os.write(bsrfd, 'Volume="%s"\n' % volume[0])
                os.write(bsrfd, 'MediaType="%s"\n' % volume[1])
                os.write(bsrfd, 'Device="%s"\n' % volume[2]) 
                os.write(bsrfd, 'VolSessionId=%d\n' % volume[3])
                os.write(bsrfd, 'VolSessionTime=%d\n' % volume[4])
                os.write(bsrfd, 'VolAddr=%d-%d\n' % (volume[5],volume[6]))
                os.write(bsrfd, 'FileIndex=%d\n' % volume[7])
                os.write(bsrfd, 'Count=1\n')
        os.close(bsrfd)
        return bsrpath

    def _match_stat(self, path, bs) :
        '''
        determine if stat of path matches bs
        '''
        found = False
        if os.path.exists(path) or os.path.lexists(path) :
            s = os.lstat(path)
            found = all([getattr(s, attr) == getattr(bs, attr)
                         for attr in ['st_mode', 'st_uid', 'st_gid', 'st_size', 'st_mtime']])
        return found

    def _setup_logging(self) :
        '''
        initialize logging facility
        '''
        # log messages are sent to both console and syslog
        # use -o logging=level to set the log level
        # use -o syslog to enable logging to syslog
        self.logger = logging.getLogger('BaculaFS')
        self.loglevel = LOGGING_LEVELS.get(self.logging, logging.NOTSET)
        self.logger.setLevel(self.loglevel)
        h = logging.StreamHandler()
        h.setLevel(self.loglevel)
        formatter = logging.Formatter("%(message)s")
        h.setFormatter(formatter)
        self.logger.addHandler(h)
        if self.syslog :
            try :
                h = logging.handlers.SysLogHandler('/dev/log')
                h.setLevel(self.loglevel)
                formatter = logging.Formatter("%(name)s: %(levelname)-8s - %(message)s")
                h.setFormatter(formatter)
                self.logger.addHandler(h)
            except :
                self.logger.warning(traceback.format_exc())
        self.logfile = LogFile(self.logger, logging.DEBUG)

    
    def initialize(self):
        '''
        initialize database, catalog
        '''

        self._setup_logging()

        self.logger.info('Populating file system ... ')

        # setup cache
        if self.user_cache_path :
            self.cache_prefix = self.user_cache_path
        else :
            self.cache_prefix = tempfile.mkdtemp(prefix='baculafs-')
        self.cache_path = os.path.normpath(self.cache_prefix + '/files')
        makedirs(self.cache_path)
        self.cache_bsrpath = os.path.normpath(self.cache_prefix + '/bsr')
        makedirs(self.cache_bsrpath)
        self.cache_symlinks = os.path.normpath(self.cache_prefix + '/symlinks')
        makedirs(self.cache_symlinks)

        # test access to sd conf file
        open(self.conf, 'r').close()
        # init bextract failure pattren
        self.fail_pattern = 'Mount Volume "([^"]+)" on device "%s" (.*) and press return when ready:' % self.device
        # init database and catalog
        self.db = Database(self.driver,
                           self.host,
                           self.port,
                           self.database,
                           self.username,
                           self.password,
                           self.logger)
        self.catalog = Catalog(self.db)
        self.base64 = Base64()
        files = self.catalog.query(self.client, self.fileset, self.datetime, self.recent_job, self.joblist)
        # validated values
        self.client = self.catalog.client
        self.fileset = self.catalog.fileset[1]
        self.datetime = self.catalog.datetime
        # we don't need the database anymore
        self.db.close()

        prefetches = []

        # validate prefetch conditions
        if self.prefetch_everything :
            self.prefetch_recent = False
            self.prefetch_regex = None
            self.prefetch_diff = None
            self.prefetch_symlinks = True
        if self.prefetch_regex :
            try :
                regex = re.compile(self.prefetch_regex)
                self.prefetch_attrs = True
            except :
                # bad regex: show traceback and ignore
                self.logger.warning(traceback.format_exc())
                self.prefetch_regex = None
        if self.prefetch_diff :
            self.prefetch_diff = os.path.normpath(os.path.expanduser(self.prefetch_diff))
            try :
                if os.path.isdir(self.prefetch_diff) :
                    self.prefetch_symlinks = True
                else :
                    self.prefetch_diff = None
            except :
                # can't access target directory: show traceback and ignore
                self.logger.warning(traceback.format_exc())
                self.prefetch_diff = None
        if self.prefetch_recent :
            self.prefetch_symlinks = True
        if self.prefetch_symlinks :
            self.prefetch_attrs = True

        for file in files :
            head = file[0]
            tail = file[1]
            # handle windows directories
            if not head.startswith('/') :
                head = '/'+head
            # make file entry
            if self.prefetch_attrs :
                entry = file[2:] + self._bacula_stat(file[-2])
                # detemine if we need to prefetch this entry
                filepath = head + tail
                if (not stat.S_ISDIR(entry[-1].st_mode) and
                    (self.prefetch_everything or
                     (self.prefetch_recent and
                      file[3] == self.catalog.most_recent_jobid) or 
                     (self.prefetch_regex and
                      regex.match(filepath)) or
                     (self.prefetch_diff and
                      not self._match_stat(self.prefetch_diff + filepath, entry[-1])) or 
                     (self.prefetch_symlinks and
                      stat.S_ISLNK(entry[-1].st_mode)))) :
                    prefetches.append(filepath)
            else :
                entry = file[2:] + (None,) # stat info placeholder
            # new directory
            if head not in self.dirs :
                self.dirs[head] = {}
            # add parent directories
            self._add_parent_dirs(head)
            # directories are added to their parents
            if head != '/' and tail == '' :
                head, tail = self._split(head[:-1])
            # and finally
            self.dirs[head][tail] = entry

        npf = len(prefetches)
        if npf > 0 :
            self.logger.info('Prefetching %d objects ... ' % npf)
            self._extract(prefetches)
        self.logger.info('Cache directory is: %s' % self.cache_prefix)
        self.joblist = ' '.join([str(job[0]) for job in self.catalog.jobs])
        self.logger.info('Jobs in file system: %s' % self.joblist)
        self.logger.info('BaculaFS ready (%d files).' % len(files))
        
        self._initialized = True

    def shutdown(self) :
        '''
        remove cache directory if required
        '''
        if self.cleanup and not self.user_cache_path :
            self.logger.info('removing cache directory: %s' % self.cache_prefix)
            shutil.rmtree(self.cache_prefix, ignore_errors = True)
        
    def setxattr(self, path, name, value, flags):
        '''
        set value of extended attribute
        we allow only setting user.baculafs.bextract.state on the root directory
        '''
        if (path == '/' and
            name == FileSystem.xattr_prefix + 'bextract.state' and
            value == 'run') :
            self._bextract_user_intervention_event.set()
        else :
            return -errno.EOPNOTSUPP

    def getxattr(self, path, name, size):
        '''
        get value of extended attribute
        baculafs exposes some filesystem attributes for the root directory
        (e.g. joblist, cache_prefix - see FileSystem.xattr_fields_root)
        and several other attributes for each file/directory that appears
        in the catalog (e.g. MD5, JobId - see FileSystem.xattr_fields)
        '''
        head, tail = self._split(path)
        val = None
        n = name.replace(FileSystem.xattr_prefix, '')
        if path == '/' :
            if n in FileSystem.xattr_fields_root :
                val = str(getattr(self, n))
            elif n.startswith('bextract.') :
                n = n.replace('bextract.', '')
                if n in FileSystem.xattr_fields_bextract :
                    val = str(self._bextract_get_status()[n])
        if (not val and head in self.dirs and tail in self.dirs[head] and
            len(self.dirs[head][tail]) != 1 and
            n in FileSystem.xattr_fields) :
            val = str(self.dirs[head][tail][FileSystem.xattr_fields.index(n)])
        # attribute not found
        if val == None :
            return -errno.ENODATA
        # We are asked for size of the value.
        if size == 0:
            return len(val)
        return val

    def listxattr(self, path, size):
        '''
        list extended attributes
        '''
        head, tail = self._split(path)
        xattrs = []
        if path == '/' :
            xattrs += [FileSystem.xattr_prefix + a for a in FileSystem.xattr_fields_root]
            xattrs += [FileSystem.xattr_prefix + 'bextract.' + a for a in FileSystem.xattr_fields_bextract]
        if (head in self.dirs and tail in self.dirs[head] and 
            len(self.dirs[head][tail]) != 1) :
            xattrs += [FileSystem.xattr_prefix + a for a in FileSystem.xattr_fields]
        # We are asked for size of the attr list, ie. joint size of attrs
        # plus null separators.
        if size == 0:
            return len("".join(xattrs)) + len(xattrs)
        return xattrs

    def getattr(self, path):
        '''
        Retrieve file attributes.
        Notes:
        1) Bacula does not store attributes for parent directories
           that are not being explicitly backed up, so we provide
           a default set of attributes FileSystem.null_stat
        2) file attributes are base64-encoded and stored by Bacula
           in the catalog. These attributes are decoded when first
           needed and then cached for subsequent requests.
        3) python fuse expects atime/ctime/mtime to be positive
        '''
        head, tail = self._split(path)
        if head in self.dirs and tail in self.dirs[head] :
            self._getattr_lock.acquire()
            attrs = self.dirs[head][tail][-1]
            # decode and cache stat info
            if not attrs :
                self.dirs[head][tail] = self.dirs[head][tail][:-1] + self._bacula_stat(self.dirs[head][tail][-3])
                attrs = self.dirs[head][tail][-1]
            # zero negative timestamps
            for a in ['st_atime','st_mtime','st_ctime'] :
                t = getattr(attrs, a) 
                if t < 0 :
                    self.logger.warning('%s has negative timestamp %s=%d, will use 0' % (path, a, t))
                    setattr(attrs, a, 0)
            self._getattr_lock.release()
            return attrs
        else:
            return -errno.ENOENT
    
    def readdir(self, path, offset):
        '''
        read directory entries
        '''
        path = path if path.endswith('/') else path+'/'
        for key in ['.','..'] :
            yield fuse.Direntry(key)
        for key in self.dirs[path].keys() :
            if len(key) > 0:
                bs = self.getattr(path + key)
                ino = bs.st_ino if bs.st_ino != 0 else -1
                yield fuse.Direntry(key, ino=ino)
            
    def readlink(self, path):
        '''
        read link contents
        '''
        realpath = self._extract([path])[0]
        if realpath :
            link = os.readlink(realpath)
            if self.move_root and link.startswith('/') :
                link = os.path.normpath(self.fuse_args.mountpoint + link)
            return link
        return -errno.ENOENT
    

    class _File(object) :
        def __init__(self, fs, path, flags, *mode) :
            self.fs = fs
            accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
            if (flags & accmode) != os.O_RDONLY:
                raise IOError(errno.EACCES, '')
            self.path = path
            self.realpath = fs._extract([path])[0]
            self.file = os.fdopen(os.open(self.realpath, flags, *mode), flag2mode(flags))
            self.fd = self.file.fileno()
            self.direct_io = False
            self.keep_cache = True

        def read(self, length, offset):
            self.file.seek(offset)
            return self.file.read(length)

        def release(self, flags):
            self.file.close()
                                                                                                
def _bextract_version() :
    '''
    return version string of bextract,
    return None if not runnable or version cannot be parsed
    '''
    version = None
    try :
        child = pexpect.spawn('bextract -?')
        i = child.expect(['Version: ([^(]*) \(([^)]*)\)', pexpect.EOF])
        if i == 0 :
            version = '%s (%s)' % child.match.groups()
        child.close()
    except :
        pass
    return version

def main():
    
    usage = """
BaculaFS: exposes the Bacula catalog and storage as a Filesystem in USErspace

""" + Fuse.fusage

    bacula_version = _bextract_version() 

    server = FileSystem(version="BaculaFS version: %s\nbextract version: %s\nPython FUSE version: %s" %
                        (__version__, bacula_version, fuse.__version__), usage=usage)

    server.multithreaded = True

    server.parser.add_option(mountopt="driver", choices=Database.drivers, metavar='|'.join(Database.drivers), default=server.driver,
                             help="database driver [default: %default]")
    server.parser.add_option(mountopt="host", metavar="HOST", default=server.host,
                             help="database server address [default: %default]")
    server.parser.add_option(mountopt="port", metavar="PORT", default=server.port, type="int",
                             help="database server port")
    server.parser.add_option(mountopt="database", metavar="PATH", default=server.database,
                             help="database name [default: bacula]")
    server.parser.add_option(mountopt="username", metavar="USERNAME", default=server.username,
                             help="database user name [default: %default]")
    server.parser.add_option(mountopt="password", metavar="PASSWORD", default=server.password,
                             help="database password")
    server.parser.add_option(mountopt="conf", metavar="PATH", default=server.conf,
                             help="storage daemon configuration file [default: %default]")
    server.parser.add_option(mountopt="client", metavar="CLIENT", default=server.client,
                             help="file daemon name")
    server.parser.add_option(mountopt="fileset", metavar="FILESET", default=server.fileset,
                             help="backup fileset")
    server.parser.add_option(mountopt="device", metavar="DEVICE", default=server.device,
                             help="storage device name [default: %default]")
    server.parser.add_option(mountopt="datetime", metavar="'YYYY-MM-DD hh:mm:ss'", default=server.datetime,
                             help="snapshot date/time [default: now]")
    server.parser.add_option(mountopt="recent_job", action="store_true", default=server.recent_job,
                             help="select contents of most recent job only [default: %default]") 
    server.parser.add_option(mountopt="joblist", metavar="'JOBID1 JOBID2 ...'", default=server.joblist,
                             help="select contents of specified list of jobs") 
    server.parser.add_option(mountopt="cleanup", action="store_true", default=server.cleanup,
                             help="clean cache directory upon umount  [default: %default]")
    server.parser.add_option(mountopt="move_root", action="store_true", default=server.move_root,
                             help="make absolute path symlinks point to path under mount point  [default: %default]")
    server.parser.add_option(mountopt="prefetch_attrs", action="store_true", default=server.prefetch_symlinks,
                             help="read and parse attributes for all files upon filesystem initialization  [default: %default]")
    server.parser.add_option(mountopt="prefetch_symlinks", action="store_true", default=server.prefetch_symlinks,
                             help="extract all symbolic links upon filesystem initialization (implies prefetch_attrs) [default: %default]")
    server.parser.add_option(mountopt="prefetch_regex", metavar="REGEX", default=server.prefetch_regex,
                             help="extract all objects that match REGEX upon filesystem initialization (implies prefetch_attrs)")
    server.parser.add_option(mountopt="prefetch_recent", action="store_true", default=server.prefetch_recent,
                             help="extract contents of most recent non-full job upon filesystem initialization (implies prefetch_symlinks) [default: %default]")
    server.parser.add_option(mountopt="prefetch_diff", metavar="PATH", default=server.prefetch_diff,
                             help="extract files that do not match files at PATH (hint: speeds up rsync; implies prefetch_symlinks)")
    server.parser.add_option(mountopt="prefetch_everything", action="store_true", default=server.prefetch_everything,
                             help="extract everything upon filesystem initialization (complete restore to cache) [default: %default]")
    server.parser.add_option(mountopt="user_cache_path", metavar="PATH", default=server.user_cache_path,
                             help="user specified cache path (hint: combine this with one of the prefetch options) [default: %default]")
    server.parser.add_option(mountopt="logging", choices=LOGGING_LEVELS.keys(), metavar='|'.join(LOGGING_LEVELS.keys()), default=server.logging,
                             help="logging level [default: %default]")
    server.parser.add_option(mountopt="syslog", action="store_true", default=server.syslog,
                             help="log to both syslog and console [default: %default]")

    server.parse(values=server, errex=1)

    if server.fuse_args.mount_expected() :
        if not bacula_version :
            raise RuntimeError, 'cannot determine Bacula bextract version - is it installed?'
        else :
            # we initialize before main (i.e. not in fsinit) so that
            # any failure here aborts the mount
            try :
                server.initialize()
            except :
                traceback.print_exc()
                server.shutdown()
                raise

    server.main()

    # we shutdown after main, i.e. not in fsshutdown, because
    # calling fsshutdown with multithreaded==True seems to cause
    # the python fuse process to hang waiting for the python gil
    if server.fuse_args.mount_expected() :
        server.shutdown()

