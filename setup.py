#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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

import sys,os,subprocess
from shutil import copy2
_gvi = subprocess.check_output(['gcc','--version']).splitlines()[0]
have_mingw64 = 'x86_64' in _gvi and 'MinGW' in _gvi
have_arm     = subprocess.check_output(['uname','-m']).strip() == 'aarch64'

# Zipfile module under Windows (MinGW) can't handle UTF-8 filenames.
# Move it so that distutils will use the 'zip' utility instead.
def divert_zipfile_module():
	msg1 = 'Unable to divert zipfile module. UTF-8 filenames may be broken in the Python archive.'
	def return_warn(m):
		sys.stderr.write('WARNING: {}\n'.format(m))
		return False

	dirname = os.path.dirname(sys.modules['os'].__file__)
	if not dirname: return return_warn(msg1)
	stem = os.path.join(dirname,'zipfile')
	a,b = stem+'.py',stem+'-is-broken.py'

	try: os.stat(a)
	except: return

	try:
		sys.stderr.write('moving {} -> {}\n'.format(a,b))
		os.rename(a,b)
	except:
		return return_warn(msg1)
	else:
		try:
			os.unlink(stem+'.pyc')
			os.unlink(stem+'.pyo')
		except:
			pass

if have_mingw64:
# 	import zipfile
# 	sys.exit()
	divert_zipfile_module()

from distutils.core import setup,Extension
from distutils.command.build_ext import build_ext
from distutils.command.install_data import install_data

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
	extra_link_args = (['-lgmp'],[])[have_mingw64],
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
		platforms    = 'Linux, MS Windows, Raspberry Pi/Raspbian, Orange Pi/Armbian',
		keywords     = g.keywords,
		cmdclass     = { 'build_ext': my_build_ext, 'install_data': my_install_data },
		ext_modules  = [module1],
		data_files = [('share/mmgen', [
				'data_files/mmgen.cfg',     # source files must have 0644 mode
				'data_files/mn_wordlist.c',
				'data_files/mnemonic.py'
				]),],
		py_modules = [
			'mmgen.__init__',
			'mmgen.addr',
			'mmgen.altcoin',
			'mmgen.bech32',
			'mmgen.color',
			'mmgen.common',
			'mmgen.crypto',
			'mmgen.ed25519',
			'mmgen.filename',
			'mmgen.globalvars',
			'mmgen.license',
			'mmgen.mn_electrum',
			'mmgen.mn_tirosh',
			'mmgen.obj',
			'mmgen.opts',
			'mmgen.protocol',
			'mmgen.regtest',
			'mmgen.rpc',
			'mmgen.seed',
			'mmgen.sha256',
			'mmgen.term',
			'mmgen.test',
			'mmgen.tool',
			'mmgen.tw',
			'mmgen.tx',
			'mmgen.util',

			'mmgen.altcoins.__init__',

			'mmgen.altcoins.eth.__init__',
			'mmgen.altcoins.eth.obj',
			'mmgen.altcoins.eth.tx',
			'mmgen.altcoins.eth.tw',

			'mmgen.main',
			'mmgen.main_addrgen',
			'mmgen.main_addrimport',
			'mmgen.main_autosign',
			'mmgen.main_passgen',
			'mmgen.main_regtest',
			'mmgen.main_split',
			'mmgen.main_tool',
			'mmgen.main_txbump',
			'mmgen.main_txcreate',
			'mmgen.main_txdo',
			'mmgen.main_txsend',
			'mmgen.main_txsign',
			'mmgen.main_wallet',
			'mmgen.txsign',

			'mmgen.share.__init__',
			'mmgen.share.Opts',
		],
		scripts = [
			'cmds/mmgen-addrgen',
			'cmds/mmgen-keygen',
			'cmds/mmgen-passgen',
			'cmds/mmgen-addrimport',
			'cmds/mmgen-passchg',
			'cmds/mmgen-regtest',
			'cmds/mmgen-walletchk',
			'cmds/mmgen-walletconv',
			'cmds/mmgen-walletgen',
			'cmds/mmgen-split',
			'cmds/mmgen-txcreate',
			'cmds/mmgen-txbump',
			'cmds/mmgen-txsign',
			'cmds/mmgen-txsend',
			'cmds/mmgen-txdo',
			'cmds/mmgen-tool',
			'cmds/mmgen-autosign'
		]
	)
