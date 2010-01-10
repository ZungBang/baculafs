
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

"""Expose the Bacula catalog as a FUSE file system.
"""
from FileSystem import __version__, main

__all__ = ["FileSystem", "Database", "Catalog", "Base64", "SQL", "LogFile"] 


