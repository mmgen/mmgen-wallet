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

from distutils.core import setup,Extension
from distutils.command.build_ext import build_ext
import sys,os
from shutil import copy2

# install extension module in repository after building
class my_build_ext(build_ext):
	def build_extension(self,ext):
		build_ext.build_extension(self,ext)
		ext_src = self.get_ext_fullpath(ext.name)
		ext_dest = self.get_ext_filename(ext.name)
		try: os.unlink(ext_dest)
		except: pass
		os.chmod(ext_src,0755)
		print 'copying %s to %s' % (ext_src,ext_dest)
		copy2(ext_src,ext_dest)

module1 = Extension(
	name         = 'mmgen.secp256k1',
	sources      = ['extmod/secp256k1mod.c'],
	libraries    = ['secp256k1'],
	library_dirs = ['/usr/local/lib'],
	runtime_library_dirs = ['/usr/local/lib'],
	include_dirs = ['/usr/local/include'],
	)

setup(
		name         = 'mmgen',
		description  = 'A complete Bitcoin offline/online wallet solution for the command line',
		version      = '0.8.6',
		author       = 'Philemon',
		author_email = 'mmgen-py@yandex.com',
		url          = 'https://github.com/mmgen/mmgen',
		license      = 'GNU GPL v3',
		platforms    = 'Linux, MS Windows, Raspberry PI',
		keywords     = 'Bitcoin, wallet, cold storage, offline storage, open-source, command-line, Python, Bitcoin Core, bitcoind, hd, deterministic, hierarchical, secure, anonymous',
		cmdclass     = { 'build_ext': my_build_ext },
		# disable building of secp256k1 extension module on Windows
		ext_modules = [module1] if sys.platform[:5] == 'linux' else [],
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
