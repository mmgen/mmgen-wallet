#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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

import sys

from ..cfg import gc

def version(cfg):
	from ..util import fmt
	print(fmt(f"""
		{gc.prog_name.upper()} version {gc.version}
		Part of {gc.proj_name} Wallet, an online/offline cryptocurrency wallet for the
		command line. Copyright (C){gc.Cdates} {gc.author} {gc.email}
	""", indent='  ').rstrip())
	sys.exit(0)

def list_daemon_ids(cfg):
	from ..daemon import CoinDaemon
	from ..util import msg, fmt_list
	msg('  {} {}'.format('Coin', 'Daemon IDs'))
	msg('  {} {}'.format('----', '----------'))
	for k, v in CoinDaemon.coins.items():
		msg('  {}  {}'.format(k, fmt_list(v.daemon_ids, fmt='barest')))
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

def gen_arg_tuple(cfg, func, text):

	def help_notes(k, *args, **kwargs):
		import importlib
		return getattr(importlib.import_module(
			f'{cfg._help_pkg}.help_notes').help_notes(proto, cfg), k)(*args, **kwargs)

	def help_mod(modname):
		import importlib
		return importlib.import_module(
			f'{cfg._opts.help_pkg}.{modname}').help(proto, cfg)

	from ..protocol import init_proto_from_cfg
	proto = init_proto_from_cfg(cfg, need_amt=True)

	d = {
		'proto':      proto,
		'help_notes': help_notes,
		'help_mod':   help_mod,
		'cfg':        cfg}

	for arg in func.__code__.co_varnames:
		yield d[arg] if arg in d else text

def make_usage_str(cfg, caller):
	indent, col1_w = {
		'help': (2, len(gc.prog_name) + 1),
		'user': (0, len('USAGE:')),
	}[caller]
	def gen():
		ulbl = 'USAGE:'
		for line in [cfg._usage_data.strip()] if isinstance(cfg._usage_data, str) else cfg._usage_data:
			yield '{a:{w}} {b} {c}'.format(
				a = ulbl,
				b = gc.prog_name,
				c = cfg._usage_code(*gen_arg_tuple(cfg, cfg._usage_code, line)) if cfg._usage_code else line,
				w = col1_w)
			ulbl = ''
	return ('\n' + (' ' * indent)).join(gen())

def usage(cfg):
	print(make_usage_str(cfg, caller='user'))
	sys.exit(0)

class Help:

	def make(self, cfg, opts):

		def gen_output():
			yield '  {} {}'.format(gc.prog_name.upper() + ':', opts.opts_data['text']['desc'].strip())
			yield make_usage_str(cfg, caller='help')
			yield self.help_type.upper().replace('_', ' ') + ':'

			# process code for options
			opts_text = nl.join(self.gen_text(opts))
			if 'options' in code:
				yield code['options'](*gen_arg_tuple(cfg, code['options'], opts_text))
			else:
				yield opts_text

			# process code for notes
			if 'notes' in text:
				if 'notes' in code:
					yield from code['notes'](*gen_arg_tuple(cfg, code['notes'], text['notes'])).splitlines()
				else:
					yield from text['notes'].splitlines()

		text = getattr(opts, self.data_desc)['text']
		code = getattr(opts, self.data_desc).get('code', {})
		nl = '\n  '

		return nl.join(gen_output()) + '\n'

class CmdHelp_v1(Help):

	help_type = 'options'
	data_desc = 'opts_data'

	def gen_text(self, opts):
		from ..opts import cmd_opts_v1_pat
		skipping = False
		for line in opts.opts_data['text']['options'].strip().splitlines():
			if m := cmd_opts_v1_pat.match(line):
				yield '{} --{} {}'.format(
					(f'-{m[1]},', '   ')[m[1] == '-'],
					m[2],
					m[4])
			elif not skipping:
				yield line

class CmdHelp_v2(CmdHelp_v1):

	def gen_text(self, opts):
		from ..opts import cmd_opts_v2_help_pat
		skipping = False
		coin_codes = opts.global_filter_codes.coin
		cmd_codes = opts.opts_data['filter_codes']
		for line in opts.opts_data['text']['options'][1:].rstrip().splitlines():
			m = cmd_opts_v2_help_pat.match(line)
			if m[1] == '+':
				if not skipping:
					yield line[6:]
			elif (coin_codes is None or m[1] in coin_codes) and m[2] in cmd_codes:
				yield '{} --{} {}'.format(
					(f'-{m[3]},', '   ')[m[3] == '-'],
					m[4],
					m[6]
				) if m[4] else m[6]
				skipping = False
			else:
				skipping = True

class GlobalHelp(Help):

	help_type = 'global_options'
	data_desc = 'global_opts_data'

	def gen_text(self, opts):
		from ..opts import global_opts_help_pat
		skipping = False
		coin_codes = opts.global_filter_codes.coin
		cmd_codes = opts.global_filter_codes.cmd
		for line in opts.global_opts_data['text']['options'][1:].rstrip().splitlines():
			m = global_opts_help_pat.match(line)
			if m[1] == '+':
				if not skipping:
					yield line[4:]
			elif (coin_codes is None or m[1] in coin_codes) and (cmd_codes is None or m[2] in cmd_codes):
				yield '  --{} {}'.format(m[3], m[5]) if m[3] else m[5]
				skipping = False
			else:
				skipping = True

def print_help(cfg, opts):

	if cfg.help:
		help_cls = CmdHelp_v2 if 'filter_codes' in opts.opts_data else CmdHelp_v1
	else:
		help_cls = GlobalHelp

	from ..ui import do_pager
	do_pager(help_cls().make(cfg, opts))
	sys.exit(0)
