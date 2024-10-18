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
cfg: Configuration classes for the MMGen suite
"""

import sys, os
from collections import namedtuple
from .base_obj import Lockable

def die(*args, **kwargs):
	from .util import die
	die(*args, **kwargs)

def die2(exit_val, s):
	sys.stderr.write(s+'\n')
	sys.exit(exit_val)

class GlobalConstants(Lockable):
	"""
	These values are non-runtime-configurable.  They’re constant for a given machine,
	user, executable and MMGen release.
	"""
	_autolock = True

	proj_name          = 'MMGen'
	proj_id            = 'mmgen'
	proj_url           = 'https://github.com/mmgen/mmgen-wallet'
	author             = 'The MMGen Project'
	email              = '<mmgen@tuta.io>'
	Cdates             = '2013-2024'
	dfl_hash_preset    = '3'
	passwd_max_tries   = 5
	min_screen_width   = 80
	min_time_precision = 18

	# must match CoinProtocol.coins
	core_coins = ('btc', 'bch', 'ltc', 'eth', 'etc', 'zec', 'xmr')
	rpc_coins = ('btc', 'bch', 'ltc', 'eth', 'etc', 'xmr')
	btc_fork_rpc_coins = ('btc', 'bch', 'ltc')
	eth_fork_coins = ('eth', 'etc')

	_cc = namedtuple('cmd_cap', ['proto', 'rpc', 'coin', 'caps', 'platforms'])
	cmd_caps_data = {
		'addrgen':      _cc(True,  False, None,  [],      'lmw'),
		'addrimport':   _cc(True,  True,  'R',   ['tw'],  'lmw'),
		'autosign':     _cc(True,  True,  'r',   ['rpc'], 'lm'),
		'keygen':       _cc(True,  False, None,  [],      'lmw'),
		'msg':          _cc(True,  True,  'R',   ['msg'], 'lmw'),
		'passchg':      _cc(False, False, None,  [],      'lmw'),
		'passgen':      _cc(False, False, None,  [],      'lmw'),
		'regtest':      _cc(True,  True,  'b',   ['tw'],  'lmw'),
		'seedjoin':     _cc(False, False, None,  [],      'lmw'),
		'seedsplit':    _cc(False, False, None,  [],      'lmw'),
		'subwalletgen': _cc(False, False, None,  [],      'lmw'),
		'tool':         _cc(True,  True,  None,  [],      'lmw'),
		'txbump':       _cc(True,  True,  'R',   ['tw'],  'lmw'),
		'txcreate':     _cc(True,  True,  'R',   ['tw'],  'lmw'),
		'txdo':         _cc(True,  True,  'R',   ['tw'],  'lmw'),
		'txsend':       _cc(True,  True,  'R',   ['tw'],  'lmw'),
		'txsign':       _cc(True,  True,  'R',   ['tw'],  'lmw'),
		'walletchk':    _cc(False, False, None,  [],      'lmw'),
		'walletconv':   _cc(False, False, None,  [],      'lmw'),
		'walletgen':    _cc(False, False, None,  [],      'lmw'),
		'xmrwallet':    _cc(True,  True,  'xmr', ['rpc'], 'lmw'),
	}

	prog_name = os.path.basename(sys.argv[0])
	prog_id = prog_name.removeprefix(f'{proj_id}-')
	cmd_caps = cmd_caps_data.get(prog_id)

	if sys.platform not in ('linux', 'win32', 'darwin'):
		die2(1, f'{sys.platform!r}: platform not supported by {proj_name}')

	if os.getenv('HOME'):   # Linux, MSYS2, or macOS
		home_dir = os.getenv('HOME')
	elif sys.platform == 'win32': # Windows without MSYS2 - not supported
		die2(1, f'$HOME not set!  {proj_name} for Windows must be run in MSYS2 environment')
	else:
		die2(2, '$HOME is not set!  Unable to determine home directory')

	def get_mmgen_data_file(self, filename, package='mmgen'):
		"""
		this is an expensive import, so do only when required
		"""
		# Resource will be unpacked and then cleaned up if necessary, see:
		#    https://docs.python.org/3/library/importlib.html:
		#        Note: This module provides functionality similar to pkg_resources Basic
		#        Resource Access without the performance overhead of that package.
		#    https://importlib-resources.readthedocs.io/en/latest/migration.html
		#    https://setuptools.readthedocs.io/en/latest/pkg_resources.html

		# TODO: remove try..except (workaround for Python 3.9 pylint bug)
		try:
			from importlib.resources import files # Python 3.9 and above
		except ImportError:
			from importlib_resources import files
		return files(package).joinpath('data', filename).read_text()

	@property
	def version(self):
		return self.get_mmgen_data_file(
				filename = 'version',
				package  = 'mmgen_node_tools' if self.prog_name.startswith('mmnode-') else 'mmgen'
			).strip()

	@property
	def release_date(self):
		return self.get_mmgen_data_file(filename='release_date').strip()

gc = GlobalConstants()

class GlobalVars:
	"""
	These are used only by the test suite to redirect msg() and friends to /dev/null
	"""
	stdout = sys.stdout
	stderr = sys.stderr

gv = GlobalVars()

class Config(Lockable):
	"""
	These values are configurable - RHS values are defaults
	Globals are overridden with the following precedence:
	  1 - command line
	  2 - environmental vars
	  3 - config file
	"""
	_autolock = False
	_set_ok = ('usr_randchars', '_proto')
	_reset_ok = ('accept_defaults',)
	_delete_ok = ('_opts',)
	_use_class_attr = True
	_default_to_none = True

	# general
	coin        = 'BTC'
	token       = ''
	outdir      = ''
	passwd_file = ''
	network     = 'mainnet'
	testnet     = False
	regtest     = False

	# verbosity / prompting behavior
	quiet           = False
	verbose         = False
	yes             = False
	accept_defaults = False
	no_license      = False

	# limits
	http_timeout       = 60
	usr_randchars      = 30
	fee_adjust         = 1.0
	fee_estimate_confs = 3
	minconf            = 1
	max_tx_file_size   = 100000
	max_input_size     = 1024 * 1024
	min_urandchars     = 10
	max_urandchars     = 80
	macos_autosign_ramdisk_size = 10 # see MacOSRamDisk

	# debug
	debug                = False
	debug_daemon         = False
	debug_opts           = False
	debug_rpc            = False
	debug_addrlist       = False
	debug_subseed        = False
	debug_tw             = False
	devtools             = False
	traceback            = False

	# rpc:
	rpc_host              = ''
	rpc_port              = 0
	rpc_user              = ''
	rpc_password          = ''
	aiohttp_rpc_queue_len = 16
	cached_balances       = False

	# daemons
	daemon_data_dir       = '' # set by user
	daemon_id             = ''
	blacklisted_daemons   = ''
	ignore_daemon_version = False

	# display:
	test_suite_enable_color = False # placeholder
	force_256_color = False
	scroll          = False
	pager           = False
	columns         = 0
	color = bool(
		(sys.stdout.isatty() and not os.getenv('MMGEN_TEST_SUITE_PEXPECT')) or
		os.getenv('MMGEN_TEST_SUITE_ENABLE_COLOR')
	)

	# miscellaneous features:
	use_internal_keccak_module     = False
	force_standalone_scrypt_module = False
	enable_erigon                  = False
	autochg_ignore_labels          = False

	# regtest:
	bob          = False
	alice        = False
	carol        = False
	regtest_user = ''

	# altcoin:
	cashaddr = True

	# Monero:
	monero_wallet_rpc_user     = 'monero'
	monero_wallet_rpc_password = ''
	priority                   = 0

	# test suite:
	bogus_send               = False
	bogus_unspent_data       = ''
	debug_utf8               = False
	exec_wrapper             = False
	ignore_test_py_exception = False
	test_suite               = False
	test_suite_autosign_led_simulate = False
	test_suite_autosign_threaded = False
	test_suite_xmr_autosign  = False
	test_suite_cfgtest       = False
	test_suite_deterministic = False
	test_suite_pexpect       = False
	test_suite_popen_spawn   = False
	test_suite_root_pfx      = ''
	hold_protect_disable     = False
	no_daemon_autostart      = False
	names                    = False
	no_timings               = False
	exit_after               = ''
	resuming                 = False
	skipping_deps            = False
	test_datadir             = os.path.join('test', 'data_dir' + ('', '-α')[bool(os.getenv('MMGEN_DEBUG_UTF8'))])

	mnemonic_entry_modes = {}

	# external use:
	_opts  = None
	_proto = None

	# internal use:
	_use_cfg_file           = False
	_use_env                = False

	_forbidden_opts = (
		'data_dir_root',
	)

	_incompatible_opts = (
		('help', 'longhelp'),
		('bob', 'alice', 'carol'),
		('label', 'keep_label'),
		('tx_id', 'info'),
		('tx_id', 'terse_info'),
		('autosign', 'outdir'),
	)

	_cfg_file_opts = (
		'autochg_ignore_labels',
		'color',
		'daemon_data_dir',
		'debug',
		'fee_adjust',
		'force_256_color',
		'hash_preset',
		'http_timeout',
		'macos_autosign_ramdisk_size',
		'max_input_size',
		'max_tx_file_size',
		'mnemonic_entry_modes',
		'monero_wallet_rpc_password',
		'monero_wallet_rpc_user',
		'no_license',
		'quiet',
		'regtest',
		'rpc_host',
		'rpc_password',
		'rpc_port',
		'rpc_user',
		'scroll',
		'subseeds',
		'testnet',
		'usr_randchars',
		'bch_cashaddr',
		'bch_max_tx_fee',
		'btc_max_tx_fee',
		'eth_max_tx_fee',
		'ltc_max_tx_fee',
		'bch_ignore_daemon_version',
		'btc_ignore_daemon_version',
		'etc_ignore_daemon_version',
		'eth_ignore_daemon_version',
		'ltc_ignore_daemon_version',
		'xmr_ignore_daemon_version',
		'eth_mainnet_chain_names',
		'eth_testnet_chain_names')

	# Supported environmental vars
	# The corresponding attributes (lowercase, without 'mmgen_') must exist in the class.
	# The 'MMGEN_DISABLE_' prefix sets the corresponding attribute to False.
	_env_opts = (
		'MMGEN_DEBUG_ALL', # special: there is no `debug_all` attribute

		'MMGEN_COLUMNS',
		'MMGEN_TEST_SUITE',
		'MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE',
		'MMGEN_TEST_SUITE_AUTOSIGN_THREADED',
		'MMGEN_TEST_SUITE_XMR_AUTOSIGN',
		'MMGEN_TEST_SUITE_CFGTEST',
		'MMGEN_TEST_SUITE_DETERMINISTIC',
		'MMGEN_TEST_SUITE_ENABLE_COLOR',
		'MMGEN_TEST_SUITE_PEXPECT',
		'MMGEN_TEST_SUITE_POPEN_SPAWN',
		'MMGEN_TEST_SUITE_ROOT_PFX',
		'MMGEN_TRACEBACK',
		'MMGEN_BLACKLIST_DAEMONS',
		'MMGEN_BOGUS_SEND',
		'MMGEN_BOGUS_UNSPENT_DATA',
		'MMGEN_DEBUG',
		'MMGEN_DEBUG_DAEMON',
		'MMGEN_DEBUG_OPTS',
		'MMGEN_DEBUG_RPC',
		'MMGEN_DEBUG_ADDRLIST',
		'MMGEN_DEBUG_TW',
		'MMGEN_DEBUG_UTF8',
		'MMGEN_DEBUG_SUBSEED',
		'MMGEN_DEVTOOLS',
		'MMGEN_FORCE_256_COLOR',
		'MMGEN_HOLD_PROTECT_DISABLE',
		'MMGEN_HTTP_TIMEOUT',
		'MMGEN_QUIET',
		'MMGEN_NO_LICENSE',
		'MMGEN_RPC_HOST',
		'MMGEN_RPC_FAIL_ON_COMMAND',
		'MMGEN_TESTNET',
		'MMGEN_REGTEST',
		'MMGEN_EXEC_WRAPPER',
		'MMGEN_IGNORE_TEST_PY_EXCEPTION',
		'MMGEN_RPC_BACKEND',
		'MMGEN_IGNORE_DAEMON_VERSION',
		'MMGEN_USE_STANDALONE_SCRYPT_MODULE',
		'MMGEN_ENABLE_ERIGON',
		'MMGEN_DISABLE_COLOR',
	)
	_infile_opts = (
		'keys_from_file',
		'mmgen_keys_from_file',
		'passwd_file',
		'keysforaddrs',
		'comment_file',
		'contract_data',
	)
	# Auto-typechecked and auto-set opts - first value in list is the default
	_ov = namedtuple('autoset_opt_info', ['type', 'choices'])
	_autoset_opts = {
		'fee_estimate_mode': _ov('nocase_pfx', ['conservative', 'economical']),
		'rpc_backend':       _ov('nocase_pfx', ['auto', 'httplib', 'curl', 'aiohttp', 'requests']),
	}

	_auto_typeset_opts = {
		'seed_len': int,
		'subseeds': int,
		'vsize_adj': float,
	}

	# test suite:
	err_disp_timeout   = 0.7
	short_disp_timeout = 0.3
	stdin_tty          = sys.stdin.isatty()

	if os.getenv('MMGEN_TEST_SUITE'):
		min_urandchars = 3
		err_disp_timeout = 0.1
		short_disp_timeout = 0.1
		if os.getenv('MMGEN_TEST_SUITE_POPEN_SPAWN'):
			stdin_tty = True
		if gc.prog_name == 'modtest.py':
			_set_ok += ('debug_subseed',)
			_reset_ok += ('force_standalone_scrypt_module',)

	if os.getenv('MMGEN_DEBUG_ALL'):
		for name in _env_opts:
			if name[:11] == 'MMGEN_DEBUG':
				os.environ[name] = '1'

	@property
	def data_dir_root(self):
		"""
		location of mmgen.cfg
		"""
		if not hasattr(self, '_data_dir_root'):
			if self._data_dir_root_override:
				self._data_dir_root = os.path.normpath(os.path.abspath(self._data_dir_root_override))
			elif self.test_suite:
				self._data_dir_root = self.test_datadir
			else:
				self._data_dir_root = os.path.join(gc.home_dir, '.'+gc.proj_name.lower())
		return self._data_dir_root

	@property
	def data_dir(self):
		"""
		location of wallet and other data - same as data_dir_root for mainnet
		"""
		if not hasattr(self, '_data_dir'):
			self._data_dir = os.path.normpath(os.path.join(*{
				'regtest': (self.data_dir_root, 'regtest', (self.regtest_user or 'none')),
				'testnet': (self.data_dir_root, 'testnet'),
				'mainnet': (self.data_dir_root,),
			}[self.network]))
		return self._data_dir

	def __init__(
			self,
			cfg          = None,
			opts_data    = None,
			init_opts    = None,
			opt_filter   = None,
			parse_only   = False,
			parsed_opts  = None,
			need_proto   = True,
			need_amt     = True,
			caller_post_init = False,
			process_opts = False):

		# Step 1: get user-supplied configuration data from
		#           a) command line, or
		#           b) first argument to constructor;
		#         save to self._uopts:
		self._cloned = {}
		if opts_data or parsed_opts or process_opts:
			assert cfg is None, (
				'Config(): ‘cfg’ cannot be used simultaneously with ' +
				'‘opts_data’, ‘parsed_opts’ or ‘process_opts’')
			from .opts import UserOpts
			UserOpts(
				cfg          = self,
				opts_data    = opts_data,
				init_opts    = init_opts,
				opt_filter   = opt_filter,
				parsed_opts  = parsed_opts,
				need_proto   = need_proto)
			self._uopt_desc = 'command-line option'
		else:
			if cfg is None:
				self._uopts = {}
			else:
				if '_clone' in cfg:
					assert isinstance(cfg['_clone'], Config)
					self._cloned = cfg['_clone'].__dict__
					for k, v in self._cloned.items():
						if not k.startswith('_'):
							setattr(self, k, v)
					del cfg['_clone']
				self._uopts = cfg
			self._uopt_desc = 'configuration option'

		self._data_dir_root_override = self._cloned.pop(
			'_data_dir_root_override',
			self._uopts.pop('data_dir', None))

		if parse_only and not any(k in self._uopts for k in ['help', 'longhelp']):
			return

		# Step 2: set cfg from user-supplied data, skipping auto opts; set type from corresponding
		#         class attribute, if it exists:
		auto_opts = tuple(self._autoset_opts) + tuple(self._auto_typeset_opts)
		for key, val in self._uopts.items():
			assert key.isascii() and key.isidentifier() and key[0] != '_', (
				f'{key!r}: malformed configuration option')
			assert key not in self._forbidden_opts, (
				f'{key!r}: forbidden configuration option')
			if key not in auto_opts:
				if hasattr(type(self), key):
					setattr(
						self,
						key,
						getattr(type(self), key) if val is None else
							conv_type(key, val, getattr(type(self), key), self._uopt_desc))
				elif val is None:
					if hasattr(self, key):
						delattr(self, key)
				else:
					setattr(self, key, val)

		# Step 3: set cfg from environment, skipping already-set opts; save names set from environment:
		self._envopts = tuple(self._set_cfg_from_env()) if self._use_env else ()

		from .term import init_term
		init_term(self) # requires ‘hold_protect_disable’ (set from env)

		from .fileutil import check_or_create_dir
		check_or_create_dir(self.data_dir_root)

		from .util import wrap_ripemd160
		wrap_ripemd160() # ripemd160 required by mmgen_cfg_file() in _set_cfg_from_cfg_file()

		# Step 4: set cfg from cfgfile, skipping already-set opts and auto opts; save set opts and auto
		#         opts to be set:
		# requires ‘data_dir_root’, ‘test_suite_cfgtest’
		self._cfgfile_opts = self._set_cfg_from_cfg_file(self._envopts, need_proto)

		# Step 5: set autoset opts from user-supplied data, cfgfile data, or default values, in that order:
		self._set_autoset_opts(self._cfgfile_opts.autoset)

		# Step 6: set auto typeset opts from user-supplied data or cfgfile data, in that order:
		self._set_auto_typeset_opts(self._cfgfile_opts.auto_typeset)

		if self.regtest or self.bob or self.alice or self.carol or gc.prog_name == f'{gc.proj_id}-regtest':
			self.network = 'regtest'
			self.regtest_user = 'bob' if self.bob else 'alice' if self.alice else 'carol' if self.carol else None
		else:
			self.network = 'testnet' if self.testnet else 'mainnet'

		self.coin = self.coin.upper()
		self.token = self.token.upper() if self.token else None

		# self.color is finalized, so initialize color:
		if self.color: # MMGEN_DISABLE_COLOR sets this to False
			from .color import init_color
			init_color(num_colors=256 if self.force_256_color else 'auto')

		self._die_on_incompatible_opts()

		check_or_create_dir(self.data_dir)

		if self.debug and gc.prog_name != 'cmdtest.py':
			self.verbose = True
			self.quiet = False

		if self.debug_opts:
			opt_postproc_debug(self)

		from .util import Util
		self._util = Util(self)

		del self._cloned

		self._lock()

		if need_proto:
			from .protocol import init_proto_from_cfg, warn_trustlevel
			# requires the default-to-none behavior, so do after the lock:
			self._proto = init_proto_from_cfg(self, need_amt=need_amt)

		if self._opts and not caller_post_init:
			self._post_init()

		# Check user-set opts without modifying them
		check_opts(self)

		if need_proto:
			warn_trustlevel(self) # do this only after proto is initialized

	def _post_init(self):
		if self.help or self.longhelp:
			from .help import print_help
			print_help(self, self._opts) # exits
		del self._opts

	def _usage(self):
		from .help import make_usage_str
		print(make_usage_str(self, caller='user'))
		sys.exit(1) # called only on bad invocation

	def _set_cfg_from_env(self):
		for name, val in ((k, v) for k, v in os.environ.items() if k.startswith('MMGEN_')):
			if name == 'MMGEN_DEBUG_ALL':
				continue
			if name in self._env_opts:
				if val: # ignore empty string values; string value of '0' or 'false' sets variable to False
					disable = name.startswith('MMGEN_DISABLE_')
					gname = name[(6, 14)[disable]:].lower()
					if gname in self._uopts: # don’t touch attr if already set by user
						continue
					if hasattr(self, gname):
						setattr(
							self,
							gname,
							conv_type(name, val, getattr(self, gname), 'environment var', invert_bool=disable))
						yield gname
					else:
						raise ValueError(f'Name {gname!r} not present in globals')
			else:
				raise ValueError(f'{name!r} is not a valid MMGen environment variable')

	def _set_cfg_from_cfg_file(self, env_cfg, need_proto):

		_ret = namedtuple('cfgfile_opts', ['non_auto', 'autoset', 'auto_typeset'])

		if not self._use_cfg_file:
			return _ret((), {}, {})

		# check for changes in system template file (term must be initialized)
		from .cfgfile import mmgen_cfg_file
		mmgen_cfg_file(self, 'sample')

		ucfg = mmgen_cfg_file(self, 'usr')

		self._cfgfile_fn = ucfg.fn

		if need_proto:
			from .protocol import init_proto

		autoset_opts = {}
		auto_typeset_opts = {}
		non_auto_opts = []
		already_set = tuple(self._uopts) + env_cfg

		for d in ucfg.get_lines():
			if d.name in self._cfg_file_opts:
				ns = d.name.split('_')
				if ns[0] in gc.core_coins:
					if not need_proto:
						continue
					nse, tn = (
						(ns[2:], ns[1]=='testnet') if len(ns) > 2 and ns[1] in ('mainnet', 'testnet') else
						(ns[1:], False)
					)
					# no instance yet, so override _class_ attr:
					cls = init_proto(self, ns[0], tn, need_amt=True, return_cls=True)
					attr = '_'.join(nse)
				else:
					cls = self
					attr = d.name
				refval = getattr(cls, attr)
				val = ucfg.parse_value(d.value, refval)
				if not val:
					die('CfgFileParseError', f'Parse error in file {ucfg.fn!r}, line {d.lineno}')
				val_conv = conv_type(attr, val, refval, 'configuration file option', src=ucfg.fn)
				if not attr in already_set:
					setattr(cls, attr, val_conv)
					non_auto_opts.append(attr)
			elif d.name in self._autoset_opts:
				autoset_opts[d.name] = d.value
			elif d.name in self._auto_typeset_opts:
				auto_typeset_opts[d.name] = d.value
			else:
				die('CfgFileParseError', f'{d.name!r}: unrecognized option in {ucfg.fn!r}, line {d.lineno}')

		return _ret(tuple(non_auto_opts), autoset_opts, auto_typeset_opts)

	def _set_autoset_opts(self, cfgfile_autoset_opts):

		def get_autoset_opt(key, val, src):

			def die_on_err(desc):
				from .util import fmt_list
				die(
					'UserOptError',
					'{a!r}: invalid {b} (not {c}: {d})'.format(
						a = val,
						b = {
							'cmdline': f'parameter for option --{key.replace("_", "-")}',
							'cfgfile': f'value for cfg file option {key!r}'
						}[src],
						c = desc,
						d = fmt_list(data.choices)))

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

			data = self._autoset_opts[key]

			return getattr(opt_type, data.type)()

		# Check autoset opts, setting if unset
		for key in self._autoset_opts:

			if key in self._cloned:
				continue

			assert not hasattr(self, key), f'autoset opt {key!r} is already set, but it shouldn’t be!'

			if key in self._uopts:
				val, src = (self._uopts[key], 'cmdline')
			elif key in cfgfile_autoset_opts:
				val, src = (cfgfile_autoset_opts[key], 'cfgfile')
			else:
				val = None

			if val is None:
				setattr(self, key, self._autoset_opts[key].choices[0])
			else:
				setattr(self, key, get_autoset_opt(key, val, src=src))

	def _set_auto_typeset_opts(self, cfgfile_auto_typeset_opts):

		def do_set(key, val, ref_type):
			assert not hasattr(self, key), f'{key!r} is in cfg!'
			setattr(self, key, None if val is None else ref_type(val))

		for key, ref_type in self._auto_typeset_opts.items():
			if key in self._uopts:
				do_set(key, self._uopts[key], ref_type)
			elif key in cfgfile_auto_typeset_opts:
				do_set(key, cfgfile_auto_typeset_opts[key], ref_type)

	def _die_on_incompatible_opts(self):
		for group in self._incompatible_opts:
			bad = [k for k in self.__dict__ if k in group and getattr(self, k) is not None]
			if len(bad) > 1:
				die(1, 'Conflicting options: {}'.format(', '.join(map(fmt_opt, bad))))

	def _set_quiet(self, val):
		from .util import Util
		self.__dict__['quiet'] = val
		self.__dict__['_util'] = Util(self) # qmsg, qmsg_r

def check_opts(cfg): # Raises exception if any check fails

	from .util import is_int, Msg

	def get_desc(desc_pfx=''):
		return (
			(desc_pfx + ' ' if desc_pfx else '')
			+ (
				f'parameter for command-line option {fmt_opt(name)!r}'
					if name in cfg._uopts and 'command-line' in cfg._uopt_desc else
				f'value for configuration option {name!r}'
			)
			+ (' from environment' if name in cfg._envopts else '')
			+ (f' in {cfg._cfgfile_fn!r}' if name in cfg._cfgfile_opts.non_auto else '')
		)

	def display_opt(name, val='', beg='For selected', end=':\n'):
		from .util import msg_r
		msg_r('{} option {!r}{}'.format(
			beg,
			f'{fmt_opt(name)}={val}' if val else fmt_opt(name),
			end))

	def opt_compares(val, op_str, target):
		import operator
		if not {
			'<':  operator.lt,
			'<=': operator.le,
			'>':  operator.gt,
			'>=': operator.ge,
			'=':  operator.eq,
		}[op_str](val, target):
			die('UserOptError', f'{val}: invalid {get_desc()} (not {op_str} {target})')

	def opt_is_int(val, desc_pfx=''):
		if not is_int(val):
			die('UserOptError', f'{val!r}: invalid {get_desc(desc_pfx)} (not an integer)')

	def opt_is_in_list(val, tlist, desc_pfx=''):
		if val not in tlist:
			q, sep = (('', ','), ("'", "','"))[isinstance(tlist[0], str)]
			die('UserOptError', '{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}'.format(
				v = val,
				w = get_desc(desc_pfx),
				q = q,
				o = sep.join(map(str, sorted(tlist)))))

	def opt_unrecognized():
		die('UserOptError', f'{val!r}: unrecognized {get_desc()}')

	class check_funcs:

		def in_fmt():
			from .wallet import get_wallet_data
			wd = get_wallet_data(fmt_code=val)
			if not wd:
				opt_unrecognized()
			if name == 'out_fmt':
				p = 'hidden_incog_output_params'

				if wd.type == 'incog_hidden' and not getattr(cfg, p):
					die('UserOptError',
						'Hidden incog format output requested.  ' +
						f'You must supply a file and offset with the {fmt_opt(p)!r} option')

				if wd.base_type == 'incog_base' and cfg.old_incog_fmt:
					display_opt(name, val, beg='Selected', end=' ')
					display_opt('old_incog_fmt', beg='conflicts with', end=':\n')
					die('UserOptError', 'Export to old incog wallet format unsupported')
				elif wd.type == 'brain':
					die('UserOptError', 'Output to brainwallet format unsupported')

		out_fmt = in_fmt

		def hidden_incog_input_params():
			a = val.rsplit(',', 1) # permit comma in filename
			if len(a) != 2:
				display_opt(name, val)
				die('UserOptError', 'Option requires two comma-separated arguments')

			fn, offset = a
			opt_is_int(offset)

			from .fileutil import check_infile, check_outdir, check_outfile
			if name == 'hidden_incog_input_params':
				check_infile(fn, blkdev_ok=True)
				key2 = 'in_fmt'
			else:
				try:
					os.stat(fn)
				except:
					b = os.path.dirname(fn)
					if b:
						check_outdir(b)
				else:
					check_outfile(fn, blkdev_ok=True)
				key2 = 'out_fmt'

			if hasattr(cfg, key2):
				val2 = getattr(cfg, key2)
				from .wallet import get_wallet_data
				wd = get_wallet_data('incog_hidden')
				if val2 and val2 not in wd.fmt_codes:
					die('UserOptError', f'Option conflict:\n  {fmt_opt(name)}, with\n  {fmt_opt(key2)}={val2}')

		hidden_incog_output_params = hidden_incog_input_params

		def subseeds():
			from .subseed import SubSeedIdxRange
			opt_compares(val, '>=', SubSeedIdxRange.min_idx)
			opt_compares(val, '<=', SubSeedIdxRange.max_idx)

		def seed_len():
			from .seed import Seed
			opt_is_in_list(int(val), Seed.lens)

		def hash_preset():
			from .crypto import Crypto
			opt_is_in_list(val, list(Crypto.hash_presets.keys()))

		def brain_params():
			a = val.split(',')
			if len(a) != 2:
				display_opt(name, val)
				die('UserOptError', 'Option requires two comma-separated arguments')

			opt_is_int(a[0], desc_pfx='seed length')
			from .seed import Seed
			opt_is_in_list(int(a[0]), Seed.lens, desc_pfx='seed length')

			from .crypto import Crypto
			opt_is_in_list(a[1], list(Crypto.hash_presets.keys()), desc_pfx='hash preset')

		def usr_randchars():
			if val != 0:
				opt_compares(val, '>=', cfg.min_urandchars)
				opt_compares(val, '<=', cfg.max_urandchars)

		def tx_confs():
			opt_is_int(val)
			opt_compares(int(val), '>=', 1)

		def vsize_adj():
			from .util import ymsg
			ymsg(f'Adjusting transaction vsize by a factor of {val:1.2f}')

		def daemon_id():
			from .daemon import CoinDaemon
			opt_is_in_list(val, CoinDaemon.all_daemon_ids())

		def locktime():
			opt_is_int(val)
			opt_compares(int(val), '>', 0)

		def columns():
			opt_compares(val, '>', 10)

	# TODO: add checks for token, rbf, tx_fee
	check_funcs_names = tuple(check_funcs.__dict__)
	for name in tuple(cfg._uopts) + cfg._envopts + cfg._cfgfile_opts.non_auto:
		val = getattr(cfg, name)
		if name in cfg._infile_opts:
			from .fileutil import check_infile
			check_infile(val) # file exists and is readable - dies on error
		elif name == 'outdir':
			from .fileutil import check_outdir
			check_outdir(val) # dies on error
		elif name in check_funcs_names:
			getattr(check_funcs, name)()
		elif cfg.debug:
			Msg(f'check_opts(): No test for config opt {name!r}')

def fmt_opt(o):
	return '--' + o.replace('_', '-')

def opt_postproc_debug(cfg):
	none_opts = [k for k in dir(cfg) if k[:2] != '__' and getattr(cfg, k) is None]
	from .util import Msg
	Msg('\n    Configuration opts:')
	for e in [d for d in dir(cfg) if d[:2] != '__']:
		Msg(f'        {e:<20}: {getattr(cfg, e)}')
	Msg("    Configuration opts set to 'None':")
	Msg('        {}\n'.format('\n        '.join(none_opts)))
	Msg('\n=== end opts.py debug ===\n')

def conv_type(
		name,
		val,
		refval,
		desc,
		invert_bool = False,
		src         = None):

	def do_fail():
		die(1, '{a!r}: invalid value for {b} {c!r}{d} (must be of type {e!r})'.format(
			a = val,
			b = desc,
			c = fmt_opt(name) if 'command-line' in desc else name,
			d = f' in {src!r}' if src else '',
			e = type(refval).__name__))

	if type(refval) is bool:
		v = str(val).lower()
		ret = (
			True  if v in ('true', 'yes', '1', 'on') else
			False if v in ('false', 'no', 'none', '0', 'off', '') else
			None
		)
		return do_fail() if ret is None else (not ret) if invert_bool else ret
	else:
		try:
			return type(refval)(not val if invert_bool else val)
		except:
			do_fail()
