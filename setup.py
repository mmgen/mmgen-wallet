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
		run(['git','clone','https://github.com/bitcoin-core/secp256k1.git'],check=True,cwd=cache_path)
	if not os.path.exists(os.path.join(ext_path,'.libs/libsecp256k1.a')):
		run(['./autogen.sh'],check=True,cwd=ext_path)
		run(['./configure','CFLAGS=-g -O2 -fPIC'],check=True,cwd=ext_path)
		run(['make','-j4'],check=True,cwd=ext_path)

have_msys2 = run(['uname','-s'],stdout=PIPE,check=True).stdout.startswith(b'MSYS_NT')
if have_msys2:
	print('MSYS2 system detected')

class my_build_ext(build_ext):
	def build_extension(self,ext):
		build_libsecp256k1()
		build_ext.build_extension(self,ext)

setup(
	cmdclass = { 'build_ext': my_build_ext },
	ext_modules = [Extension(
		name         = 'mmgen.secp256k1',
		sources      = ['extmod/secp256k1mod.c'],
		libraries    = ([],['gmp'])[have_msys2],
		extra_objects = [os.path.join(ext_path,'.libs/libsecp256k1.a')],
		include_dirs = [os.path.join(ext_path,'include')],
	)]
)
