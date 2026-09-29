#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
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
mmgen-tool:  Perform various MMGen- and cryptocoin-related operations.
             Part of the MMGen suite
"""

import sys, os, importlib
from .cfg import gc, Config
from .util import Msg, die, capfirst, async_run, isAsync
from .tool import process_args

opts_data = {
	'filter_codes': ['-'],
	'text': {
		'desc':    f'Perform various {gc.proj_name}- and cryptocoin-related operations',
		'usage':   '[opts] <command> <command args>',
		'options': """
			-- -d, --outdir=       d  Specify an alternate directory 'd' for output
			-- -h, --help             Print this help message
			-- --, --longhelp         Print help message for long (global) options
			x- -a, --autosign         Operate on an autosigned transaction
			-- -e, --echo-passphrase  Echo passphrase or mnemonic to screen upon entry
			-- -k, --use-internal-keccak-module Force use of the internal keccak module
			-- -K, --keygen-backend=n Use backend 'n' for public key generation.  Options
			+                         for {coin_id}: {kgs}
			-- -l, --list             List available commands
			-- -p, --hash-preset= p   Use the scrypt hash parameters defined by preset 'p'
			+                         for password hashing (default: '{gc.dfl_hash_preset}')
			-- -P, --passwd-file= f   Get passphrase from file 'f'.
			-- -q, --quiet            Produce quieter output
			-- -r, --usr-randchars=n  Get 'n' characters of additional randomness from
			+                         user (min={cfg.min_urandchars}, max={cfg.max_urandchars})
			x- -s, --scroll           Use the curses-like scrolling interface for tracking
			+                         wallet views
			-- -t, --type=t           Specify address type (valid choices: 'legacy',
			+                         'compressed', 'segwit', 'bech32', 'zcash_z')
			-- -v, --verbose          Produce more verbose output
			-- -x, --proxy=P          Proxy HTTP connections via SOCKS5h proxy ‘P’ (host:port).
			+                         Use special value ‘env’ to honor *_PROXY environment
			+                         vars instead.
			e- -X, --cached-balances  Use cached balances
			-- -y, --yes              Answer 'yes' to prompts, suppress non-essential output
""",
	'notes': """

                               COMMANDS

{n_th}
Type ‘{pn} help <command>’ for help on a particular command
"""
	},
	'code': {
		'options': lambda cfg, s, help_notes: s.format(
			kgs     = help_notes('keygen_backends'),
			coin_id = help_notes('coin_id'),
			cfg     = cfg,
			gc      = gc,
		),
		'notes': lambda cfg, s, help_notes: s.format(
			n_th = help_notes('tool_help'),
			pn   = gc.prog_name)
	}
}

# NB: Command groups and commands are displayed on the help screen in the following order,
# so keep the command names sorted
mods = {
	'help': (
		'help',
		'usage',
	),
	'util': (
		'b32tohex',
		'b58chktohex',
		'b58tobytes',
		'b58tohex',
		'b6dtohex',
		'bytespec',
		'bytestob58',
		'hash160',
		'hash256',
		'hexdump',
		'hexlify',
		'hexreverse',
		'hextob32',
		'hextob58',
		'hextob58chk',
		'hextob6d',
		'id6',
		'id8',
		'randb58',
		'randhex',
		'str2id6',
		'to_bytespec',
		'unhexdump',
		'unhexlify',
	),
	'coin': (
		'addr2pubhash',
		'addr2pubhex',
		'addr2scriptpubkey',
		'eth_checksummed_addr',
		'hex2wif',
		'privhex2addr',
		'privhex2pubhex',
		'pubhash2addr',
		'pubhex2addr',
		'pubhex2redeem_script',
		'privhex2pair',
		'randpair',
		'randwif',
		'redeem_script2addr',
		'scriptpubkey2addr',
		'wif2addr',
		'wif2hex',
		'wif2redeem_script',
		'wif2segwit_pair',
	),
	'mnemonic': (
		'hex2mn',
		'mn2hex',
		'mn2hex_interactive',
		'mn_printlist',
		'mn_rand128',
		'mn_rand192',
		'mn_rand256',
		'mn_stats',
	),
	'file': (
		'addrfile_chksum',
		'keyaddrfile_chksum',
		'viewkeyaddrfile_chksum',
		'passwdfile_chksum',
		'txview',
	),
	'filecrypt': (
		'decrypt',
		'encrypt',
	),
	'fileutil': (
		'decrypt_keystore',
		'decrypt_geth_keystore',
		'find_incog_data',
		'rand2file',
	),
	'wallet': (
		'gen_addr',
		'gen_key',
		'get_subseed',
		'get_subseed_by_seed_id',
		'list_shares',
		'list_subseeds',
	),
	'rpc': (
		'add_label',
		'daemon_version',
		'getbalance',
		'listaddress',
		'listaddresses',
		'remove_address',
		'remove_label',
		'rescan_address',
		'rescan_blockchain',
		'resolve_address',
		'twexport',
		'twimport',
		'twview',
		'txhist',
	),
}

def process_result(ret, *, pager=False, print_result=False):
	"""
	Convert result to something suitable for output to screen and return it.
	If result is bytes and not convertible to utf8, output as binary using os.write().
	If 'print_result' is True, send the converted result directly to screen or
	pager instead of returning it.
	"""

	def triage_result(o):
		if print_result:
			if pager:
				from .ui import do_pager
				do_pager(o)
			else:
				Msg(o)
		else:
			return o

	match ret:
		case True:
			return True
		case False | None:
			die(2, f'tool command returned {ret!r}')
		case str():
			return triage_result(ret)
		case int():
			return triage_result(str(ret))
		case tuple():
			return triage_result('\n'.join([r.decode() if isinstance(r, bytes) else r for r in ret]))
		case bytes():
			try:
				return triage_result(ret.decode())
			except:
				# don't add NL to binary data if it can't be converted to utf8
				return os.write(1, ret) if print_result else ret
		case _:
			die(2, f'tool.py: can’t handle return value of type {type(ret).__name__!r}')

def get_cmd_cls(cmd):
	for modname, cmdlist in mods.items():
		if cmd in cmdlist:
			return importlib.import_module(f'mmgen.tool.{modname}').tool_cmd
	return False

def get_mod_cls(modname):
	return importlib.import_module(f'mmgen.tool.{modname}').tool_cmd

if gc.prog_name.endswith('-tool'):

	cfg = Config(opts_data=opts_data, parse_only=True)
	po = cfg._parsed_opts

	if po.user_opts.get('list'):
		def gen():
			for mod, cmdlist in mods.items():
				if mod == 'help':
					continue
				yield capfirst(get_mod_cls(mod).__doc__.lstrip().split('\n')[0]) + ':'
				for cmd in cmdlist:
					yield '  ' + cmd
				yield ''
		Msg('\n'.join(gen()).rstrip())
		sys.exit(0)

	if len(po.cmd_args) < 1:
		cfg._usage()

	cmd = po.cmd_args[0]

	cls = get_cmd_cls(cmd)

	if not cls:
		die(1, f'{cmd!r}: no such command')

	cfg = Config(
		opts_data   = opts_data,
		parsed_opts = po,
		need_proto  = cls.need_proto,
		init_opts   = {'rpc_backend':'aiohttp'} if cmd == 'twimport'
			and gc.machine != 'aarch64' # TODO: aiohttp + Reth is broken for arm64
				else None,
		process_opts = True)

	cmd, *args = cfg._args

	if cmd in ('help', 'usage') and args:
		args[0] = 'command_name=' + args[0]

	args, kwargs = process_args(cmd, args, cls)

	func = getattr(cls(cfg, cmdname=cmd), cmd)

	process_result(
		async_run(cfg, func, args=args, kwargs=kwargs) if isAsync(func) else func(*args, **kwargs),
		pager = kwargs.get('pager'),
		print_result = True)
