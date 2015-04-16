#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
filename.py:  Filename class and methods for the MMGen suite
"""
import sys,os
import mmgen.opt as opt
from mmgen.obj import *
import mmgen.globalvars as g
from mmgen.util import msg,fmt_code_to_sstype

class Filename(MMGenObject):

	exts = {
		'seed': {
			"mmdat":   "Wallet",
			"mmseed":  "SeedFile",
			"mmwords": "Mnemonic",
			"mmbrain": "Brainwallet",
			"mmincog": "IncogWallet",
			"mmincox": "IncogWalletHex",
		},
		'tx': {
			"raw":         "RawTX",
			"sig":         "SigTX",
		},
		'addr': {
			"addrs":       "AddrInfo",
			"keys":        "KeyInfo",
			"akeys":       "KeyAddrInfo",
			"akeys.mmenc": "KeyAddrInfoEnc",
		},
		'other': {
			"chk":         "AddrInfoChecksum",
			"mmenc":       "MMEncInfo",
		},
	}

	ftypes = {
		'seed': {
			"hincog":   "IncogWalletHidden",
		},
	}

	def __init__(self,fn,ftype=""):
		self.name     = fn
		self.dirname  = os.path.dirname(fn)
		self.basename = os.path.basename(fn)
		self.ext      = None

		def mf1(k): return k == ftype
		def mf2(k): return '.'+k == fn[-len('.'+k):]

		# find file info for ftype or extension
		e,attr,have_match = (self.ftypes,"ftype",mf1) if ftype else \
							(self.exts,"ext",mf2)

		for k in e:
			for j in e[k]:
				if have_match(j):
					setattr(self,attr,j)
					self.fclass = k
					self.sstype = e[k][j]

		if not hasattr(self,attr):
			die(2,"Unrecognized %s for file '%s'" % (attr,fn))

		# TODO: Check for Windows
		import stat
		if stat.S_ISBLK(os.stat(fn).st_mode):
			fd = os.open(fn, os.O_RDONLY)
			self.size = os.lseek(fd, 0, os.SEEK_END)
			os.close(fd)
		else:
			self.size = os.stat(fn).st_size
