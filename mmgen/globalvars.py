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
globalvars.py:  Constants and configuration options for the MMGen suite
"""

import sys,os
from collections import namedtuple
from .devtools import *

from .base_obj import Lockable

def die(exit_val,s=''):
	if s:
		sys.stderr.write(s+'\n')
	sys.exit(exit_val)

class GlobalContext(Lockable):
	"""
	Set global vars to default values
	Globals are overridden in this order:
	  1 - config file
	  2 - environmental vars
	  3 - command line
	"""
	_autolock = False
	_set_ok = ('session',)
	_reset_ok = ('stdout','stderr','accept_defaults')
	_use_class_attr = True

	# Constants:

	proj_name = 'MMGen'
	proj_url  = 'https://github.com/mmgen/mmgen'
	prog_name = os.path.basename(sys.argv[0])
	author    = 'The MMGen Project'
	email     = '<mmgen@tuta.io>'
	Cdates    = '2013-2022'

	is_txprog = prog_name == 'mmgen-regtest' or prog_name.startswith('mmgen-tx')

	stdin_tty = sys.stdin.isatty()
	stdout = sys.stdout
	stderr = sys.stderr

	http_timeout = 60
	err_disp_timeout = 0.7
	short_disp_timeout = 0.3
	min_time_precision = 18

	# Variables - these might be altered at runtime:

	dfl_hash_preset = '3'
	usr_randchars   = 30

	tx_fee_adj   = 1.0
	tx_confs     = 3

	# Constant vars - some of these might be overridden in opts.py, but they don't change thereafter

	coin                 = ''
	token                = ''
	debug                = False
	debug_opts           = False
	debug_rpc            = False
	debug_addrlist       = False
	debug_subseed        = False
	debug_tw             = False
	quiet                = False
	no_license           = False
	force_256_color      = False
	testnet              = False
	regtest              = False
	accept_defaults      = False

	# rpc:
	rpc_host             = ''
	rpc_port             = 0
	rpc_user             = ''
	rpc_password         = ''
	ignore_daemon_version  = False
	monero_wallet_rpc_host = 'localhost'
	monero_wallet_rpc_user = 'monero'
	monero_wallet_rpc_password = ''
	aiohttp_rpc_queue_len = 16
	session              = None
	cached_balances      = False

	# regtest:
	bob                  = False
	alice                = False
	carol                = False
	regtest_user         = None

	# miscellaneous features:
	use_internal_keccak_module = False
	enable_erigon = False

	# test suite:
	bogus_send           = False
	debug_utf8           = False
	exec_wrapper         = False
	test_suite           = False
	test_suite_deterministic = False
	test_suite_popen_spawn = False

	mnemonic_entry_modes = {}

	# display:
	columns = 0
	color = bool(
		( sys.stdout.isatty() and not os.getenv('MMGEN_TEST_SUITE_PEXPECT') ) or
		os.getenv('MMGEN_FORCE_COLOR')
	)

	for k in ('linux','win','msys'):
		if sys.platform.startswith(k):
			platform = { 'linux':'linux', 'win':'win', 'msys':'win' }[k]
			break
	else:
		die(1,f'{sys.platform!r}: platform not supported by {proj_name}')

	if os.getenv('HOME'):   # Linux or MSYS2
		home_dir = os.getenv('HOME')
	elif platform == 'win': # Windows without MSYS2 - not supported
		die(1,f'$HOME not set!  {proj_name} for Windows must be run in MSYS2 environment')
	else:
		die(2,'$HOME is not set!  Unable to determine home directory')

	data_dir_root,data_dir,cfg_file = (None,None,None)
	daemon_data_dir = '' # set by user
	daemon_id = ''

	# must match CoinProtocol.coins
	core_coins = ('btc','bch','ltc','eth','etc','zec','xmr')

	# global var sets user opt:
	global_sets_opt = (
		'debug',
		'minconf',
		'quiet',
		'tx_confs',
		'tx_fee_adj',
		'use_internal_keccak_module',
		'usr_randchars' )

	# user opt sets global var:
	opt_sets_global = ( 'cached_balances', )

	# 'long' opt sets global var (subset of common_opts_data):
	common_opts = (
		'accept_defaults',
		'aiohttp_rpc_queue_len',
		'bob',
		'alice',
		'carol',
		'coin',
		'color',
		'columns',
		'daemon_data_dir',
		'daemon_id',
		'force_256_color',
		'http_timeout',
		'ignore_daemon_version',
		'no_license',
		'regtest',
		'rpc_backend',
		'rpc_host',
		'rpc_password',
		'rpc_port',
		'rpc_user',
		'testnet',
		'token' )

	# opts not in common_opts but required to be set during opts initialization
	init_opts = ('show_hash_presets','yes','verbose')
	incompatible_opts = (
		('help','longhelp'),
		('bob','alice','carol'),
		('label','keep_label'),
		('tx_id','info'),
		('tx_id','terse_info'),
	)
	cfg_file_opts = (
		'color',
		'daemon_data_dir',
		'debug',
		'force_256_color',
		'hash_preset',
		'http_timeout',
		'max_input_size',
		'max_tx_file_size',
		'mnemonic_entry_modes',
		'monero_wallet_rpc_host',
		'monero_wallet_rpc_password',
		'monero_wallet_rpc_user',
		'no_license',
		'quiet',
		'regtest',
		'rpc_host',
		'rpc_password',
		'rpc_port',
		'rpc_user',
		'subseeds',
		'testnet',
		'tx_fee_adj',
		'usr_randchars',
		'bch_max_tx_fee',
		'btc_max_tx_fee',
		'eth_max_tx_fee',
		'ltc_max_tx_fee',
		'bch_ignore_daemon_version',
		'btc_ignore_daemon_version',
		'etc_ignore_daemon_version',
		'eth_ignore_daemon_version',
		'ltc_ignore_daemon_version',
		'eth_mainnet_chain_names',
		'eth_testnet_chain_names' )

	# Supported environmental vars
	# The corresponding vars (lowercase, minus 'mmgen_') must be initialized in g
	# 'DISABLE_' env vars disable the corresponding var in g
	env_opts = (
		'MMGEN_DEBUG_ALL', # special: there is no g.debug_all var

		'MMGEN_COLUMNS',
		'MMGEN_TEST_SUITE',
		'MMGEN_TEST_SUITE_DETERMINISTIC',
		'MMGEN_TEST_SUITE_POPEN_SPAWN',
		'MMGEN_BOGUS_SEND',
		'MMGEN_DEBUG',
		'MMGEN_DEBUG_OPTS',
		'MMGEN_DEBUG_RPC',
		'MMGEN_DEBUG_ADDRLIST',
		'MMGEN_DEBUG_TW',
		'MMGEN_DEBUG_UTF8',
		'MMGEN_DEBUG_SUBSEED',
		'MMGEN_QUIET',
		'MMGEN_FORCE_256_COLOR',
		'MMGEN_MIN_URANDCHARS',
		'MMGEN_NO_LICENSE',
		'MMGEN_RPC_HOST',
		'MMGEN_RPC_FAIL_ON_COMMAND',
		'MMGEN_TESTNET',
		'MMGEN_REGTEST',
		'MMGEN_EXEC_WRAPPER',
		'MMGEN_RPC_BACKEND',
		'MMGEN_IGNORE_DAEMON_VERSION',
		'MMGEN_USE_STANDALONE_SCRYPT_MODULE',
		'MMGEN_ENABLE_ERIGON',

		'MMGEN_DISABLE_COLOR',
		'MMGEN_DISABLE_MSWIN_PW_WARNING',
	)
	infile_opts = (
		'keys_from_file',
		'mmgen_keys_from_file',
		'passwd_file',
		'keysforaddrs',
		'comment_file',
		'contract_data',
	)
	# Auto-typechecked and auto-set opts.  These have no corresponding value in g.
	# First value in list is the default
	ov = namedtuple('autoset_opt_info',['type','choices'])
	autoset_opts = {
		'fee_estimate_mode': ov('nocase_pfx', ['conservative','economical']),
		'rpc_backend':       ov('nocase_pfx', ['auto','httplib','curl','aiohttp','requests']),
	}
	if platform == 'win':
		_skip_type_check = ('stdout','stderr')

	auto_typeset_opts = {
		'seed_len': int,
		'subseeds': int,
		'vsize_adj': float,
	}

	min_screen_width = 80
	minconf = 1
	max_tx_file_size = 100000
	max_input_size   = 1024 * 1024

	passwd_max_tries = 5

	max_urandchars = 80
	min_urandchars = 10

	force_standalone_scrypt_module = False

	if os.getenv('MMGEN_TEST_SUITE'):
		err_disp_timeout = 0.1
		short_disp_timeout = 0.1
		if os.getenv('MMGEN_TEST_SUITE_POPEN_SPAWN'):
			stdin_tty = True
		if prog_name == 'unit_tests.py':
			_set_ok += ('debug_subseed',)
			_reset_ok += ('force_standalone_scrypt_module','session')

	if os.getenv('MMGEN_DEBUG_ALL'):
		for name in env_opts:
			if name[:11] == 'MMGEN_DEBUG':
				os.environ[name] = '1'

	def get_mmgen_data_file(self,filename,package='mmgen'):
		"""
		this is an expensive import, so do only when required
		"""
		# Resource will be unpacked and then cleaned up if necessary, see:
		#    https://docs.python.org/3/library/importlib.html:
		#        Note: This module provides functionality similar to pkg_resources Basic
		#        Resource Access without the performance overhead of that package.
		#    https://importlib-resources.readthedocs.io/en/latest/migration.html
		#    https://setuptools.readthedocs.io/en/latest/pkg_resources.html
		try:
			from importlib.resources import files # Python 3.9
		except ImportError:
			from importlib_resources import files
		return files(package).joinpath('data',filename).read_text()

	@property
	def version(self):
		return self.get_mmgen_data_file(
				filename = 'version',
				package  = 'mmgen_node_tools' if self.prog_name.startswith('mmnode-') else 'mmgen'
			).strip()

	@property
	def release_date(self):
		return self.get_mmgen_data_file(filename='release_date').strip()

g = GlobalContext()
