#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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

from distutils.core import setup

setup(
		name         = 'mmgen',
		description  = 'A complete Bitcoin cold-storage solution for the command line',
		version      = '0.8.4',
		author       = 'Philemon',
		author_email = 'mmgen-py@yandex.com',
		url          = 'https://github.com/mmgen/mmgen',
		license      = 'GNU GPL v3',
		platforms    = 'Linux, MS Windows',
		keywords     = 'Bitcoin, wallet, cold storage, offline storage, open-source, command-line, Python, Bitcoin Core, bitcoind, hd, deterministic, hierarchical, secure, anonymous',
		py_modules = [
			'mmgen.__init__',
			'mmgen.addr',
			'mmgen.bitcoin',
			'mmgen.globalvars',
			'mmgen.common',
			'mmgen.crypto',
			'mmgen.filename',
			'mmgen.license',
			'mmgen.mn_electrum',
			'mmgen.mn_tirosh',
			'mmgen.obj',
			'mmgen.opts',
			'mmgen.rpc',
			'mmgen.seed',
			'mmgen.term',
			'mmgen.test',
			'mmgen.tool',
			'mmgen.tx',
			'mmgen.tw',
			'mmgen.util',

			'mmgen.main',
			'mmgen.main_addrgen',
			'mmgen.main_addrimport',
			'mmgen.main_tool',
			'mmgen.main_txcreate',
			'mmgen.main_txsend',
			'mmgen.main_txsign',
			'mmgen.main_wallet',

			'mmgen.share.__init__',
			'mmgen.share.Opts',
		],
		scripts=[
			'mmgen-addrgen',
			'mmgen-keygen',
			'mmgen-addrimport',
			'mmgen-passchg',
			'mmgen-walletchk',
			'mmgen-walletconv',
			'mmgen-walletgen',
			'mmgen-txcreate',
			'mmgen-txsign',
			'mmgen-txsend',
			'mmgen-tool',
		]
	)
