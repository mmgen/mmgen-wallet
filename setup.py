#!/usr/bin/env python3

import sys,os
from setuptools import setup,Extension
from setuptools.command.build_ext import build_ext
from subprocess import run,PIPE

cache_path = os.path.join(os.environ['HOME'],'.cache','mmgen')
ext_path = os.path.join(cache_path,'secp256k1')

def build_libsecp256k1():
	if not os.path.exists(cache_path):
		os.makedirs(cache_path)
	if not os.path.exists(ext_path):
		print('\nCloning libsecp256k1')
		run(['git','clone','https://github.com/bitcoin-core/secp256k1.git'],check=True,cwd=cache_path)
	if not os.path.exists(os.path.join(ext_path,'.libs/libsecp256k1.a')):
		import platform
		print('\nBuilding libsecp256k1')
		cmds = {
			'Windows': (
				['sh','./autogen.sh'],
				['sh','./configure','CFLAGS=-g -O2 -fPIC','--disable-dependency-tracking'],
				['mingw32-make','MAKE=mingw32-make']
			),
			'Linux': (
				['./autogen.sh'],
				['./configure','CFLAGS=-g -O2 -fPIC'],
				['make'] + ([] if have_arm else ['-j4']),
			),
		}[platform.system()]
		for cmd in cmds:
			print('Executing {}'.format(' '.join(cmd)))
			run(cmd,check=True,cwd=ext_path)

uname = {k:run(['uname',f'-{k}'],stdout=PIPE,check=True).stdout.strip().decode() for k in ('m','s')}

have_arm   = uname['m'] in ('aarch64','armv7l') # x86_64, aarch64, armv7l
have_msys2 = uname['s'].startswith('MSYS_NT')   # Linux, MSYS_NT.*

class my_build_ext(build_ext):
	def build_extension(self,ext):
		build_libsecp256k1()
		build_ext.build_extension(self,ext)

setup(
	cmdclass = { 'build_ext': my_build_ext },
	ext_modules = [Extension(
		name          = 'mmgen.secp256k1',
		sources       = ['extmod/secp256k1mod.c'],
		libraries     = ([],['gmp'])[have_msys2],
		extra_objects = [os.path.join(ext_path,'.libs/libsecp256k1.a')],
		include_dirs  = [os.path.join(ext_path,'include')],
	)]
)
