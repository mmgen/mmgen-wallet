#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
opts: MMGen-specific options processing after generic processing by share.Opts
"""
import sys,os,stat

from .globalvars import g
from .base_obj import Lockable

import mmgen.share.Opts

class UserOpts(Lockable):
	_autolock = False
	_default_to_none = True
	_set_ok = ('usr_randchars',)
	_reset_ok = ('quiet','verbose','yes')

opt = UserOpts()

def usage():
	from .util import Die
	Die(1,mmgen.share.Opts.make_usage_str(g.prog_name,'user',usage_data))

def version():
	from .util import Die,fmt
	Die(0,fmt(f"""
		{g.prog_name.upper()} version {g.version}
		Part of the {g.proj_name} suite, an online/offline cryptocurrency wallet for the
		command line.  Copyright (C){g.Cdates} {g.author} {g.email}
	""",indent='  ').rstrip())

def delete_data(opts_data):
	for k in ('text','notes','code'):
		if k in opts_data:
			del opts_data[k]
	del mmgen.share.Opts.make_help
	del mmgen.share.Opts.process_uopts
	del mmgen.share.Opts.parse_opts

def post_init():
	global opts_data_save,opt_filter_save
	if opt.help or opt.longhelp:
		print_help(opt,opts_data_save,opt_filter_save)
	else:
		delete_data(opts_data_save)
		del opts_data_save,opt_filter_save

def print_help(opt,opts_data,opt_filter):
	if not 'code' in opts_data:
		opts_data['code'] = {}

	from .protocol import init_proto_from_opts
	proto = init_proto_from_opts(need_amt=True)

	if getattr(opt,'longhelp',None):
		opts_data['code']['long_options'] = common_opts_data['code']
		def remove_unneeded_long_opts():
			d = opts_data['text']['long_options']
			if proto.base_proto != 'Ethereum':
				d = '\n'.join(''+i for i in d.split('\n') if not '--token' in i)
			opts_data['text']['long_options'] = d
		remove_unneeded_long_opts()

	from .ui import do_pager
	do_pager(
		mmgen.share.Opts.make_help(
			proto,
			opt,
			opts_data,
			opt_filter ))

	sys.exit(0)

def fmt_opt(o):
	return '--' + o.replace('_','-')

def die_on_incompatible_opts(incompat_list):
	for group in incompat_list:
		bad = [k for k in opt.__dict__ if k in group and getattr(opt,k) != None]
		if len(bad) > 1:
			from .util import die
			die(1,'Conflicting options: {}'.format(', '.join(map(fmt_opt,bad))))

def _show_hash_presets():
	fs = '  {:<7} {:<6} {:<3}  {}'
	from .util import msg
	from .crypto import hash_presets
	msg('Available parameters for scrypt.hash():')
	msg(fs.format('Preset','N','r','p'))
	for i in sorted(hash_presets.keys()):
		msg(fs.format(i,*hash_presets[i]))
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
	from .util import Msg
	Msg('\n=== opts.py debug ===')
	for e in d:
		Msg('    {:<20}: {}'.format(*e))

def opt_postproc_debug():
	a = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) != None]
	b = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) == None]
	from .util import Msg
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

def set_for_type(val,refval,desc,invert_bool=False,src=None):

	if type(refval) == bool:
		v = str(val).lower()
		ret = (
			True  if v in ('true','yes','1','on') else
			False if v in ('false','no','none','0','off','') else
			None
		)
		if ret is not None:
			return not ret if invert_bool else ret
	else:
		try:
			return type(refval)(not val if invert_bool else val)
		except:
			pass

	from .util import die
	die(1,'{!r}: invalid value for {!r}{} (must be of type {!r})'.format(
		val,
		desc,
		' in {!r}'.format(src) if src else '',
		type(refval).__name__) )

def override_globals_from_cfg_file(ucfg,autoset_opts,env_globals,need_proto):
	if need_proto:
		from .protocol import init_proto
	for d in ucfg.get_lines():
		if d.name in g.cfg_file_opts:
			ns = d.name.split('_')
			if ns[0] in g.core_coins:
				if not need_proto:
					continue
				nse,tn = (
					(ns[2:],ns[1]=='testnet') if len(ns) > 2 and ns[1] in ('mainnet','testnet') else
					(ns[1:],False)
				)
				cls = type(init_proto( ns[0], tn, need_amt=True )) # no instance yet, so override _class_ attr
				attr = '_'.join(nse)
			else:
				cls = g                          # g is "singleton" instance, so override _instance_ attr
				attr = d.name
			refval = getattr(cls,attr)
			val = ucfg.parse_value(d.value,refval)
			if not val:
				from .util import die
				die( 'CfgFileParseError', f'Parse error in file {ucfg.fn!r}, line {d.lineno}' )
			val_conv = set_for_type(val,refval,attr,src=ucfg.fn)
			if attr not in env_globals:
				setattr(cls,attr,val_conv)
		elif d.name in g.autoset_opts:
			autoset_opts[d.name] = d.value
		else:
			from .util import die
			die( 'CfgFileParseError', f'{d.name!r}: unrecognized option in {ucfg.fn!r}, line {d.lineno}' )

def override_globals_and_set_opts_from_env(opt):
	for name,val in ((k,v) for k,v in os.environ.items() if k.startswith('MMGEN_')):
		if name == 'MMGEN_DEBUG_ALL':
			continue
		elif name in g.env_opts:
			if val: # ignore empty string values; string value of '0' or 'false' sets variable to False
				disable = name.startswith('MMGEN_DISABLE_')
				gname = name[(6,14)[disable]:].lower()
				if hasattr(g,gname):
					setattr(g,gname,set_for_type(val,getattr(g,gname),name,disable))
					yield gname
				elif hasattr(opt,gname):
					if getattr(opt,gname) is None: # env must not override cmdline!
						setattr(opt,gname,val)
				else:
					raise ValueError(f'Name {gname!r} not present in globals or opts')
		else:
			raise ValueError(f'{name!r} is not a valid MMGen environment variable')

def show_common_opts_diff():

	def common_opts_data_to_list():
		for l in common_opts_data['text'].splitlines():
			if l.startswith('--,'):
				yield l.split()[1].split('=')[0][2:].replace('-','_')

	def do_fmt(set_data):
		from .util import fmt_list
		return fmt_list(['--'+s.replace('_','-') for s in set_data],fmt='col',indent='   ')

	a = g.common_opts
	b = list(common_opts_data_to_list())
	a_minus_b = [e for e in a if e not in b]
	b_minus_a = [e for e in b if e not in a]
	a_and_b   = [e for e in a if e in b]

	from .util import msg
	msg(f'g.common_opts - common_opts_data:\n   {do_fmt(a_minus_b) if a_minus_b else "None"}\n')
	msg(f'common_opts_data - g.common_opts (these do not set global var):\n{do_fmt(b_minus_a)}\n')
	msg(f'common_opts_data ^ g.common_opts (these set global var):\n{do_fmt(a_and_b)}\n')

	sys.exit(0)

common_opts_data = {
	# Most but not all of these set the corresponding global var
	# View differences with show_common_opts_diff()
	'text': """
--, --accept-defaults      Accept defaults at all prompts
--, --coin=c               Choose coin unit. Default: BTC. Current choice: {cu_dfl}
--, --token=t              Specify an ERC20 token by address or symbol
--, --color=0|1            Disable or enable color output (enabled by default)
--, --columns=N            Force N columns of output with certain commands
--, --scroll               Use the curses-like scrolling interface for
                           tracking wallet views
--, --force-256-color      Force 256-color output when color is enabled
--, --pager                Pipe output of certain commands to pager (WIP)
--, --data-dir=path        Specify {pnm} data directory location
--, --daemon-data-dir=path Specify coin daemon data directory location
--, --daemon-id=ID         Specify the coin daemon ID
--, --ignore-daemon-version Ignore coin daemon version check
--, --http-timeout=t       Set HTTP timeout in seconds for JSON-RPC connections
--, --no-license           Suppress the GPL license prompt
--, --rpc-host=HOST        Communicate with coin daemon running on host HOST
--, --rpc-port=PORT        Communicate with coin daemon listening on port PORT
--, --rpc-user=USER        Authenticate to coin daemon using username USER
--, --rpc-password=PASS    Authenticate to coin daemon using password PASS
--, --rpc-backend=backend  Use backend 'backend' for JSON-RPC communications
--, --aiohttp-rpc-queue-len=N Use N simultaneous RPC connections with aiohttp
--, --regtest=0|1          Disable or enable regtest mode
--, --testnet=0|1          Disable or enable testnet
--, --skip-cfg-file        Skip reading the configuration file
--, --version              Print version information and exit
--, --bob                  Specify user “Bob” in MMGen regtest mode
--, --alice                Specify user “Alice” in MMGen regtest mode
--, --carol                Specify user “Carol” in MMGen regtest mode
	""",
	'code': lambda help_notes,proto,s: s.format(
			pnm    = g.proj_name,
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

def init(
	opts_data   = None,
	add_opts    = None,
	init_opts   = None,
	opt_filter  = None,
	parse_only  = False,
	parsed_opts = None,
	need_proto  = True,
	do_post_init = False,
	return_parsed = False ):

	if opts_data is None:
		opts_data = opts_data_dfl

	opts_data['text']['long_options'] = common_opts_data['text']

	# Make this available to usage()
	global usage_data
	usage_data = opts_data['text'].get('usage2') or opts_data['text']['usage']

	# po: (user_opts,cmd_args,opts,skipped_opts)
	po = parsed_opts or mmgen.share.Opts.parse_opts(opts_data,opt_filter=opt_filter,parse_only=parse_only)

	if init_opts: # allow programs to preload user opts
		for uopt,val in init_opts.items():
			if uopt not in po.user_opts:
				po.user_opts[uopt] = val

	if parse_only and not any(k in po.user_opts for k in ('version','help','longhelp')):
		return po

	if g.debug_opts:
		opt_preproc_debug(po)

	# Copy parsed opts to opt, setting values to None if not set by user
	for o in set(
			po.opts
			+ po.skipped_opts
			+ tuple(add_opts or [])
			+ tuple(init_opts or [])
			+ g.init_opts
			+ g.common_opts ):
		setattr(opt,o,po.user_opts[o] if o in po.user_opts else None)

	if opt.version:
		version() # exits

	# === begin global var initialization === #

	env_globals = tuple(override_globals_and_set_opts_from_env(opt))

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
		g.data_dir_root = os.path.normpath(os.path.abspath(opt.data_dir))
	elif g.test_suite:
		from test.include.common import get_test_data_dir
		g.data_dir_root = get_test_data_dir()
	else:
		g.data_dir_root = os.path.join(g.home_dir,'.'+g.proj_name.lower())

	from .fileutil import check_or_create_dir
	check_or_create_dir(g.data_dir_root)

	from .term import init_term
	init_term()

	from .util import wrap_ripemd160
	wrap_ripemd160() # ripemd160 used by cfg_file()

	cfgfile_autoset_opts = {}

	if not (opt.skip_cfg_file or opt.bob or opt.alice or g.prog_name == 'mmgen-regtest'):
		from .cfgfile import cfg_file
		# check for changes in system template file - term must be initialized
		cfg_file('sample')
		override_globals_from_cfg_file(
			cfg_file('usr'),
			cfgfile_autoset_opts,
			env_globals,
			need_proto )

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

	if g.bob or g.alice or g.carol or g.prog_name == 'mmgen-regtest':
		g.regtest_user = 'bob' if g.bob else 'alice' if g.alice else 'carol' if g.carol else None
		g.regtest = True
		g.data_dir = os.path.join(
			g.data_dir_root,
			'regtest',
			g.coin.lower(),
			(g.regtest_user or 'none') )

	# === end global var initialization === #

	if need_proto:
		from .protocol import warn_trustlevel
		warn_trustlevel(g.coin)

	die_on_incompatible_opts(g.incompatible_opts)

	check_or_create_dir(g.data_dir) # g.data_dir is finalized, so we can create it

	# Check user-set opts without modifying them
	check_usr_opts(po.user_opts)

	# Check autoset opts, setting if unset
	for key in g.autoset_opts:
		if hasattr(opt,key):
			if getattr(opt,key) is not None:
				setattr(opt, key, get_autoset_opt(key,getattr(opt,key),src='cmdline'))
			elif key in cfgfile_autoset_opts:
				setattr(opt, key, get_autoset_opt(key,cfgfile_autoset_opts[key],src='cfgfile'))
			else:
				setattr(opt, key, g.autoset_opts[key].choices[0])

	set_auto_typeset_opts()

	if opt.verbose:
		opt.quiet = None

	if g.debug and g.prog_name != 'test.py':
		opt.verbose,opt.quiet = (True,None)

	if g.debug_opts:
		opt_postproc_debug()

	g.lock()
	opt.lock()

	# print help screen only after globals and opts initialized and locked:
	if opt.help or opt.longhelp:
		if not do_post_init:
			print_help(opt,opts_data,opt_filter) # exits

	if do_post_init:
		global opts_data_save,opt_filter_save
		opts_data_save = opts_data
		opt_filter_save = opt_filter
	else:
		delete_data(opts_data)

	return po if return_parsed else po.cmd_args

def check_usr_opts(usr_opts): # Raises an exception if any check fails

	def opt_splits(val,sep,n,desc):
		sepword = 'comma' if sep == ',' else 'colon' if sep == ':' else repr(sep)
		try:
			l = val.split(sep)
		except:
			die( 'UserOptError', f'{val!r}: invalid {desc} (not {sepword}-separated list)' )

		if len(l) != n:
			die( 'UserOptError', f'{val!r}: invalid {desc} ({n} {sepword}-separated items required)' )

	def opt_compares(val,op_str,target,desc,desc2=''):
		import operator as o
		op_f = { '<':o.lt, '<=':o.le, '>':o.gt, '>=':o.ge, '=':o.eq }[op_str]
		if not op_f(val,target):
			d2 = desc2 + ' ' if desc2 else ''
			die( 'UserOptError', f'{val}: invalid {desc} ({d2}not {op_str} {target})' )

	def opt_is_int(val,desc):
		if not is_int(val):
			die( 'UserOptError', f'{val!r}: invalid {desc} (not an integer)' )

	def opt_is_float(val,desc):
		try:
			float(val)
		except:
			die( 'UserOptError', f'{val!r}: invalid {desc} (not a floating-point number)' )

	def opt_is_in_list(val,tlist,desc):
		if val not in tlist:
			q,sep = (('',','),("'","','"))[type(tlist[0]) == str]
			die( 'UserOptError', '{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}'.format(
				v = val,
				w = desc,
				q = q,
				o = sep.join(map(str,sorted(tlist))) ))

	def opt_unrecognized(key,val,desc='value'):
		die( 'UserOptError', f'{val!r}: unrecognized {desc} for option {fmt_opt(key)!r}' )

	def opt_display(key,val='',beg='For selected',end=':\n'):
		from .util import msg_r
		msg_r('{} option {!r}{}'.format(
			beg,
			f'{fmt_opt(key)}={val}' if val else fmt_opt(key),
			end ))

	def chk_in_fmt(key,val,desc):
		from .wallet import get_wallet_data
		wd = get_wallet_data(fmt_code=val)
		if not wd:
			opt_unrecognized(key,val)
		if key == 'out_fmt':
			p = 'hidden_incog_output_params'

			if wd.type == 'incog_hidden' and not getattr(opt,p):
				die( 'UserOptError',
					'Hidden incog format output requested.  ' +
					f'You must supply a file and offset with the {fmt_opt(p)!r} option' )

			if wd.base_type == 'incog_base' and opt.old_incog_fmt:
				opt_display(key,val,beg='Selected',end=' ')
				opt_display('old_incog_fmt',beg='conflicts with',end=':\n')
				die( 'UserOptError', 'Export to old incog wallet format unsupported' )
			elif wd.type == 'brain':
				die( 'UserOptError', 'Output to brainwallet format unsupported' )

	chk_out_fmt = chk_in_fmt

	def chk_hidden_incog_input_params(key,val,desc):
		a = val.rsplit(',',1) # permit comma in filename
		if len(a) != 2:
			opt_display(key,val)
			die( 'UserOptError', 'Option requires two comma-separated arguments' )

		fn,offset = a
		opt_is_int(offset,desc)

		from .fileutil import check_infile,check_outdir,check_outfile
		if key == 'hidden_incog_input_params':
			check_infile(fn,blkdev_ok=True)
			key2 = 'in_fmt'
		else:
			try: os.stat(fn)
			except:
				b = os.path.dirname(fn)
				if b:
					check_outdir(b)
			else:
				check_outfile(fn,blkdev_ok=True)
			key2 = 'out_fmt'

		if hasattr(opt,key2):
			val2 = getattr(opt,key2)
			from .wallet import get_wallet_data
			wd = get_wallet_data('incog_hidden')
			if val2 and val2 not in wd.fmt_codes:
				die( 'UserOptError', f'Option conflict:\n  {fmt_opt(key)}, with\n  {fmt_opt(key2)}={val2}' )

	chk_hidden_incog_output_params = chk_hidden_incog_input_params

	def chk_subseeds(key,val,desc):
		from .subseed import SubSeedIdxRange
		opt_is_int(val,desc)
		opt_compares(int(val),'>=',SubSeedIdxRange.min_idx,desc)
		opt_compares(int(val),'<=',SubSeedIdxRange.max_idx,desc)

	def chk_seed_len(key,val,desc):
		from .seed import Seed
		opt_is_int(val,desc)
		opt_is_in_list(int(val),Seed.lens,desc)

	def chk_hash_preset(key,val,desc):
		from .crypto import hash_presets
		opt_is_in_list(val,list(hash_presets.keys()),desc)

	def chk_brain_params(key,val,desc):
		from .seed import Seed
		from .crypto import hash_presets
		a = val.split(',')
		if len(a) != 2:
			opt_display(key,val)
			die( 'UserOptError', 'Option requires two comma-separated arguments' )
		opt_is_int(a[0],'seed length '+desc)
		opt_is_in_list(int(a[0]),Seed.lens,'seed length '+desc)
		opt_is_in_list(a[1],list(hash_presets.keys()),'hash preset '+desc)

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
		from .util import ymsg
		ymsg(f'Adjusting transaction vsize by a factor of {float(val):1.2f}')

	def chk_daemon_id(key,val,desc):
		from .daemon import CoinDaemon
		opt_is_in_list(val,CoinDaemon.all_daemon_ids(),desc)

# TODO: move this check elsewhere
#	def chk_rbf(key,val,desc):
#		if not proto.cap('rbf'):
#			die( 'UserOptError', f'--rbf requested, but {proto.coin} does not support replace-by-fee transactions' )

#	def chk_bob(key,val,desc):
#		from .proto.btc.regtest import MMGenRegtest
#		try:
#			os.stat(os.path.join(MMGenRegtest(g.coin).d.datadir,'regtest','debug.log'))
#		except:
#			die( 'UserOptError',
#				'Regtest (Bob and Alice) mode not set up yet.  ' +
#				f"Run '{g.proj_name.lower()}-regtest setup' to initialize." )
#
#	chk_alice = chk_bob

	def chk_locktime(key,val,desc):
		opt_is_int(val,desc)
		opt_compares(int(val),'>',0,desc)

	def chk_columns(key,val,desc):
		opt_compares(int(val),'>',10,desc)

# TODO: move this check elsewhere
#	def chk_token(key,val,desc):
#		if not 'token' in proto.caps:
#			die( 'UserOptError', f'Coin {tx.coin!r} does not support the --token option' )
#		if len(val) == 40 and is_hex_str(val):
#			return
#		if len(val) > 20 or not all(s.isalnum() for s in val):
#			die( 'UserOptError', f'{val!r}: invalid parameter for --token option' )

	from .util import is_int,die,Msg

	cfuncs = { k:v for k,v in locals().items() if k.startswith('chk_') }

	for key in usr_opts:
		val = getattr(opt,key)
		desc = f'parameter for {fmt_opt(key)!r} option'

		if key in g.infile_opts:
			from .fileutil import check_infile
			check_infile(val) # file exists and is readable - dies on error
		elif key == 'outdir':
			from .fileutil import check_outdir
			check_outdir(val) # dies on error
		elif 'chk_'+key in cfuncs:
			cfuncs['chk_'+key](key,val,desc)
		elif g.debug:
			Msg(f'check_usr_opts(): No test for opt {key!r}')

def set_auto_typeset_opts():
	for key,ref_type in g.auto_typeset_opts.items():
		if hasattr(opt,key):
			val = getattr(opt,key)
			if val is not None: # typeset only if opt is set
				setattr(opt,key,ref_type(val))

def get_autoset_opt(key,val,src):

	def die_on_err(desc):
		from .util import fmt_list,die
		die(
			'UserOptError',
			'{a!r}: invalid {b} (not {c}: {d})'.format(
				a = val,
				b = {
					'cmdline': 'parameter for option --{}'.format(key.replace('_','-')),
					'cfgfile': 'value for cfg file option {!r}'.format(key)
				}[src],
				c = desc,
				d = fmt_list(data.choices) ))

	class opt_type:

		def nocase_str():
			if val.lower() in data.choices:
				return val.lower()
			else:
				die_on_err('one of')

		def nocase_pfx():
			cs = [s for s in data.choices if s.startswith(val.lower())]
			if len(cs) == 1:
				return cs[0]
			else:
				die_on_err('unique substring of')

	data = g.autoset_opts[key]

	return getattr(opt_type,data.type)()
