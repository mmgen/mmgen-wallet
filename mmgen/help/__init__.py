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
help: help notes for MMGen suite commands
"""

import sys, re

from ..cfg import gc

def version(cfg):
	from ..util import fmt
	print(fmt(f"""
		{gc.prog_name.upper()} version {gc.version}
		Part of {gc.proj_name} Wallet, an online/offline cryptocurrency wallet for the
		command line. Copyright (C){gc.Cdates} {gc.author} {gc.email}
	""", indent='  ').rstrip())
	sys.exit(0)

def show_hash_presets(cfg):
	fs = '      {:<6} {:<3} {:<2} {}'
	from ..util import msg
	from ..crypto import Crypto
	msg('  Available parameters for scrypt.hash():')
	msg(fs.format('Preset', 'N', 'r', 'p'))
	for i in sorted(Crypto.hash_presets.keys()):
		msg(fs.format(i, *Crypto.hash_presets[i]))
	msg('  N = memory usage (power of two)\n  p = iterations (rounds)')
	sys.exit(0)

def make_usage_str(cfg, caller):
	indent, col1_w = {
		'help': (2, len(gc.prog_name) + 1),
		'user': (0, len('USAGE:')),
	}[caller]
	def gen():
		ulbl = 'USAGE:'
		for line in [cfg._usage_data.strip()] if isinstance(cfg._usage_data, str) else cfg._usage_data:
			yield f'{ulbl:{col1_w}} {gc.prog_name} {line}'
			ulbl = ''
	return ('\n' + (' ' * indent)).join(gen())

def usage(cfg):
	print(make_usage_str(cfg, caller='user'))
	sys.exit(0)

class Help:

	def make(self, cfg, opts, proto):

		def gen_arg_tuple(func, text):

			def help_notes(k):
				import importlib
				return getattr(importlib.import_module(
					f'{opts.help_pkg}.help_notes').help_notes(proto, cfg), k)()

			def help_mod(modname):
				import importlib
				return importlib.import_module(
					f'{opts.help_pkg}.{modname}').help(proto, cfg)

			d = {
				'proto':      proto,
				'help_notes': help_notes,
				'help_mod':   help_mod,
				'cfg':        cfg,
			}
			for arg in func.__code__.co_varnames:
				yield d[arg] if arg in d else text

		def gen_output():
			yield '  {} {}'.format(gc.prog_name.upper() + ':', text['desc'].strip())
			yield make_usage_str(cfg, caller='help')
			yield help_type.upper().replace('_', ' ') + ':'

			# process code for options
			opts_text = nl.join(self.gen_text(opts))
			if help_type in code:
				yield code[help_type](*tuple(gen_arg_tuple(code[help_type], opts_text)))
			else:
				yield opts_text

			# process code for notes
			if help_type == 'options' and 'notes' in text:
				if 'notes' in code:
					yield from code['notes'](*tuple(gen_arg_tuple(code['notes'], text['notes']))).splitlines()
				else:
					yield from text['notes'].splitlines()

		text = opts.opts_data['text']
		code = opts.opts_data['code']
		help_type = self.help_type
		nl = '\n  '

		return nl.join(gen_output()) + '\n'

class CmdHelp(Help):

	help_type = 'options'

	def gen_text(self, opts):
		opt_filter = opts.opt_filter
		from ..opts import cmd_opts_pat
		skipping = False
		for line in opts.opts_data['text']['options'].strip().splitlines():
			if m := cmd_opts_pat.match(line):
				if opt_filter:
					if m[1] in opt_filter:
						skipping = False
					else:
						skipping = True
						continue
				yield '{} --{} {}'.format(
					(f'-{m[1]},', '   ')[m[1] == '-'],
					m[2],
					m[4])
			elif not skipping:
				yield line

class GlobalHelp(Help):

	help_type = 'global_options'

	def gen_text(self, opts):
		from ..opts import global_opts_pat
		for line in opts.global_opts_data['text'][1:-2].splitlines():
			if m := global_opts_pat.match(line):
				if m[1] in opts.global_opts_filter.coin and m[2] in opts.global_opts_filter.cmd:
					yield '  --{} {}'.format(m[3], m[5])
					skipping = False
				else:
					skipping = True
			elif not skipping:
				yield line[4:]

def print_help(cfg, opts):

	from ..protocol import init_proto_from_cfg
	proto = init_proto_from_cfg(cfg, need_amt=True)

	if not 'code' in opts.opts_data:
		opts.opts_data['code'] = {}

	if cfg.help:
		cls = CmdHelp
	else:
		opts.opts_data['code']['global_options'] = opts.global_opts_data['code']
		cls = GlobalHelp

	from ..ui import do_pager
	do_pager(cls().make(cfg, opts, proto))
	sys.exit(0)
