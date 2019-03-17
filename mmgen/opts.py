#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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

class opt(object): pass

from mmgen.globalvars import g
import mmgen.share.Opts
from mmgen.util import *

def usage(): Die(2,'USAGE: {} {}'.format(g.prog_name,usage_txt))

def die_on_incompatible_opts(incompat_list):
	for group in incompat_list:
		bad = [k for k in opt.__dict__ if opt.__dict__[k] and k in group]
		if len(bad) > 1:
			die(1,'Conflicting options: {}'.format(', '.join(map(fmt_opt,bad))))

def fmt_opt(o): return '--' + o.replace('_','-')

def _show_hash_presets():
	fs = '  {:<7} {:<6} {:<3}  {}'
	msg('Available parameters for scrypt.hash():')
	msg(fs.format('Preset','N','r','p'))
	for i in sorted(g.hash_presets.keys()):
		msg(fs.format("'{}'".format(i,*g.hash_presets[i])))
	msg('N = memory usage (power of two), p = iterations (rounds)')

def opt_preproc_debug(short_opts,long_opts,skipped_opts,uopts,args):
	d = (
		('Cmdline',            ' '.join(sys.argv)),
		('Short opts',         short_opts),
		('Long opts',          long_opts),
		('Skipped opts',       skipped_opts),
		('User-selected opts', uopts),
		('Cmd args',           args),
	)
	Msg('\n=== opts.py debug ===')
	for e in d: Msg('    {:<20}: {}'.format(*e))

def opt_postproc_debug():
	a = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) != None]
	b = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) == None]
	Msg('    Opts after processing:')
	for k in a:
		v = getattr(opt,k)
		Msg('        {:18}: {:<6} [{}]'.format(k,v,type(v).__name__))
	Msg("    Opts set to 'None':")
	Msg('        {}\n'.format('\n        '.join(b)))
	Msg('    Global vars:')
	for e in [d for d in dir(g) if d[:2] != '__']:
		Msg('        {:<20}: {}'.format(e, getattr(g,e)))
	Msg('\n=== end opts.py debug ===\n')

def opt_postproc_initializations():
	from mmgen.term import set_terminal_vars
	set_terminal_vars()

	from mmgen.color import init_color
	init_color(enable_color=g.color,num_colors=('auto',256)[bool(g.force_256_color)])

	if g.platform == 'win': start_mscolor()

	g.coin = g.coin.upper() # allow user to use lowercase
	g.dcoin = g.coin

def set_data_dir_root():
	g.data_dir_root = os.path.normpath(os.path.expanduser(opt.data_dir)) if opt.data_dir else \
			os.path.join(g.home_dir,'.'+g.proj_name.lower())

	# mainnet and testnet share cfg file, as with Core
	g.cfg_file = os.path.join(g.data_dir_root,'{}.cfg'.format(g.proj_name.lower()))

def get_cfg_template_data():
	# https://wiki.debian.org/Python:
	#   Debian (Ubuntu) sys.prefix is '/usr' rather than '/usr/local, so add 'local'
	# TODO - test for Windows
	# This must match the configuration in setup.py
	cfg_template = os.path.join(*([sys.prefix]
				+ (['share'],['local','share'])[g.platform=='linux']
				+ [g.proj_name.lower(),os.path.basename(g.cfg_file)]))
	try:
		return open(cfg_template).read()
	except:
		msg("WARNING: configuration template not found at '{}'".format(cfg_template))
		return ''

def get_data_from_cfg_file():
	from mmgen.util import msg,die,check_or_create_dir
	check_or_create_dir(g.data_dir_root) # dies on error
	template_data = get_cfg_template_data()
	data = {}

	def copy_template_data(fn):
		try:
			open(fn,'wb').write(template_data.encode())
			os.chmod(fn,0o600)
		except:
			die(2,"ERROR: unable to write to datadir '{}'".format(g.data_dir))

	for k,suf in (('cfg',''),('sample','.sample')):
		try:
			data[k] = open(g.cfg_file+suf,'rb').read().decode()
		except:
			if template_data:
				copy_template_data(g.cfg_file+suf)
				data[k] = template_data
			else:
				data[k] = ''

	if template_data and data['sample'] != template_data:
		g.cfg_options_changed = True
		copy_template_data(g.cfg_file+'.sample')

	return data['cfg']

def override_from_cfg_file(cfg_data):
	from mmgen.util import die,strip_comments,set_for_type
	import re
	from mmgen.protocol import CoinProtocol
	for n,l in enumerate(cfg_data.splitlines(),1): # DOS-safe
		l = strip_comments(l)
		if l == '': continue
		m = re.match(r'(\w+)\s+(\S+)$',l)
		if not m: die(2,"Parse error in file '{}', line {}".format(g.cfg_file,n))
		name,val = m.groups()
		if name in g.cfg_file_opts:
			pfx,cfg_var = name.split('_',1)
			if pfx in CoinProtocol.coins:
				tn = False
				cv1,cv2 = cfg_var.split('_',1)
				if cv1 in ('mainnet','testnet'):
					tn,cfg_var = (cv1 == 'testnet'),cv2
				cls,attr = CoinProtocol(pfx,tn),cfg_var
			else:
				cls,attr = g,name
			setattr(cls,attr,set_for_type(val,getattr(cls,attr),attr,src=g.cfg_file))
		else:
			die(2,"'{}': unrecognized option in '{}'".format(name,g.cfg_file))

def override_from_env():
	from mmgen.util import set_for_type
	for name in g.env_opts:
		if name == 'MMGEN_DEBUG_ALL': continue
		disable = name[:14] == 'MMGEN_DISABLE_'
		val = os.getenv(name) # os.getenv() returns None if env var is unset
		if val: # exclude empty string values; string value of '0' or 'false' sets variable to False
			gname = name[(6,14)[disable]:].lower()
			setattr(g,gname,set_for_type(val,getattr(g,gname),name,disable))

def warn_altcoins(trust_level):
	if trust_level == None: return
	tl = (red('COMPLETELY UNTESTED'),red('LOW'),yellow('MEDIUM'),green('HIGH'))
	m = """
Support for coin '{}' is EXPERIMENTAL.  The {pn} project assumes no
responsibility for any loss of funds you may incur.
This coin's {pn} testing status: {}
Are you sure you want to continue?
""".strip().format(g.coin,tl[trust_level],pn=g.proj_name)
	if g.test_suite:
		msg(m); return
	if not keypress_confirm(m,default_yes=True):
		sys.exit(0)

def get_common_opts_data():
	# most, but not all, of these set the corresponding global var
	from mmgen.protocol import CoinProtocol
	return """
--, --accept-defaults     Accept defaults at all prompts
--, --coin=c              Choose coin unit. Default: {cu_dfl}. Options: {cu_all}
--, --token=t             Specify an ERC20 token by address or symbol
--, --color=0|1           Disable or enable color output
--, --force-256-color     Force 256-color output when color is enabled
--, --daemon-data-dir=d   Specify coin daemon data directory location 'd'
--, --data-dir=d          Specify {pnm} data directory location 'd'
--, --no-license          Suppress the GPL license prompt
--, --rpc-host=h          Communicate with {dn} running on host 'h'
--, --rpc-port=p          Communicate with {dn} listening on port 'p'
--, --rpc-user=user       Override 'rpcuser' in {pn}.conf
--, --rpc-password=pass   Override 'rpcpassword' in {pn}.conf
--, --regtest=0|1         Disable or enable regtest mode
--, --testnet=0|1         Disable or enable testnet
--, --skip-cfg-file       Skip reading the configuration file
--, --version             Print version information and exit
--, --bob                 Switch to user "Bob" in MMGen regtest setup
--, --alice               Switch to user "Alice" in MMGen regtest setup
	""".format( pnm=g.proj_name,pn=g.proto.name,dn=g.proto.daemon_name,
				cu_dfl=g.coin,
				cu_all=' '.join(CoinProtocol.coins))

def init(opts_f,add_opts=[],opt_filter=None,parse_only=False):

	from mmgen.protocol import CoinProtocol,BitcoinProtocol,init_genonly_altcoins
	g.proto = BitcoinProtocol # this must be initialized to something before opts_f is called

	opts_data = opts_f()
	opts_data['long_options'] = get_common_opts_data()

	uopts,args,short_opts,long_opts,skipped_opts,do_help = \
		mmgen.share.Opts.parse_opts(sys.argv,opts_data,opt_filter=opt_filter,skip_help=True)

	if parse_only:
		return uopts,args,short_opts,long_opts,skipped_opts,do_help

	if g.debug_opts: opt_preproc_debug(short_opts,long_opts,skipped_opts,uopts,args)

	# Save this for usage()
	global usage_txt
	usage_txt = opts_data['usage']

	# Transfer uopts into opt, setting program's opts + required opts to None if not set by user
	for o in tuple([s.rstrip('=') for s in long_opts] + add_opts + skipped_opts) + \
				g.required_opts + g.common_opts:
		setattr(opt,o,uopts[o] if o in uopts else None)

	if opt.version: Die(0,"""
    {pn} version {g.version}
    Part of the {g.proj_name} suite, an online/offline cryptocoin wallet for the command line.
    Copyright (C) {g.Cdates} {g.author} {g.email}
	""".format(g=g,pn=g.prog_name.upper()).lstrip('\n').rstrip())


	if os.getenv('MMGEN_DEBUG_ALL'):
		for name in g.env_opts:
			if name[:11] == 'MMGEN_DEBUG':
				os.environ[name] = '1'

	# === Interaction with global vars begins here ===

	# NB: user opt --data-dir is actually g.data_dir_root
	# cfg file is in g.data_dir_root, wallet and other data are in g.data_dir
	# We must set g.data_dir_root and g.cfg_file from cmdline before processing cfg file
	set_data_dir_root()
	if not opt.skip_cfg_file:
		override_from_cfg_file(get_data_from_cfg_file())
	override_from_env()

	# User opt sets global var - do these here, before opt is set from g.global_sets_opt
	for k in g.common_opts:
		val = getattr(opt,k)
		if val != None: setattr(g,k,set_for_type(val,getattr(g,k),'--'+k))

	if g.regtest: g.testnet = True # These are equivalent for now

	altcoin_trust_level = init_genonly_altcoins(opt.coin)

	# g.testnet is set, so we can set g.proto
	g.proto = CoinProtocol(g.coin,g.testnet)

	# global sets proto
	if g.daemon_data_dir: g.proto.daemon_data_dir = g.daemon_data_dir

#	g.proto is set, so we can set g.data_dir
	g.data_dir = os.path.normpath(os.path.join(g.data_dir_root,g.proto.data_subdir))

	# If user opt is set, convert its type based on value in mmgen.globalvars (g)
	# If unset, set it to default value in mmgen.globalvars (g)
	setattr(opt,'set_by_user',[])
	for k in g.global_sets_opt:
		if k in opt.__dict__ and getattr(opt,k) != None:
			setattr(opt,k,set_for_type(getattr(opt,k),getattr(g,k),'--'+k))
			opt.set_by_user.append(k)
		else:
			setattr(opt,k,g.__dict__[k])

	if opt.show_hash_presets:
		_show_hash_presets()
		sys.exit(0)

	if opt.verbose: opt.quiet = None

	die_on_incompatible_opts(g.incompatible_opts)

	opt_postproc_initializations()

	if do_help: # print help screen only after global vars are initialized
		opts_data = opts_f()
		opts_data['long_options'] = get_common_opts_data()
		if g.debug_utf8:
			for k in opts_data:
				if type(opts_data[k]) == str:
					opts_data[k] += '-α'
		mmgen.share.Opts.parse_opts(sys.argv,opts_data,opt_filter=opt_filter) # exits

	if g.bob or g.alice:
		g.testnet = True
		g.regtest = True
		g.proto = CoinProtocol(g.coin,g.testnet)
		g.data_dir = os.path.join(g.data_dir_root,'regtest',g.coin.lower(),('alice','bob')[g.bob])
		from . import regtest as rt
		g.rpc_host = 'localhost'
		g.rpc_port = rt.rpc_port
		g.rpc_user = rt.rpc_user
		g.rpc_password = rt.rpc_password

	check_or_create_dir(g.data_dir) # g.data_dir is finalized, so now we can do this

	if g.regtest and hasattr(g.proto,'bech32_hrp_rt'):
		g.proto.bech32_hrp = g.proto.bech32_hrp_rt

	# Check user-set opts without modifying them
	if not check_opts(uopts):
		die(1,'Options checking failed')

	if hasattr(g,'cfg_options_changed'):
		ymsg("Warning: config file options have changed! See '{}' for details".format(g.cfg_file+'.sample'))
		my_raw_input('Hit ENTER to continue: ')

	if g.debug and g.prog_name != 'test.py':
		opt.verbose,opt.quiet = True,None
	if g.debug_opts: opt_postproc_debug()

	# We don't need this data anymore
	del mmgen.share.Opts
	del opts_f
	for k in ('prog_name','desc','usage','options','notes'):
		if k in opts_data: del opts_data[k]

	g.altcoin_data_dir = os.path.join(g.data_dir_root,'altcoins')
	warn_altcoins(altcoin_trust_level)

	return args

def opt_is_tx_fee(val,desc):
	from mmgen.tx import MMGenTX
	ret = MMGenTX().process_fee_spec(val,224,on_fail='return')
	# Non-standard startgas: disable fee checking
	if hasattr(opt,'contract_data') and opt.contract_data: ret = None
	if hasattr(opt,'tx_gas') and opt.tx_gas:               ret = None
	if ret == False:
		msg("'{}': invalid {}\n(not a {} amount or {} specification)".format(
				val,desc,g.coin.upper(),MMGenTX().rel_fee_desc))
	elif ret != None and ret > g.proto.max_tx_fee:
		msg("'{}': invalid {}\n({} > max_tx_fee ({} {}))".format(
				val,desc,ret.fmt(fs='1.1'),g.proto.max_tx_fee,g.coin.upper()))
	else:
		return True
	return False

def check_opts(usr_opts):       # Returns false if any check fails

	def opt_splits(val,sep,n,desc):
		sepword = 'comma' if sep == ',' else 'colon' if sep == ':' else "'{}'".format(sep)
		try: l = val.split(sep)
		except:
			msg("'{}': invalid {} (not {}-separated list)".format(val,desc,sepword))
			return False

		if len(l) == n: return True
		else:
			msg("'{}': invalid {} ({} {}-separated items required)".format(val,desc,n,sepword))
			return False

	def opt_compares(val,op_str,target,desc,what=''):
		import operator as o
		op_f = { '<':o.lt, '<=':o.le, '>':o.gt, '>=':o.ge, '=':o.eq }[op_str]
		if what: what += ' '
		if not op_f(val,target):
			msg('{}: invalid {} ({}not {} {})'.format(val,desc,what,op_str,target))
			return False
		return True

	def opt_is_int(val,desc):
		try: int(val)
		except:
			msg("'{}': invalid {} (not an integer)".format(val,desc))
			return False
		return True

	def opt_is_float(val,desc):
		try: float(val)
		except:
			msg("'{}': invalid {} (not a floating-point number)".format(val,desc))
			return False
		return True

	def opt_is_in_list(val,lst,desc):
		if val not in lst:
			q,sep = (('',','),("'","','"))[type(lst[0]) == str]
			fs = '{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}'
			msg(fs.format(v=val,w=desc,q=q,o=sep.join(map(str,sorted(lst)))))
			return False
		return True

	def opt_unrecognized(key,val,desc):
		msg("'{}': unrecognized {} for option '{}'".format(val,desc,fmt_opt(key)))
		return False

	def opt_display(key,val='',beg='For selected',end=':\n'):
		s = '{}={}'.format(fmt_opt(key),val) if val else fmt_opt(key)
		msg_r("{} option '{}'{}".format(beg,s,end))

	global opt
	for key,val in [(k,getattr(opt,k)) for k in usr_opts]:

		desc = "parameter for '{}' option".format(fmt_opt(key))

		from mmgen.util import check_infile,check_outfile,check_outdir
		# Check for file existence and readability
		if key in ('keys_from_file','mmgen_keys_from_file',
				'passwd_file','keysforaddrs','comment_file'):
			check_infile(val)  # exits on error
			continue

		if key == 'outdir':
			check_outdir(val)  # exits on error
# 		# NEW
		elif key in ('in_fmt','out_fmt'):
			from mmgen.seed import SeedSource,IncogWallet,Brainwallet,IncogWalletHidden
			sstype = SeedSource.fmt_code_to_type(val)
			if not sstype:
				return opt_unrecognized(key,val,'format code')
			if key == 'out_fmt':
				p = 'hidden_incog_output_params'
				if sstype == IncogWalletHidden and not getattr(opt,p):
					m1 = 'Hidden incog format output requested.  '
					m2 = "You must supply a file and offset with the '{}' option"
					die(1,m1+m2.format(fmt_opt(p)))
				if issubclass(sstype,IncogWallet) and opt.old_incog_fmt:
					opt_display(key,val,beg='Selected',end=' ')
					opt_display('old_incog_fmt',beg='conflicts with',end=':\n')
					die(1,'Export to old incog wallet format unsupported')
				elif issubclass(sstype,Brainwallet):
					die(1,'Output to brainwallet format unsupported')
		elif key in ('hidden_incog_input_params','hidden_incog_output_params'):
			a = val.split(',')
			if len(a) < 2:
				opt_display(key,val)
				msg('Option requires two comma-separated arguments')
				return False
			fn,ofs = ','.join(a[:-1]),a[-1] # permit comma in filename
			if not opt_is_int(ofs,desc): return False
			if key == 'hidden_incog_input_params':
				check_infile(fn,blkdev_ok=True)
				key2 = 'in_fmt'
			else:
				try: os.stat(fn)
				except:
					b = os.path.dirname(fn)
					if b: check_outdir(b)
				else: check_outfile(fn,blkdev_ok=True)
				key2 = 'out_fmt'
			if hasattr(opt,key2):
				val2 = getattr(opt,key2)
				from mmgen.seed import IncogWalletHidden
				if val2 and val2 not in IncogWalletHidden.fmt_codes:
					fs = 'Option conflict:\n  {}, with\n  {}={}'
					die(1,fs.format(fmt_opt(key),fmt_opt(key2),val2))
		elif key == 'seed_len':
			if not opt_is_int(val,desc): return False
			if not opt_is_in_list(int(val),g.seed_lens,desc): return False
		elif key == 'hash_preset':
			if not opt_is_in_list(val,list(g.hash_presets.keys()),desc): return False
		elif key == 'brain_params':
			a = val.split(',')
			if len(a) != 2:
				opt_display(key,val)
				msg('Option requires two comma-separated arguments')
				return False
			d = 'seed length ' + desc
			if not opt_is_int(a[0],d): return False
			if not opt_is_in_list(int(a[0]),g.seed_lens,d): return False
			d = 'hash preset ' + desc
			if not opt_is_in_list(a[1],list(g.hash_presets.keys()),d): return False
		elif key == 'usr_randchars':
			if val == 0: continue
			if not opt_is_int(val,desc): return False
			if not opt_compares(val,'>=',g.min_urandchars,desc): return False
			if not opt_compares(val,'<=',g.max_urandchars,desc): return False
		elif key == 'tx_fee':
			if not opt_is_tx_fee(val,desc): return False
		elif key == 'tx_confs':
			if not opt_is_int(val,desc): return False
			if not opt_compares(val,'>=',1,desc): return False
		elif key == 'vsize_adj':
			if not opt_is_float(val,desc): return False
			ymsg('Adjusting transaction vsize by a factor of {:1.2f}'.format(float(val)))
		elif key == 'key_generator':
			if not opt_compares(val,'<=',len(g.key_generators),desc): return False
			if not opt_compares(val,'>',0,desc): return False
		elif key == 'coin':
			from mmgen.protocol import CoinProtocol
			if not opt_is_in_list(val.lower(),list(CoinProtocol.coins.keys()),'coin'): return False
		elif key == 'rbf':
			if not g.proto.cap('rbf'):
				msg('--rbf requested, but {} does not support replace-by-fee transactions'.format(g.coin))
				return False
		elif key in ('bob','alice'):
			from mmgen.regtest import daemon_dir
			m = "Regtest (Bob and Alice) mode not set up yet.  Run '{}-regtest setup' to initialize."
			try: os.stat(daemon_dir)
			except: die(1,m.format(g.proj_name.lower()))
		elif key == 'locktime':
			if not opt_is_int(val,desc): return False
			if not opt_compares(int(val),'>',0,desc): return False
		elif key == 'token':
			if not 'token' in g.proto.caps:
				msg("Coin '{}' does not support the --token option".format(g.coin))
				return False
			elif len(val) == 40 and is_hex_str(val):
				pass
			elif len(val) > 20 or not all(s.isalnum() for s in val):
				msg("u'{}: invalid parameter for --token option".format(val))
				return False
		elif key == 'contract_data':
			check_infile(val)
		else:
			if g.debug: Msg("check_opts(): No test for opt '{}'".format(key))

	return True
