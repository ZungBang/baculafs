
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

import logging
import logging.handlers

LOGGING_LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL}

class LogFile :
    '''
    file like object that wraps a logger object
    '''
    def __init__(self, logger, level) :
        self.logger = logger
        self.level = level
        self.tail = ''

    def write(self, message) :
        lines = (self.tail + message).splitlines()
        for line in lines[:-1] :
            self.logger.log(self.level, line)
        if message.endswith('\n') :
            self.logger.log(self.level, lines[-1])
            self.tail = ''
        elif len(lines) > 0 :
            self.tail = lines[-1]
        else :
            self.tail = ''
                                

    def flush(self, flush_tail = False) :
        if flush_tail and self.tail :
            self.logger.log(self.level, self.tail)
            self.tail = ''
        for handler in self.logger.handlers :
            handler.flush()
        

