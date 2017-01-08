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
from distutils.command.install_data import install_data
import sys,os
from shutil import copy2

import subprocess as sp
_gvi = sp.check_output(['gcc','--version']).splitlines()[0]
have_mingw_64 = 'x86_64' in _gvi and 'MinGW' in _gvi

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

class my_install_data(install_data):
	def run(self):
		for f in 'mmgen.cfg','mnemonic.py','mn_wordlist.c':
			os.chmod(os.path.join('data_files',f),0644)
		install_data.run(self)

module1 = Extension(
	name         = 'mmgen.secp256k1',
	sources      = ['extmod/secp256k1mod.c'],
	libraries    = ['secp256k1'],
	library_dirs = ['/usr/local/lib',r'c:\msys\local\lib'],
	# mingw32 needs this, Linux can use it, but it breaks mingw64
	extra_link_args = (['-lgmp'],[])[have_mingw_64],
	include_dirs = ['/usr/local/include',r'c:\msys\local\include'],
	)

from mmgen.globalvars import g
setup(
		name         = 'mmgen',
		description  = 'A complete Bitcoin offline/online wallet solution for the command line',
		version      = g.version,
		author       = g.author,
		author_email = g.email,
		url          = g.proj_url,
		license      = 'GNU GPL v3',
		platforms    = 'Linux, MS Windows, Raspberry Pi',
		keywords     = g.keywords,
		cmdclass     = { 'build_ext': my_build_ext, 'install_data': my_install_data },
		ext_modules = [module1],
		data_files = [('share/mmgen', [
				'data_files/mmgen.cfg',     # source files must have 0644 mode
				'data_files/mn_wordlist.c',
				'data_files/mnemonic.py'
				]),],
		py_modules = [
			'mmgen.__init__',
			'mmgen.addr',
			'mmgen.bitcoin',
			'mmgen.color',
			'mmgen.common',
			'mmgen.crypto',
			'mmgen.filename',
			'mmgen.globalvars',
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
			'mmgen.tw',
			'mmgen.tx',
			'mmgen.util',

			'mmgen.main',
			'mmgen.main_wallet',
			'mmgen.main_addrgen',
			'mmgen.main_addrimport',
			'mmgen.main_txcreate',
			'mmgen.main_txsign',
			'mmgen.main_txsend',
			'mmgen.main_txdo',
			'mmgen.txcreate',
			'mmgen.txsign',
			'mmgen.main_tool',

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
			'mmgen-txdo',
			'mmgen-tool'
		]
	)
