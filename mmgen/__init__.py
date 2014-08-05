#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
#
# This program is free software: you can redistribute it and/or modify
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

"""
MMGen = Multi-Mode GENerator, a Bitcoin cold storage/tracking solution for
        the command line
"""
__all__ = [
	'rpc',
	'addr.py',
	'bitcoin.py',
	'config.py',
	'license.py',
	'mn_electrum.py',
	'mnemonic.py',
	'mn_tirosh.py',
	'Opts.py',
	'tx.py',
	'util.py',
	'walletgen.py'
]

__version__ = '.6.0'     # See also below and setup.py

# New software should look at this instead of at __version__ above.
version_info = (0, 6, 0)    # See also above and setup.py
