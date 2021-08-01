#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
opts.py:  MMGen-specific options processing after generic processing by share.Opts
"""
import sys,os,stat

from .exception import UserOptError
from .globalvars import g
from .base_obj import Lockable
import mmgen.share.Opts

class UserOpts(Lockable):
	_set_ok = ('usr_randchars',)
	_reset_ok = ('quiet','verbose','yes')

opt = UserOpts()

from .util import *

def usage():
	from mmgen.share import Opts
	Die(1,Opts.make_usage_str(g.prog_name,'user',usage_data))

def version():
	Die(0,fmt("""
		{pn} version {g.version}
		Part of the {g.proj_name} suite, an online/offline cryptocurrency wallet for the
		command line.  Copyright (C){g.Cdates} {g.author} {g.email}
	""".format(g=g,pn=g.prog_name.upper()),indent='    ').rstrip())

def print_help(po,opts_data,opt_filter):
	if not 'code' in opts_data:
		opts_data['code'] = {}

	from .protocol import init_proto_from_opts
	proto = init_proto_from_opts()

	if getattr(opt,'longhelp',None):
		opts_data['code']['long_options'] = common_opts_data['code']
		def remove_unneeded_long_opts():
			d = opts_data['text']['long_options']
			if g.prog_name != 'mmgen-tool':
				d = '\n'.join(''+i for i in d.split('\n') if not '--monero-wallet' in i)
			if proto.base_proto != 'Ethereum':
				d = '\n'.join(''+i for i in d.split('\n') if not '--token' in i)
			opts_data['text']['long_options'] = d
		remove_unneeded_long_opts()

	mmgen.share.Opts.print_help( # exits
		proto,
		po,
		opts_data,
		opt_filter )

def fmt_opt(o):
	return '--' + o.replace('_','-')

def die_on_incompatible_opts(incompat_list):
	for group in incompat_list:
		bad = [k for k in opt.__dict__ if k in group and getattr(opt,k) != None]
		if len(bad) > 1:
			die(1,'Conflicting options: {}'.format(', '.join(map(fmt_opt,bad))))

def _show_hash_presets():
	fs = '  {:<7} {:<6} {:<3}  {}'
	msg('Available parameters for scrypt.hash():')
	msg(fs.format('Preset','N','r','p'))
	for i in sorted(g.hash_presets.keys()):
		msg(fs.format(i,*g.hash_presets[i]))
	msg('N = memory usage (power of two), p = iterations (rounds)')
	sys.exit(0)

def opt_preproc_debug(po):
	d = (
		('Cmdline',            ' '.join(sys.argv)),
		('Opts',               po.opts),
		('Skipped opts',       po.skipped_opts),
		('User-selected opts', po.user_opts),
		('Cmd args',           po.cmd_args),
	)
	Msg('\n=== opts.py debug ===')
	for e in d:
		Msg('    {:<20}: {}'.format(*e))

def opt_postproc_debug():
	a = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) != None]
	b = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) == None]
	Msg('    Opts after processing:')
	for k in a:
		v = getattr(opt,k)
		Msg('        {:18}: {!r:<6} [{}]'.format(k,v,type(v).__name__))
	Msg("    Opts set to 'None':")
	Msg('        {}\n'.format('\n        '.join(b)))
	Msg('    Global vars:')
	for e in [d for d in dir(g) if d[:2] != '__']:
		Msg('        {:<20}: {}'.format(e, getattr(g,e)))
	Msg('\n=== end opts.py debug ===\n')

def override_globals_from_cfg_file(ucfg):
	from .protocol import CoinProtocol,init_proto
	for d in ucfg.get_lines():
		if d.name in g.cfg_file_opts:
			ns = d.name.split('_')
			if ns[0] in CoinProtocol.coins:
				nse,tn = (
					(ns[2:],ns[1]=='testnet') if len(ns) > 2 and ns[1] in ('mainnet','testnet') else
					(ns[1:],False)
				)
				cls = type(init_proto(ns[0],tn)) # no instance yet, so override _class_ attr
				attr = '_'.join(nse)
			else:
				cls = g                          # g is "singleton" instance, so override _instance_ attr
				attr = d.name
			refval = getattr(cls,attr)
			val = ucfg.parse_value(d.value,refval)
			if not val:
				raise CfgFileParseError(f'Parse error in file {ucfg.fn!r}, line {d.lineno}')
			val_conv = set_for_type(val,refval,attr,src=ucfg.fn)
			setattr(cls,attr,val_conv)
		else:
			raise CfgFileParseError(f'{d.name!r}: unrecognized option in {ucfg.fn!r}, line {d.lineno}')

def override_globals_and_set_opts_from_env(opt):
	for name in g.env_opts:
		if name == 'MMGEN_DEBUG_ALL':
			continue
		disable = name[:14] == 'MMGEN_DISABLE_'
		val = os.getenv(name) # os.getenv() returns None if env var is unset
		if val: # exclude empty string values; string value of '0' or 'false' sets variable to False
			gname = name[(6,14)[disable]:].lower()
			if hasattr(g,gname):
				setattr(g,gname,set_for_type(val,getattr(g,gname),name,disable))
			elif hasattr(opt,gname):
				if getattr(opt,gname) is None: # env must not override cmdline!
					setattr(opt,gname,val)
			else:
				raise ValueError(f'Name {gname} not present in globals or opts')

def show_common_opts_diff():

	def common_opts_data_to_list():
		for l in common_opts_data['text'].splitlines():
			if l.startswith('--,'):
				yield l.split()[1].split('=')[0][2:].replace('-','_')

	def do_fmt(set_data):
		return fmt_list(['--'+s.replace('_','-') for s in set_data],fmt='col',indent='   ')

	a = set(g.common_opts)
	b = set(common_opts_data_to_list())

	m1 = 'g.common_opts - common_opts_data:\n   {}\n'
	msg(m1.format(do_fmt(a-b) if a-b else 'None'))

	m2 = 'common_opts_data - g.common_opts (these do not set global var):\n{}\n'
	msg(m2.format(do_fmt(b-a)))

	m3 = 'common_opts_data ^ g.common_opts (these set global var):\n{}\n'
	msg(m3.format(do_fmt(b.intersection(a))))

	sys.exit(0)

common_opts_data = {
	# Most but not all of these set the corresponding global var
	# View differences with show_common_opts_diff()
	'text': """
--, --accept-defaults      Accept defaults at all prompts
--, --coin=c               Choose coin unit. Default: BTC. Current choice: {cu_dfl}
--, --token=t              Specify an ERC20 token by address or symbol
--, --color=0|1            Disable or enable color output
--, --force-256-color      Force 256-color output when color is enabled
--, --data-dir=path        Specify {pnm} data directory location
--, --daemon-data-dir=path Specify {dn} data directory location
--, --daemon-id=ID         Specify the coin daemon ID
--, --ignore-daemon-version Ignore {dn} version check
--, --no-license           Suppress the GPL license prompt
--, --rpc-host=host        Communicate with {dn} running on host 'host'
--, --rpc-port=port        Communicate with {dn} listening on port 'port'
--, --rpc-user=user        Authenticate to {dn} using username 'user'
--, --rpc-password=pass    Authenticate to {dn} using password 'pass'
--, --rpc-backend=backend  Use backend 'backend' for JSON-RPC communications
--, --aiohttp-rpc-queue-len=N Use 'N' simultaneous RPC connections with aiohttp
--, --monero-wallet-rpc-host=host  Specify Monero wallet daemon host
--, --monero-wallet-rpc-user=user  Specify Monero wallet daemon username
--, --monero-wallet-rpc-password=pass  Specify Monero wallet daemon password
--, --regtest=0|1          Disable or enable regtest mode
--, --testnet=0|1          Disable or enable testnet
--, --skip-cfg-file        Skip reading the configuration file
--, --version              Print version information and exit
--, --bob                  Switch to user "Bob" in MMGen regtest setup
--, --alice                Switch to user "Alice" in MMGen regtest setup
	""",
	'code': lambda help_notes,proto,s: s.format(
			pnm    = g.proj_name,
			dn     = help_notes('coind_exec'),
			cu_dfl = proto.coin,
		)
}

opts_data_dfl = {
	'text': {
		'desc': '',
		'usage':'',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long (common) options
"""
	}
}

def init(opts_data=None,add_opts=None,init_opts=None,opt_filter=None,parse_only=False):

	if opts_data is None:
		opts_data = opts_data_dfl

	opts_data['text']['long_options'] = common_opts_data['text']

	# po: (user_opts,cmd_args,opts,skipped_opts)
	po = mmgen.share.Opts.parse_opts(opts_data,opt_filter=opt_filter,parse_only=parse_only)

	if init_opts: # allow programs to preload user opts
		for uopt,val in init_opts.items():
			if uopt not in po.user_opts:
				po.user_opts[uopt] = val

	if parse_only:
		return po

	if g.debug_opts:
		opt_preproc_debug(po)

	# Copy parsed opts to opt, setting values to None if not set by user
	for o in set(
			po.opts
			+ po.skipped_opts
			+ tuple(add_opts or [])
			+ tuple(init_opts or [])
			+ g.required_opts
			+ g.common_opts ):
		setattr(opt,o,po.user_opts[o] if o in po.user_opts else None)

	# Make this available to usage()
	global usage_data
	usage_data = opts_data['text'].get('usage2') or opts_data['text']['usage']

	if opt.version:
		version() # exits

	# === begin global var initialization === #
	"""
	NB: user opt --data-dir is actually data_dir_root
	- data_dir is data_dir_root plus optionally 'regtest' or 'testnet', so for mainnet
	  data_dir == data_dir_root
	- As with Bitcoin Core, cfg file is in data_dir_root, wallets and other data are
	  in data_dir
	- Since cfg file is in data_dir_root, data_dir_root must be finalized before we
	  can process cfg file
	- Since data_dir depends on the values of g.testnet and g.regtest, these must be
	  finalized before setting data_dir
	"""
	if opt.data_dir:
		g.data_dir_root = os.path.normpath(os.path.expanduser(opt.data_dir))
	elif os.getenv('MMGEN_TEST_SUITE'):
		from test.include.common import get_data_dir
		g.data_dir_root = get_data_dir()
	else:
		g.data_dir_root = os.path.join(g.home_dir,'.'+g.proj_name.lower())

	check_or_create_dir(g.data_dir_root)

	from .term import init_term
	init_term()

	if not opt.skip_cfg_file:
		from .cfg import cfg_file
		# check for changes in system template file - term must be initialized
		cfg_file('sample')
		override_globals_from_cfg_file(cfg_file('usr'))

	override_globals_and_set_opts_from_env(opt)

	# Set globals from opts, setting type from original global value
	# Do here, before opts are set from globals below
	for k in (g.common_opts + g.opt_sets_global):
		if hasattr(opt,k):
			val = getattr(opt,k)
			if val != None and hasattr(g,k):
				setattr(g,k,set_for_type(val,getattr(g,k),'--'+k))

	"""
	g.color is finalized, so initialize color
	"""
	if g.color: # MMGEN_DISABLE_COLOR sets this to False
		from .color import init_color
		init_color(num_colors=('auto',256)[bool(g.force_256_color)])

	"""
	g.testnet and g.regtest are finalized, so we can set g.data_dir
	"""
	g.data_dir = os.path.normpath(os.path.join(
		g.data_dir_root,
		('regtest' if g.regtest else 'testnet' if g.testnet else '') ))

	# Set user opts from globals:
	# - if opt is unset, set it to global value
	# - if opt is set, convert its type to that of global value
	for k in g.global_sets_opt:
		if hasattr(opt,k) and getattr(opt,k) != None:
			setattr(opt,k,set_for_type(getattr(opt,k),getattr(g,k),'--'+k))
		else:
			setattr(opt,k,getattr(g,k))

	if opt.show_hash_presets: # exits
		_show_hash_presets()

	g.coin = g.coin.upper() or 'BTC'
	g.token = g.token.upper() or None

	if g.prog_name == 'mmgen-regtest' or g.bob or g.alice:
		g.regtest = True
		g.rpc_host = 'localhost'
		g.data_dir = os.path.join(g.data_dir_root,'regtest',g.coin.lower(),('alice','bob')[g.bob])
		from .regtest import MMGenRegtest
		g.rpc_user = MMGenRegtest.rpc_user
		g.rpc_password = MMGenRegtest.rpc_password
		g.rpc_port = MMGenRegtest(g.coin).d.rpc_port

	from .protocol import init_genonly_altcoins
	altcoin_trust_level = init_genonly_altcoins(
		g.coin,
		testnet = g.testnet or g.regtest )

	# === end global var initialization === #

	# print help screen only after global vars are initialized:
	if getattr(opt,'help',None) or getattr(opt,'longhelp',None):
		print_help(po,opts_data,opt_filter) # exits

	warn_altcoins(g.coin,altcoin_trust_level)

	die_on_incompatible_opts(g.incompatible_opts)

	check_or_create_dir(g.data_dir) # g.data_dir is finalized, so we can create it

	# Check user-set opts without modifying them
	check_usr_opts(po.user_opts)

	# Check all opts against g.autoset_opts, setting if unset
	check_and_set_autoset_opts()

	set_auto_typeset_opts()

	if opt.verbose:
		opt.quiet = None

	if g.debug and g.prog_name != 'test.py':
		opt.verbose,opt.quiet = (True,None)

	if g.debug_opts:
		opt_postproc_debug()

	# We don't need this data anymore
	del mmgen.share.Opts
	for k in ('text','notes','code'):
		if k in opts_data:
			del opts_data[k]

	g.lock()
	opt.lock()

	return po.cmd_args

# DISABLED
def opt_is_tx_fee(key,val,desc): # 'key' must remain a placeholder

	# contract data or non-standard startgas: disable fee checking
	if hasattr(opt,'contract_data') and opt.contract_data:
		return
	if hasattr(opt,'tx_gas') and opt.tx_gas:
		return

	from .tx import MMGenTX
	from .protocol import init_proto_from_opts
	tx = MMGenTX.New(init_proto_from_opts())
	# Size of 224 is just a ball-park figure to eliminate the most extreme cases at startup
	# This check will be performed again once we know the true size
	ret = tx.feespec2abs(val,224)

	if ret == False:
		raise UserOptError('{!r}: invalid {}\n(not a {} amount or {} specification)'.format(
				val,desc,tx.proto.coin.upper(),tx.rel_fee_desc))

	if ret > tx.proto.max_tx_fee:
		raise UserOptError('{!r}: invalid {}\n({} > max_tx_fee ({} {}))'.format(
				val,desc,ret.fmt(fs='1.1'),tx.proto.max_tx_fee,tx.proto.coin.upper()))

def check_usr_opts(usr_opts): # Raises an exception if any check fails

	def opt_splits(val,sep,n,desc):
		sepword = 'comma' if sep == ',' else 'colon' if sep == ':' else repr(sep)
		try:
			l = val.split(sep)
		except:
			raise UserOptError('{!r}: invalid {} (not {}-separated list)'.format(val,desc,sepword))

		if len(l) != n:
			raise UserOptError('{!r}: invalid {} ({} {}-separated items required)'.format(val,desc,n,sepword))

	def opt_compares(val,op_str,target,desc,desc2=''):
		import operator as o
		op_f = { '<':o.lt, '<=':o.le, '>':o.gt, '>=':o.ge, '=':o.eq }[op_str]
		if not op_f(val,target):
			d2 = desc2 + ' ' if desc2 else ''
			raise UserOptError('{}: invalid {} ({}not {} {})'.format(val,desc,d2,op_str,target))

	def opt_is_int(val,desc):
		if not is_int(val):
			raise UserOptError('{!r}: invalid {} (not an integer)'.format(val,desc))

	def opt_is_float(val,desc):
		try:
			float(val)
		except:
			raise UserOptError('{!r}: invalid {} (not a floating-point number)'.format(val,desc))

	def opt_is_in_list(val,tlist,desc):
		if val not in tlist:
			q,sep = (('',','),("'","','"))[type(tlist[0]) == str]
			fs = '{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}'
			raise UserOptError(fs.format(v=val,w=desc,q=q,o=sep.join(map(str,sorted(tlist)))))

	def opt_unrecognized(key,val,desc='value'):
		raise UserOptError('{!r}: unrecognized {} for option {!r}'.format(val,desc,fmt_opt(key)))

	def opt_display(key,val='',beg='For selected',end=':\n'):
		s = '{}={}'.format(fmt_opt(key),val) if val else fmt_opt(key)
		msg_r('{} option {!r}{}'.format(beg,s,end))

	def chk_in_fmt(key,val,desc):
		from .wallet import Wallet,IncogWallet,Brainwallet,IncogWalletHidden
		sstype = Wallet.fmt_code_to_type(val)
		if not sstype:
			opt_unrecognized(key,val)
		if key == 'out_fmt':
			p = 'hidden_incog_output_params'
			if sstype == IncogWalletHidden and not getattr(opt,p):
				m1 = 'Hidden incog format output requested.  '
				m2 = 'You must supply a file and offset with the {!r} option'
				raise UserOptError(m1+m2.format(fmt_opt(p)))
			if issubclass(sstype,IncogWallet) and opt.old_incog_fmt:
				opt_display(key,val,beg='Selected',end=' ')
				opt_display('old_incog_fmt',beg='conflicts with',end=':\n')
				raise UserOptError('Export to old incog wallet format unsupported')
			elif issubclass(sstype,Brainwallet):
				raise UserOptError('Output to brainwallet format unsupported')

	chk_out_fmt = chk_in_fmt

	def chk_hidden_incog_input_params(key,val,desc):
		a = val.rsplit(',',1) # permit comma in filename
		if len(a) != 2:
			opt_display(key,val)
			raise UserOptError('Option requires two comma-separated arguments')

		fn,offset = a
		opt_is_int(offset,desc)

		if key == 'hidden_incog_input_params':
			check_infile(fn,blkdev_ok=True)
			key2 = 'in_fmt'
		else:
			try: os.stat(fn)
			except:
				b = os.path.dirname(fn)
				if b: check_outdir(b)
			else:
				check_outfile(fn,blkdev_ok=True)
			key2 = 'out_fmt'

		if hasattr(opt,key2):
			val2 = getattr(opt,key2)
			from .wallet import IncogWalletHidden
			if val2 and val2 not in IncogWalletHidden.fmt_codes:
				fs = 'Option conflict:\n  {}, with\n  {}={}'
				raise UserOptError(fs.format(fmt_opt(key),fmt_opt(key2),val2))

	chk_hidden_incog_output_params = chk_hidden_incog_input_params

	def chk_seed_len(key,val,desc):
		opt_is_int(val,desc)
		opt_is_in_list(int(val),g.seed_lens,desc)

	def chk_hash_preset(key,val,desc):
		opt_is_in_list(val,list(g.hash_presets.keys()),desc)

	def chk_brain_params(key,val,desc):
		a = val.split(',')
		if len(a) != 2:
			opt_display(key,val)
			raise UserOptError('Option requires two comma-separated arguments')
		opt_is_int(a[0],'seed length '+desc)
		opt_is_in_list(int(a[0]),g.seed_lens,'seed length '+desc)
		opt_is_in_list(a[1],list(g.hash_presets.keys()),'hash preset '+desc)

	def chk_usr_randchars(key,val,desc):
		if val == 0:
			return
		opt_is_int(val,desc)
		opt_compares(val,'>=',g.min_urandchars,desc)
		opt_compares(val,'<=',g.max_urandchars,desc)

	def chk_tx_fee(key,val,desc):
		pass
#		opt_is_tx_fee(key,val,desc) # TODO: move this check elsewhere

	def chk_tx_confs(key,val,desc):
		opt_is_int(val,desc)
		opt_compares(val,'>=',1,desc)

	def chk_vsize_adj(key,val,desc):
		opt_is_float(val,desc)
		ymsg('Adjusting transaction vsize by a factor of {:1.2f}'.format(float(val)))

	def chk_key_generator(key,val,desc):
		opt_compares(val,'<=',len(g.key_generators),desc)
		opt_compares(val,'>',0,desc)

	def chk_coin(key,val,desc):
		from .protocol import CoinProtocol
		opt_is_in_list(val.lower(),CoinProtocol.coins,'coin')

# TODO: move this check elsewhere
#	def chk_rbf(key,val,desc):
#		if not proto.cap('rbf'):
#			m = '--rbf requested, but {} does not support replace-by-fee transactions'
#			raise UserOptError(m.format(proto.coin))

#	def chk_bob(key,val,desc):
#		m = "Regtest (Bob and Alice) mode not set up yet.  Run '{}-regtest setup' to initialize."
#		from .regtest import MMGenRegtest
#		try:
#			os.stat(os.path.join(MMGenRegtest(g.coin).d.datadir,'regtest','debug.log'))
#		except:
#			raise UserOptError(m.format(g.proj_name.lower()))
#
#	chk_alice = chk_bob

	def chk_locktime(key,val,desc):
		opt_is_int(val,desc)
		opt_compares(int(val),'>',0,desc)

# TODO: move this check elsewhere
#	def chk_token(key,val,desc):
#		if not 'token' in proto.caps:
#			raise UserOptError('Coin {!r} does not support the --token option'.format(tx.coin))
#		if len(val) == 40 and is_hex_str(val):
#			return
#		if len(val) > 20 or not all(s.isalnum() for s in val):
#			raise UserOptError('{!r}: invalid parameter for --token option'.format(val))

	cfuncs = { k:v for k,v in locals().items() if k.startswith('chk_') }

	for key in usr_opts:
		val = getattr(opt,key)
		desc = 'parameter for {!r} option'.format(fmt_opt(key))

		if key in g.infile_opts:
			check_infile(val) # file exists and is readable - dies on error
		elif key == 'outdir':
			check_outdir(val) # dies on error
		elif 'chk_'+key in cfuncs:
			cfuncs['chk_'+key](key,val,desc)
		elif g.debug:
			Msg('check_usr_opts(): No test for opt {!r}'.format(key))

def set_auto_typeset_opts():
	for key,ref_type in g.auto_typeset_opts.items():
		if hasattr(opt,key):
			val = getattr(opt,key)
			if val is not None: # typeset only if opt is set
				setattr(opt,key,ref_type(val))

def check_and_set_autoset_opts(): # Raises exception if any check fails

	def nocase_str(key,val,asd):
		try:
			return asd.choices.index(val)
		except:
			return 'one of'

	def nocase_pfx(key,val,asd):
		cs = [s.startswith(val.lower()) for s in asd.choices]
		if cs.count(True) == 1:
			return cs.index(True)
		else:
			return 'unique substring of'

	for key,asd in g.autoset_opts.items():
		if hasattr(opt,key):
			val = getattr(opt,key)
			if val is None:
				setattr(opt,key,asd.choices[0])
			else:
				ret = locals()[asd.type](key,val,asd)
				if type(ret) is str:
					m = '{!r}: invalid parameter for option --{} (not {}: {})'
					raise UserOptError(m.format(val,key.replace('_','-'),ret,fmt_list(asd.choices)))
				elif ret is True:
					setattr(opt,key,val)
				else:
					setattr(opt,key,asd.choices[ret])
