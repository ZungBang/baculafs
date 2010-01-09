
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

class Base64 :
    '''
    Bacula specific implementation of a base64 decoder
    '''
    digits = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '/'
        ]

    def __init__(self) :
        '''
        Initialize the Base 64 conversion routines
        '''
        self.base64_map = dict(zip(Base64.digits,xrange(0,64)))
    
    def decode(self, base64) :
        '''
        Convert the Base 64 characters in base64 to a value.
        '''
        value = 0
        first = 0
        neg = False

        if base64[0] == '-' :
            neg = True
            first = 1
            
        for i in xrange(first, len(base64)) :
            value = value << 6
            value += self.base64_map[base64[i]]

        return -value if neg else value
