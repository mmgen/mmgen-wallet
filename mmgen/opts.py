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
opts: command-line options processing for the MMGen Project
"""

import sys, os, re
from collections import namedtuple

from .cfg import gc

def negated_opts(opts, data={}):
	if data:
		return data
	else:
		data.update(dict(
			((k[3:] if k.startswith('no-') else f'no-{k}'), v)
				for k, v in opts.items()
					if len(k) > 1 and not v.has_parm))
		return data

def get_opt_by_substring(opt, opts):
	matches = [o for o in opts if o.startswith(opt)]
	if len(matches) == 1:
		return matches[0]
	if len(matches) > 1:
		from .util import die
		die('CmdlineOptError', f'--{opt}: ambiguous option (not unique substring)')

def process_uopts(opts_data, opts):

	from .util import die

	def get_uopts():
		nonlocal uargs
		idx = 1
		argv_len = len(sys.argv)
		while idx < argv_len:
			arg = sys.argv[idx]
			if len(arg) > 4096:
				raise RuntimeError(f'{len(arg)} bytes: command-line argument too long')
			if arg.startswith('--'):
				if len(arg) == 2:
					uargs = sys.argv[idx+1:]
					return
				opt, parm = arg[2:].split('=', 1) if '=' in arg else (arg[2:], None)
				if len(opt) < 2:
					die('CmdlineOptError', f'--{opt}: option name must be at least two characters long')
				if (
						(_opt := opt) in opts
						or (_opt := get_opt_by_substring(_opt, opts))):
					if opts[_opt].has_parm:
						if parm:
							yield (opts[_opt].name, parm)
						else:
							idx += 1
							if idx == argv_len or (parm := sys.argv[idx]).startswith('-'):
								die('CmdlineOptError', f'missing parameter for option --{_opt}')
							yield (opts[_opt].name, parm)
					else:
						if parm:
							die('CmdlineOptError', f'option --{_opt} requires no parameter')
						yield (opts[_opt].name, True)
				elif (
						(_opt := opt) in negated_opts(opts)
						or (_opt := get_opt_by_substring(_opt, negated_opts(opts)))):
					if parm:
						die('CmdlineOptError', f'option --{_opt} requires no parameter')
					yield (negated_opts(opts)[_opt].name, False)
				else:
					die('CmdlineOptError', f'--{opt}: unrecognized option')
			elif arg[0] == '-' and len(arg) > 1:
				for j, sopt in enumerate(arg[1:], 2):
					if sopt in opts:
						if opts[sopt].has_parm:
							if arg[j:]:
								yield (opts[sopt].name, arg[j:])
							else:
								idx += 1
								if idx == argv_len or (parm := sys.argv[idx]).startswith('-'):
									die('CmdlineOptError', f'missing parameter for option -{sopt}')
								yield (opts[sopt].name, parm)
							break
						else:
							yield (opts[sopt].name, True)
					else:
						die('CmdlineOptError', f'-{sopt}: unrecognized option')
			else:
				uargs = sys.argv[idx:]
				return
			idx += 1

	uargs = []
	uopts = dict(get_uopts())

	if 'sets' in opts_data:
		for a_opt, a_val, b_opt, b_val in opts_data['sets']:
			if a_opt in uopts:
				u_val = uopts[a_opt]
				if (u_val and a_val == bool) or u_val == a_val:
					if b_opt in uopts and uopts[b_opt] != b_val:
						die(1,
							'Option conflict:'
							+ '\n  --{}={}, with'.format(b_opt.replace('_', '-'), uopts[b_opt])
							+ '\n  --{}={}\n'.format(a_opt.replace('_', '-'), uopts[a_opt]))
					else:
						uopts[b_opt] = b_val

	return uopts, uargs

cmd_opts_pat = re.compile(r'^-([a-zA-Z0-9-]), --([a-zA-Z0-9-]{2,64})(=| )(.+)')
global_opts_pat = re.compile(r'^\t\t\t(.)(.) --([a-zA-Z0-9-]{2,64})(=| )(.+)')
opt_tuple = namedtuple('cmdline_option', ['name', 'has_parm'])

def parse_opts(opts_data, opt_filter, global_opts_data, global_opts_filter):

	def parse_cmd_opts_text():
		for line in opts_data['text']['options'].strip().splitlines():
			m = cmd_opts_pat.match(line)
			if m and (not opt_filter or m[1] in opt_filter):
				ret = opt_tuple(m[2].replace('-', '_'), m[3] == '=')
				yield (m[1], ret)
				yield (m[2], ret)

	def parse_global_opts_text():
		for line in global_opts_data['text'].splitlines():
			m = global_opts_pat.match(line)
			if m and m[1] in global_opts_filter.coin and m[2] in global_opts_filter.cmd:
				yield (m[3], opt_tuple(m[3].replace('-', '_'), m[4] == '='))

	opts = tuple(parse_cmd_opts_text()) + tuple(parse_global_opts_text())

	uopts, uargs = process_uopts(opts_data, dict(opts))

	return namedtuple('parsed_cmd_opts', ['user_opts', 'cmd_args', 'opts'])(
		uopts, # dict
		uargs, # list, callers can pop
		tuple(v.name for k, v in opts if len(k) > 1)
	)

def opt_preproc_debug(po):
	d = (
		('Cmdline',            ' '.join(sys.argv), False),
		('Filtered opts',      po.filtered_opts,   False),
		('User-selected opts', po.user_opts,       False),
		('Cmd args',           po.cmd_args,        False),
		('Opts',               po.opts,            True),
	)
	from .util import Msg, fmt_list
	Msg('\n=== opts.py debug ===')
	for label, data, pretty in d:
		Msg('    {:<20}: {}'.format(label, '\n' + fmt_list(data, fmt='col', indent=' '*8) if pretty else data))

opts_data_dfl = {
	'text': {
		'desc': '',
		'usage':'[options]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long (global) options
"""
	}
}

def get_coin():
	for n, arg in enumerate(sys.argv[1:]):
		if len(arg) > 4096:
			raise RuntimeError(f'{len(arg)} bytes: command-line argument too long')
		if arg.startswith('--coin='):
			return arg.removeprefix('--coin=').lower()
		if arg == '--coin':
			if len(sys.argv) < n + 3:
				from .util import die
				die('CmdlineOptError', f'{arg}: missing parameter')
			return sys.argv[n + 2].lower()
		if arg == '-' or not arg.startswith('-'): # stop at first non-option
			return 'btc'
	return 'btc'

class Opts:

	def __init__(
			self,
			cfg,
			opts_data,
			init_opts,    # dict containing opts to pre-initialize
			opt_filter,   # whitelist of opt letters; all others are skipped
			parsed_opts,
			need_proto):

		if len(sys.argv) > 257:
			raise RuntimeError(f'{len(sys.argv) - 1}: too many command-line arguments')

		opts_data = opts_data or opts_data_dfl
		self.opt_filter = opt_filter

		self.global_opts_filter = self.get_global_opts_filter(need_proto)
		self.opts_data = opts_data

		po = parsed_opts or parse_opts(opts_data, opt_filter, self.global_opts_data, self.global_opts_filter)

		cfg._args = po.cmd_args
		cfg._uopts = uopts = po.user_opts

		if init_opts: # initialize user opts to given value
			for uopt, val in init_opts.items():
				if uopt not in uopts:
					uopts[uopt] = val

		cfg._opts = self
		cfg._parsed_opts = po
		cfg._use_env = True
		cfg._use_cfg_file = not 'skip_cfg_file' in uopts
		# Make this available to usage()
		cfg._usage_data = opts_data['text'].get('usage2') or opts_data['text']['usage']

		if os.getenv('MMGEN_DEBUG_OPTS'):
			opt_preproc_debug(po)

		for funcname in self.info_funcs:
			if funcname in uopts:
				import importlib
				getattr(importlib.import_module(self.help_pkg), funcname)(cfg) # exits

class UserOpts(Opts):

	help_pkg = 'mmgen.help'
	info_funcs = ('usage', 'version', 'show_hash_presets')

	global_opts_data = {
		#  coin code : cmd code : opt : opt param : text
		'text': """
			-- --accept-defaults      Accept defaults at all prompts
			hp --cashaddr=0|1         Display addresses in cashaddr format (default: 1)
			-p --coin=c               Choose coin unit. Default: BTC. Current choice: {cu_dfl}
			er --token=t              Specify an ERC20 token by address or symbol
			-- --color=0|1            Disable or enable color output (default: 1)
			-- --columns=N            Force N columns of output with certain commands
			Rr --scroll               Use the curses-like scrolling interface for
			+                         tracking wallet views
			-- --force-256-color      Force 256-color output when color is enabled
			-- --pager                Pipe output of certain commands to pager (WIP)
			-- --data-dir=path        Specify {pnm} data directory location
			rr --daemon-data-dir=path Specify coin daemon data directory location
			Rr --daemon-id=ID         Specify the coin daemon ID
			rr --ignore-daemon-version Ignore coin daemon version check
			rr --http-timeout=t       Set HTTP timeout in seconds for JSON-RPC connections
			-- --no-license           Suppress the GPL license prompt
			rr --rpc-host=HOST        Communicate with coin daemon running on host HOST
			rr --rpc-port=PORT        Communicate with coin daemon listening on port PORT
			rr --rpc-user=USER        Authenticate to coin daemon using username USER
			rr --rpc-password=PASS    Authenticate to coin daemon using password PASS
			Rr --rpc-backend=backend  Use backend 'backend' for JSON-RPC communications
			Rr --aiohttp-rpc-queue-len=N Use N simultaneous RPC connections with aiohttp
			-p --regtest=0|1          Disable or enable regtest mode
			-- --testnet=0|1          Disable or enable testnet
			br --tw-name=NAME         Specify alternate name for the BTC/LTC/BCH tracking
			+                         wallet (default: ‘{tw_name}’)
			-- --skip-cfg-file        Skip reading the configuration file
			-- --version              Print version information and exit
			-- --usage                Print usage information and exit
			b- --bob                  Specify user ‘Bob’ in MMGen regtest mode
			b- --alice                Specify user ‘Alice’ in MMGen regtest mode
			b- --carol                Specify user ‘Carol’ in MMGen regtest mode
		""",
		'code': lambda proto, help_notes, s: s.format(
			pnm     = gc.proj_name,
			cu_dfl  = proto.coin,
			tw_name = help_notes('dfl_twname'))
	}

	@staticmethod
	def get_global_opts_filter(need_proto):
		"""
		Coin codes:
		  'b' - Bitcoin or Bitcoin code fork supporting RPC
		  'R' - Bitcoin or Ethereum code fork supporting RPC
		  'e' - Ethereum or Ethereum code fork
		  'r' - coin supporting RPC
		  'h' - Bitcoin Cash
		  '-' - other coin
		Cmd codes:
		  'p' - proto required
		  'r' - RPC required
		  '-' - no capabilities required
		"""
		ret = namedtuple('global_opts_filter', ['coin', 'cmd'])
		if caps := gc.cmd_caps:
			coin = caps.coin if caps.coin and len(caps.coin) > 1 else get_coin()
			return ret(
				coin = (
					('-', 'r', 'R', 'b', 'h') if coin == 'bch' else
					('-', 'r', 'R', 'b') if coin in gc.btc_fork_rpc_coins else
					('-', 'r', 'R', 'e') if coin in gc.eth_fork_coins else
					('-', 'r') if coin in gc.rpc_coins else
					('-')),
				cmd = (
					['-']
					+ (['r'] if caps.rpc else [])
					+ (['p'] if caps.proto else [])
				))
		else:
			return ret(
				coin = ('-', 'r', 'R', 'b', 'h', 'e'),
				cmd = ('-', 'r', 'p')
			)
