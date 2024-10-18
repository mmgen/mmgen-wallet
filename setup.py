#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

import sys, os
from pathlib import Path
from subprocess import run, PIPE
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

def build_libsecp256k1():

	home          = Path(os.environ['HOME'])
	cache_path    = home.joinpath('.cache', 'mmgen')
	src_path      = home.joinpath('.cache', 'mmgen', 'secp256k1')
	lib_file      = src_path.joinpath('.libs', 'libsecp256k1.dll.a')
	root = Path().resolve().anchor
	installed_lib_file = Path(root, 'msys64', 'ucrt64', 'lib', 'libsecp256k1.dll.a')

	if installed_lib_file.exists():
		return

	# fix broken aclocal path:
	os.environ['ACLOCAL_PATH'] = '/C/msys64/ucrt64/share/aclocal:/C/msys64/usr/share/aclocal'

	if not src_path.exists():
		cache_path.mkdir(parents=True)
		print('\nCloning libsecp256k1')
		run(['git', 'clone', 'https://github.com/bitcoin-core/secp256k1.git'], check=True, cwd=cache_path)

	if not lib_file.exists():
		print(f'\nBuilding libsecp256k1 (cwd={str(src_path)})')
		cmds = (
			['sh', './autogen.sh'],
			['sh', './configure', 'CFLAGS=-g -O2 -fPIC', '--disable-dependency-tracking'],
			['mingw32-make', 'MAKE=mingw32-make'])
		for cmd in cmds:
			print('Executing {}'.format(' '.join(cmd)))
			run(cmd, check=True, cwd=src_path)

	if not installed_lib_file.exists():
		run(['mingw32-make', 'install', 'MAKE=mingw32-make'], check=True, cwd=src_path)

class my_build_ext(build_ext):
	def build_extension(self, ext):
		if sys.platform == 'win32':
			build_libsecp256k1()
		build_ext.build_extension(self, ext)

setup(
	cmdclass = {'build_ext': my_build_ext},
	ext_modules = [Extension(
		name      = 'mmgen.proto.secp256k1.secp256k1',
		sources   = ['extmod/secp256k1mod.c'],
		libraries = ['gmp', 'secp256k1'] if sys.platform == 'win32' else ['secp256k1'],
		include_dirs = ['/usr/local/include'] if sys.platform == 'darwin' else [],
		library_dirs = ['/usr/local/lib'] if sys.platform == 'darwin' else [],
	)]
)
