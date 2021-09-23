#!/usr/bin/env python3

from setuptools import setup,Extension
from subprocess import run,PIPE

have_msys2 = run(['uname','-s'],stdout=PIPE,check=True).stdout.startswith(b'MSYS_NT')
if have_msys2:
	print('MSYS2 system detected')

setup(ext_modules=[Extension(
	name         = 'mmgen.secp256k1',
	sources      = ['extmod/secp256k1mod.c'],
	libraries    = ['secp256k1'] + ([],['gmp'])[have_msys2],
	library_dirs = ['/usr/local/lib',r'C:\msys64\mingw64\lib',r'C:\msys64\usr\lib'],
	include_dirs = ['/usr/local/include',r'C:\msys64\mingw64\include',r'C:\msys64\usr\include'],
	)])
