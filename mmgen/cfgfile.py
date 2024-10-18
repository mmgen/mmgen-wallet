#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
cfgfile: API for the MMGen runtime configuration file and related files
"""

import os, re
from collections import namedtuple

from .cfg import gc
from .util import msg, ymsg, suf, fmt, fmt_list, oneshot_warning, strip_comment, capfirst, die

def mmgen_cfg_file(cfg, id_str):
	return cfg_file.get_cls_by_id(id_str)(cfg)

class cfg_file:
	cur_ver = 2
	ver = None
	write_ok = False
	warn_missing = True
	write_metadata = False
	line_data = namedtuple('cfgfile_line', ['name', 'value', 'lineno', 'chunk'])
	fn_base = 'mmgen.cfg'

	class warn_missing_file(oneshot_warning):
		color = 'yellow' # has no effect, as color not initialized yet
		message = '{} not found at {!r}'

	def get_data(self, fn):
		try:
			with open(fn) as fp:
				return fp.read().splitlines()
		except:
			if self.warn_missing:
				self.warn_missing_file(div=fn, fmt_args=(self.desc, fn))
			return ''

	def copy_system_data(self, fn):
		assert self.write_ok, f'writing to file {fn!r} not allowed!'
		src = mmgen_cfg_file(self.cfg, 'sys')
		if src.data:
			data = src.data + src.make_metadata() if self.write_metadata else src.data
			try:
				with open(fn, 'w') as fp:
					fp.write('\n'.join(data)+'\n')
				os.chmod(fn, 0o600)
			except:
				die(2, f'ERROR: unable to write to {fn!r}')

	def parse_value(self, value, refval):
		if isinstance(refval, dict):
			m = re.fullmatch(r'((\s+\w+:\S+)+)', ' '+value) # expect one or more colon-separated values
			if m:
				return dict([i.split(':') for i in m[1].split()])
		elif isinstance(refval, (list, tuple)):
			m = re.fullmatch(r'((\s+\S+)+)', ' '+value)     # expect single value or list
			if m:
				ret = m[1].split()
				return ret if isinstance(refval, list) else tuple(ret)
		else:
			return value

	def get_lines(self):
		def gen_lines():
			for lineno, line in enumerate(self.data, 1):
				line = strip_comment(line)
				if line == '':
					continue
				m = re.fullmatch(r'(\w+)(\s+)(.*)', line)
				if m:
					yield self.line_data(m[1], m[3], lineno, None)
				else:
					die('CfgFileParseError', f'Parse error in file {self.fn!r}, line {lineno}')
		return gen_lines()

	@classmethod
	def get_cls_by_id(cls, id_str):
		d = {
			'usr':    CfgFileUsr,
			'sys':    CfgFileSampleSys,
			'sample': CfgFileSampleUsr,
		}
		return d[id_str]

class cfg_file_sample(cfg_file):

	@classmethod
	def cls_make_metadata(cls, data):
		return [f'# Version {cls.cur_ver} {cls.compute_chksum(data)}']

	@staticmethod
	def compute_chksum(data):
		import hashlib
		return hashlib.new('ripemd160', '\n'.join(data).encode()).hexdigest()

	@property
	def computed_chksum(self):
		return type(self).compute_chksum(self.data)

	def get_lines(self):
		"""
		The config file template contains some 'magic':
		- lines must either be empty or begin with '# '
		- each commented chunk must end with a parsable cfg variable line
		- chunks are delimited by one or more blank lines
		- lines beginning with '##' are ignored
		- everything up to first line beginning with '##' is ignored
		- last line is metadata line of the form '# Version VER_NUM HASH'
		"""

		def process_chunk(chunk, lineno):
			m = re.fullmatch(r'(#\s*)(\w+)(\s+)(.*)', chunk[-1])
			if m:
				return self.line_data(m[2], m[4], lineno, chunk)
			else:
				die('CfgFileParseError', f'Parse error in file {self.fn!r}, line {lineno}')

		def gen_chunks(lines):
			hdr = True
			chunk = []
			in_chunk = False

			for lineno, line in enumerate(lines, 1):

				if line.startswith('##'):
					hdr = False
					continue

				if hdr:
					continue

				if line == '':
					in_chunk = False
				elif line.startswith('#'):
					if in_chunk is False:
						if chunk:
							yield process_chunk(chunk, last_nonblank)
						chunk = [line]
						in_chunk = True
					else:
						chunk.append(line)
					last_nonblank = lineno
				else:
					die('CfgFileParseError', f'Parse error in file {self.fn!r}, line {lineno}')

			if chunk:
				yield process_chunk(chunk, last_nonblank)

		return list(gen_chunks(self.data))

class CfgFileUsr(cfg_file):
	desc = 'user configuration file'
	warn_missing = False
	write_ok = True

	def __init__(self, cfg):
		self.cfg = cfg
		self.fn = os.path.join(cfg.data_dir_root, self.fn_base)
		self.data = self.get_data(self.fn)
		if not self.data:
			self.copy_system_data(self.fn)

class CfgFileSampleSys(cfg_file_sample):
	desc = 'system sample configuration file'
	test_fn_subdir = 'usr.local.share'

	def __init__(self, cfg):
		self.cfg = cfg
		if self.cfg.test_suite_cfgtest:
			self.fn = os.path.join(cfg.data_dir_root, self.test_fn_subdir, self.fn_base)
			with open(self.fn) as fp:
				self.data = fp.read().splitlines()
		else:
			# self.fn is used for error msgs only, so file need not exist on filesystem
			self.fn = os.path.join(os.path.dirname(__file__), 'data', self.fn_base)
			self.data = gc.get_mmgen_data_file(self.fn_base).splitlines()

	def make_metadata(self):
		return [f'# Version {self.cur_ver} {self.computed_chksum}']

class CfgFileSampleUsr(cfg_file_sample):
	desc = 'sample configuration file'
	warn_missing = False
	write_ok = True
	chksum = None
	write_metadata = True
	details_confirm_prompt = 'View details?'
	out_of_date_fs = 'File {!r} is out of date - replacing'
	altered_by_user_fs = 'File {!r} was altered by user - replacing'

	def __init__(self, cfg):
		self.cfg = cfg
		self.fn = os.path.join(cfg.data_dir_root, f'{self.fn_base}.sample')
		self.data = self.get_data(self.fn)

		src = mmgen_cfg_file(cfg, 'sys')

		if not src.data:
			return

		if self.data:
			if self.parse_metadata():
				if self.chksum == self.computed_chksum:
					diff = self.diff(self.get_lines(), src.get_lines())
					if not diff:
						return
					self.show_changes(diff)
				else:
					msg(self.altered_by_user_fs.format(self.fn))
			else:
				msg(self.out_of_date_fs.format(self.fn))

		self.copy_system_data(self.fn)

	def parse_metadata(self):
		if self.data:
			m = re.match(r'# Version (\d+) ([a-f0-9]{40})$', self.data[-1])
			if m:
				self.ver = m[1]
				self.chksum = m[2]
				self.data = self.data[:-1] # remove metadata line
				return True

	def diff(self, a_tup, b_tup): # a=user, b=system
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

	def show_changes(self, diff):
		ymsg('Warning: configuration file options have changed!\n')
		for desc in ('added', 'removed'):
			data = diff[desc]
			if data:
				opts = fmt_list([i.name for i in data], fmt='bare')
				msg(f'  The following option{suf(data, verb="has")} been {desc}:\n    {opts}\n')
				if desc == 'removed' and data:
					uc = mmgen_cfg_file(self.cfg, 'usr')
					usr_names = [i.name for i in uc.get_lines()]
					rm_names = [i.name for i in data]
					bad = sorted(set(usr_names).intersection(rm_names))
					if bad:
						m = f"""
							The following removed option{suf(bad, verb='is')} set in {uc.fn!r}
							and must be deleted or commented out:
							{'  ' + fmt_list(bad, fmt='bare')}
						"""
						ymsg(fmt(m, indent='  ', strip_char='\t'))

		from .ui import keypress_confirm, do_pager
		while True:
			if not keypress_confirm(self.cfg, self.details_confirm_prompt, no_nl=True):
				return

			def get_details():
				for desc, data in diff.items():
					sep, sep2 = ('\n  ', '\n\n  ')
					if data:
						yield (
							f'{capfirst(desc)} section{suf(data)}:'
							+ sep2
							+ sep2.join([f'{sep.join(v.chunk)}' for v in data])
						)

			do_pager(
				'CONFIGURATION FILE CHANGES\n\n'
				+ '\n\n'.join(get_details()) + '\n'
			)
