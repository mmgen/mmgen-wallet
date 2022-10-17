#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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

import os,importlib
from .common import *

opts_data = {
	'text': {
		'desc':    f'Perform various {g.proj_name}- and cryptocoin-related operations',
		'usage':   '[opts] <command> <command args>',
		'options': """
-d, --outdir=       d  Specify an alternate directory 'd' for output
-h, --help             Print this help message
--, --longhelp         Print help message for long options (common options)
-e, --echo-passphrase  Echo passphrase or mnemonic to screen upon entry
-k, --use-internal-keccak-module Force use of the internal keccak module
-K, --keygen-backend=n Use backend 'n' for public key generation.  Options
                       for {coin_id}: {kgs}
-l, --list             List available commands
-p, --hash-preset= p   Use the scrypt hash parameters defined by preset 'p'
                       for password hashing (default: '{g.dfl_hash_preset}')
-P, --passwd-file= f   Get passphrase from file 'f'.
-q, --quiet            Produce quieter output
-r, --usr-randchars=n  Get 'n' characters of additional randomness from
                       user (min={g.min_urandchars}, max={g.max_urandchars})
-t, --type=t           Specify address type (valid choices: 'legacy',
                       'compressed', 'segwit', 'bech32', 'zcash_z')
-v, --verbose          Produce more verbose output
-X, --cached-balances  Use cached balances (Ethereum only)
-y, --yes              Answer 'yes' to prompts, suppress non-essential output
""",
	'notes': """

                               COMMANDS

{ch}
Type ‘{pn} help <command>’ for help on a particular command
"""
	},
	'code': {
		'options': lambda s, help_notes: s.format(
			kgs=help_notes('keygen_backends'),
			coin_id=help_notes('coin_id'),
			g=g,
		),
		'notes': lambda s, help_notes: s.format(
			ch=help_notes('tool_help'),
			pn=g.prog_name)
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
		'addr2scriptpubkey',
		'eth_checksummed_addr',
		'hex2wif',
		'privhex2addr',
		'privhex2pubhex',
		'pubhash2addr',
		'pubhex2addr',
		'pubhex2redeem_script',
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
		'passwdfile_chksum',
		'txview',
	),
	'filecrypt': (
		'decrypt',
		'encrypt',
	),
	'fileutil': (
		'extract_key_from_geth_wallet',
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

def create_call_sig(cmd,cls,as_string=False):

	m = getattr(cls,cmd)

	if 'varargs_call_sig' in m.__code__.co_varnames: # hack
		flag = 'VAR_ARGS'
		va = m.__defaults__[0]
		args,dfls,ann = va['args'],va['dfls'],va['annots']
	else:
		flag = None
		args = m.__code__.co_varnames[1:m.__code__.co_argcount]
		dfls = m.__defaults__ or ()
		ann  = m.__annotations__

	nargs = len(args) - len(dfls)
	dfl_types = tuple(
		ann[a] if a in ann and isinstance(ann[a],type) else type(dfls[i])
			for i,a in enumerate(args[nargs:]) )

	if as_string:
		get_type_from_ann = lambda x: 'str or STDIN' if ann[x] == 'sstr' else ann[x].__name__
		return ' '.join(
			[f'{a} [{get_type_from_ann(a)}]' for a in args[:nargs]] +
			['{a} [{b}={c!r}]'.format(
				a = a,
				b = dfl_types[n].__name__,
				c = dfls[n] )
					for n,a in enumerate(args[nargs:])] )
	else:
		get_type_from_ann = lambda x: 'str' if ann[x] == 'sstr' else ann[x].__name__
		return (
			[(a,get_type_from_ann(a)) for a in args[:nargs]],            # c_args
			dict([(a,dfls[n]) for n,a in enumerate(args[nargs:])]),      # c_kwargs
			dict([(a,dfl_types[n]) for n,a in enumerate(args[nargs:])]), # c_kwargs_types
			('STDIN_OK' if nargs and ann[args[0]] == 'sstr' else flag),  # flag
			ann )                                                        # ann

def process_args(cmd,cmd_args,cls):
	c_args,c_kwargs,c_kwargs_types,flag,ann = create_call_sig(cmd,cls)
	have_stdin_input = False

	def usage_die(s):
		msg(s)
		from .tool.help import usage
		usage(cmd)

	if flag != 'VAR_ARGS':
		if len(cmd_args) < len(c_args):
			usage_die(f'Command requires exactly {len(c_args)} non-keyword argument{suf(c_args)}')

		u_args = cmd_args[:len(c_args)]

		# If we're reading from a pipe, replace '-' with output of previous command
		if flag == 'STDIN_OK' and u_args and u_args[0] == '-':
			if sys.stdin.isatty():
				die( 'BadFilename', "Standard input is a TTY.  Can't use '-' as a filename" )
			else:
				from .util2 import parse_bytespec
				max_dlen_spec = '10kB' # limit input to 10KB for now
				max_dlen = parse_bytespec(max_dlen_spec)
				u_args[0] = os.read(0,max_dlen)
				have_stdin_input = True
				if len(u_args[0]) >= max_dlen:
					die(2,f'Maximum data input for this command is {max_dlen_spec}')
				if not u_args[0]:
					die(2,f'{cmd}: ERROR: no output from previous command in pipe')

	u_nkwargs = len(cmd_args) - len(c_args)
	u_kwargs = {}
	if flag == 'VAR_ARGS':
		cmd_args = ['dummy_arg'] + cmd_args
		t = [a.split('=',1) for a in cmd_args if '=' in a]
		tk = [a[0] for a in t]
		tk_bad = [a for a in tk if a not in c_kwargs]
		if set(tk_bad) != set(tk[:len(tk_bad)]): # permit non-kw args to contain '='
			die(1,f'{tk_bad[-1]!r}: illegal keyword argument')
		u_kwargs = dict(t[len(tk_bad):])
		u_args = cmd_args[:-len(u_kwargs) or None]
	elif u_nkwargs > 0:
		u_kwargs = dict([a.split('=',1) for a in cmd_args[len(c_args):] if '=' in a])
		if len(u_kwargs) != u_nkwargs:
			usage_die(f'Command requires exactly {len(c_args)} non-keyword argument{suf(c_args)}')
		if len(u_kwargs) > len(c_kwargs):
			usage_die(f'Command accepts no more than {len(c_kwargs)} keyword argument{suf(c_kwargs)}')

	for k in u_kwargs:
		if k not in c_kwargs:
			usage_die(f'{k!r}: invalid keyword argument')

	def conv_type(arg,arg_name,arg_type):
		if arg_type == 'bytes' and type(arg) != bytes:
			die(1,"'Binary input data must be supplied via STDIN")

		if have_stdin_input and arg_type == 'str' and isinstance(arg,bytes):
			from .globalvars import g
			NL = '\r\n' if g.platform == 'win' else '\n'
			arg = arg.decode()
			if arg[-len(NL):] == NL: # rstrip one newline
				arg = arg[:-len(NL)]

		if arg_type == 'bool':
			if arg.lower() in ('true','yes','1','on'):
				arg = True
			elif arg.lower() in ('false','no','0','off'):
				arg = False
			else:
				usage_die(f'{arg!r}: invalid boolean value for keyword argument')

		try:
			return __builtins__[arg_type](arg)
		except:
			die(1,f'{arg!r}: Invalid argument for argument {arg_name} ({arg_type!r} required)')

	if flag == 'VAR_ARGS':
		args = [conv_type(u_args[i],c_args[0][0],c_args[0][1]) for i in range(len(u_args))]
	else:
		args = [conv_type(u_args[i],c_args[i][0],c_args[i][1]) for i in range(len(c_args))]
	kwargs = {k:conv_type(u_kwargs[k],k,c_kwargs_types[k].__name__) for k in u_kwargs}

	return ( args, kwargs )

def process_result(ret,pager=False,print_result=False):
	"""
	Convert result to something suitable for output to screen and return it.
	If result is bytes and not convertible to utf8, output as binary using os.write().
	If 'print_result' is True, send the converted result directly to screen or
	pager instead of returning it.
	"""

	from .util import Msg,die

	def triage_result(o):
		if print_result:
			if pager:
				from .ui import do_pager
				do_pager(o)
			else:
				Msg(o)
		else:
			return o

	if ret == True:
		return True
	elif ret in (False,None):
		die(2,f'tool command returned {ret!r}')
	elif isinstance(ret,str):
		return triage_result(ret)
	elif isinstance(ret,int):
		return triage_result(str(ret))
	elif isinstance(ret,tuple):
		return triage_result('\n'.join([r.decode() if isinstance(r,bytes) else r for r in ret]))
	elif isinstance(ret,bytes):
		try:
			return triage_result(ret.decode())
		except:
			# don't add NL to binary data if it can't be converted to utf8
			if print_result:
				return os.write(1,ret)
			else:
				return ret
	else:
		die(2,f'tool.py: can’t handle return value of type {type(ret).__name__!r}')

def get_cmd_cls(cmd):
	for modname,cmdlist in mods.items():
		if cmd in cmdlist:
			return getattr(importlib.import_module(f'mmgen.tool.{modname}'),'tool_cmd')
	else:
		return False

def get_mod_cls(modname):
	return getattr(importlib.import_module(f'mmgen.tool.{modname}'),'tool_cmd')

if g.prog_name == 'mmgen-tool' and not opt._lock:

	po = opts.init( opts_data, parse_only=True )

	if po.user_opts.get('list'):
		def gen():
			for mod,cmdlist in mods.items():
				if mod == 'help':
					continue
				yield capfirst( get_mod_cls(mod).__doc__.lstrip().split('\n')[0] ) + ':'
				for cmd in cmdlist:
					yield '  ' + cmd
				yield ''
		Msg('\n'.join(gen()).rstrip())
		sys.exit(0)

	if len(po.cmd_args) < 1:
		opts.usage()

	cls = get_cmd_cls(po.cmd_args[0])

	if not cls:
		die(1,f'{po.cmd_args[0]!r}: no such command')

	cmd,*args = opts.init( opts_data, parsed_opts=po, need_proto=cls.need_proto )

	if cmd in ('help','usage') and args:
		args[0] = 'command_name=' + args[0]

	args,kwargs = process_args(cmd,args,cls)

	ret = getattr(cls(cmdname=cmd),cmd)(*args,**kwargs)

	if type(ret).__name__ == 'coroutine':
		ret = async_run(ret)

	process_result(
		ret,
		pager = kwargs.get('pager'),
		print_result = True )
