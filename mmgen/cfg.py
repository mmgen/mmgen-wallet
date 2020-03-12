#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
cfg.py: API for the MMGen runtime configuration file and related files
"""

# NB: This module is used by override_from_cfg_file(), which is called before override_from_env()
# during init, so global config vars that are set from the environment (such as g.test_suite)
# cannot be used here.

import sys,os,re,hashlib
from collections import namedtuple

from mmgen.globalvars import *
from mmgen.util import *

def cfg_file(id_str):
	return CfgFile.get_cls_by_id(id_str)()

class CfgFile(object):
	cur_ver = 2
	ver = None
	write_ok = False
	warn_missing = True
	write_metadata = False
	fn_base = g.proj_name.lower() + '.cfg'
	file_not_found_fs = 'WARNING: {} not found at {!r}'

	def __init__(self):
		self.fn = os.path.join(self.fn_dir,self.fn_base)
		self.data = self.get_data()

	def get_data(self):
		try:
			return open(self.fn).read().splitlines()
		except:
			if self.warn_missing:
				msg(self.file_not_found_fs.format(self.desc,self.fn))
			return ''

	def copy_data(self):
		assert self.write_ok, 'writing to file {!r} not allowed!'.format(self.fn)
		src = cfg_file('sys')
		if src.data:
			data = src.data + src.make_metadata() if self.write_metadata else src.data
			try:
				open(self.fn,'w').write('\n'.join(data)+'\n')
				os.chmod(self.fn,0o600)
			except:
				die(2,'ERROR: unable to write to {!r}'.format(self.fn))

	def parse_var(self,line,lineno):
		try:
			m = re.match(r'(\w+)(\s+(\S+)|(\s+\w+:\S+)+)$',line) # allow multiple colon-separated values
			return (m[1], dict([i.split(':') for i in m[2].split()]) if m[4] else m[3])
		except:
			raise CfgFileParseError('Parse error in file {!r}, line {}'.format(self.fn,lineno))

	def parse(self):
		cdata = namedtuple('cfg_var',['name','value','lineno'])
		def do_parse():
			for n,line in enumerate(self.data,1):
				line = strip_comments(line)
				if line == '':
					continue
				yield cdata(*self.parse_var(line,n),n)
		return do_parse()

	@classmethod
	def get_cls_by_id(self,id_str):
		d = {
			'usr':    CfgFileUsr,
			'sys':    CfgFileSampleSys,
			'sample': CfgFileSampleUsr,
			'dist':   CfgFileSampleDist,
		}
		return d[id_str]

class CfgFileSample(CfgFile):

	@classmethod
	def cls_make_metadata(cls,data):
		return ['# Version {} {}'.format(cls.cur_ver,cls.compute_chksum(data))]

	@staticmethod
	def compute_chksum(data):
		return hashlib.new('ripemd160','\n'.join(data).encode()).hexdigest()

	@property
	def computed_chksum(self):
		return type(self).compute_chksum(self.data)

	def parse(self,parse_vars=False):
		"""
		The config file template contains some 'magic':
		- lines must either be empty or begin with '# '
		- each commented chunk must end with a parsable cfg variable line
		- chunks are delimited by one or more blank lines
		- lines beginning with '##' are ignored
		- everything up to first line beginning with '##' is ignored
		- last line is metadata line of the form '# Version VER_NUM HASH'
		"""

		cdata = namedtuple('chunk_data',['name','lines','lineno','parsed'])

		def process_chunk(chunk,n):
			last_line = chunk[-1].split()
			return cdata(
				last_line[1],
				chunk,
				n,
				self.parse_var(' '.join(last_line[1:]),n) if parse_vars else None,
			)

		def get_chunks(lines):
			hdr = True
			chunk = []
			in_chunk = False
			for n,line in enumerate(lines,1):
				if line.startswith('##'):
					hdr = False
					continue
				if hdr:
					continue

				if line == '':
					in_chunk = False
				elif line.startswith('# '):
					if in_chunk == False:
						if chunk:
							yield process_chunk(chunk,last_nonblank)
						chunk = [line]
						in_chunk = True
					else:
						chunk.append(line)
					last_nonblank = n
				else:
					die(2,'parse error in file {!r}, line {}'.format(self.fn,n))

			if chunk:
				yield process_chunk(chunk,last_nonblank)

		return list(get_chunks(self.data))

class CfgFileUsr(CfgFile):
	desc = 'user configuration file'
	warn_missing = False
	fn_dir = g.data_dir_root
	write_ok = True

	def __init__(self):
		super().__init__()
		if not self.data:
			self.copy_data()

class CfgFileSampleDist(CfgFileSample):
	desc = 'source distribution configuration file'
	fn_dir = 'data_files'

class CfgFileSampleSys(CfgFileSample):
	desc = 'system sample configuration file'
	test_fn_subdir = 'usr.local.share'

	@property
	def fn_dir(self):
		if os.getenv('MMGEN_TEST_SUITE_CFGTEST'):
			return os.path.join(g.data_dir_root,self.test_fn_subdir)
		else:
			return g.shared_data_path

	def make_metadata(self):
		return ['# Version {} {}'.format(self.cur_ver,self.computed_chksum)]

class CfgFileSampleUsr(CfgFileSample):
	desc = 'sample configuration file'
	warn_missing = False
	fn_base = g.proj_name.lower() + '.cfg.sample'
	fn_dir = g.data_dir_root
	write_ok = True
	chksum = None
	write_metadata = True
	details_confirm_prompt = 'View details?'
	out_of_date_fs = 'File {!r} is out of date - replacing'
	altered_by_user_fs = 'File {!r} was altered by user - replacing'

	def __init__(self):
		super().__init__()

		src = cfg_file('sys')
		if not src.data:
			return

		if self.data:
			if self.parse_metadata():
				if self.chksum == self.computed_chksum:
					diff = self.diff(self.parse(),src.parse())
					if not diff:
						return
					self.show_changes(diff)
				else:
					msg(self.altered_by_user_fs.format(self.fn))
			else:
				msg(self.out_of_date_fs.format(self.fn))

		self.copy_data()

	def parse_metadata(self):
		if self.data:
			m = re.match(r'# Version (\d+) ([a-f0-9]{40})$',self.data[-1])
			if m:
				self.ver = m[1]
				self.chksum = m[2]
				self.data = self.data[:-1] # remove metadata line
				return True

	def diff(self,a_tup,b_tup): # a=user, b=system
		a = [i.name for i in a_tup]#[3:] # Debug
		b = [i.name for i in b_tup]#[:-2] # Debug
		removed = set(a) - set(b)
		added   = set(b) - set(a)
		if removed or added:
			return {
				'removed': [i for i in a_tup if i.name in removed],
				'added':   [i for i in b_tup if i.name in added],
			}
		else:
			return None

	def show_changes(self,diff):
		ymsg('Warning: configuration file options have changed!\n')
		m1 = '  The following option{} been {}:\n    {}\n'
		m2 = """
			The following removed option{} set in {!r}
			and must be deleted or commented out:
			{}
		"""
		for desc in ('added','removed'):
			data = diff[desc]
			if data:
				opts = fmt_list([i.name for i in data],fmt='bare')
				msg(m1.format(suf(data,verb='has'),desc,opts))
				if desc == 'removed' and data:
					uc = cfg_file('usr')
					usr_names = [i.name for i in uc.parse()]
					rm_names = [i.name for i in data]
					bad = sorted(set(usr_names).intersection(rm_names))
					if bad:
						ymsg(fmt(m2,'  ').format(suf(bad,verb='is'),uc.fn,'  '+fmt_list(bad,fmt='bare')))

		while True:
			if not keypress_confirm(self.details_confirm_prompt,no_nl=True):
				return

			def get_details():
				for desc,data in diff.items():
					sep,sep2 = ('\n  ','\n\n  ')
					if data:
						yield (
							'{} section{}:'.format(capfirst(desc),suf(data))
							+ sep2
							+ sep2.join(['{}'.format(sep.join(v.lines)) for v in data])
						)

			do_pager(
				'CONFIGURATION FILE CHANGES\n\n'
				+ '\n\n'.join(get_details()) + '\n'
			)
