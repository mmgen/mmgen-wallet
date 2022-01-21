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
from decimal import Decimal
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
	_set_ok = ('user_entropy','session')
	_reset_ok = ('stdout','stderr','accept_defaults')
	_use_class_attr = True

	# Constants:

	proj_name = 'MMGen'
	proj_url  = 'https://github.com/mmgen/mmgen'
	prog_name = os.path.basename(sys.argv[0])
	author    = 'The MMGen Project'
	email     = '<mmgen@tuta.io>'
	Cdates    = '2013-2022'

	try:
		from importlib.resources import files # Python 3.9
	except ImportError:
		from importlib_resources import files

	version      = files('mmgen').joinpath('data','version').read_text().strip()
	release_date = files('mmgen').joinpath('data','release_date').read_text().strip()

	max_int   = 0xffffffff

	stdin_tty = sys.stdin.isatty()
	stdout = sys.stdout
	stderr = sys.stderr

	http_timeout = 60
	err_disp_timeout = 0.7
	short_disp_timeout = 0.3
	min_time_precision = 18

	# Variables - these might be altered at runtime:

	user_entropy    = b''
	dfl_hash_preset = '3'
	usr_randchars   = 30

	tx_fee_adj   = Decimal('1.0')
	tx_confs     = 3

	# Constant vars - some of these might be overridden in opts.py, but they don't change thereafter

	coin                 = ''
	token                = ''
	debug                = False
	debug_opts           = False
	debug_rpc            = False
	debug_addrlist       = False
	debug_subseed        = False
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

	# miscellaneous features:
	use_internal_keccak_module = False
	enable_erigon = False

	# test suite:
	bogus_send           = False
	debug_utf8           = False
	traceback            = False
	test_suite           = False
	test_suite_deterministic = False
	test_suite_popen_spawn = False
	terminal_width       = 0

	mnemonic_entry_modes = {}
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

	data_dir_root,data_dir,cfg_file = None,None,None
	daemon_data_dir = '' # set by user
	daemon_id = ''

	# global var sets user opt:
	global_sets_opt = (
		'use_internal_keccak_module',
		'minconf','usr_randchars','debug','quiet','tx_confs','tx_fee_adj' )

	# user opt sets global var:
	opt_sets_global = ( 'cached_balances', )

	# 'long' opts - opt sets global var
	common_opts = (
		'color','no_license','testnet',
		'rpc_host','rpc_port','rpc_user','rpc_password','rpc_backend','aiohttp_rpc_queue_len',
		'monero_wallet_rpc_host','monero_wallet_rpc_user','monero_wallet_rpc_password',
		'daemon_data_dir','force_256_color','regtest','coin','bob','alice',
		'accept_defaults','token','ignore_daemon_version','daemon_id','http_timeout',
	)
	# opts not in common_opts but required to be set during opts initialization
	init_opts = ('show_hash_presets','yes','verbose')
	incompatible_opts = (
		('help','longhelp'),
		('bob','alice'),
		('label','keep_label'),
		('tx_id','info'),
		('tx_id','terse_info'),
		('batch','rescan'), # TODO: still incompatible?
	)
	cfg_file_opts = (
		'color','debug','hash_preset','http_timeout','no_license','rpc_host','rpc_port',
		'quiet','tx_fee_adj','usr_randchars','testnet','rpc_user','rpc_password',
		'monero_wallet_rpc_host','monero_wallet_rpc_user','monero_wallet_rpc_password',
		'daemon_data_dir','force_256_color','regtest','subseeds','mnemonic_entry_modes',
		'btc_max_tx_fee','ltc_max_tx_fee','bch_max_tx_fee','eth_max_tx_fee',
		'btc_ignore_daemon_version','bch_ignore_daemon_version','ltc_ignore_daemon_version',
		'eth_ignore_daemon_version','etc_ignore_daemon_version',
		'eth_mainnet_chain_names','eth_testnet_chain_names',
		'max_tx_file_size','max_input_size'
	)
	# Supported environmental vars
	# The corresponding vars (lowercase, minus 'mmgen_') must be initialized in g
	# 'DISABLE_' env vars disable the corresponding var in g
	env_opts = (
		'MMGEN_DEBUG_ALL', # special: there is no g.debug_all var

		'MMGEN_TEST_SUITE',
		'MMGEN_TEST_SUITE_DETERMINISTIC',
		'MMGEN_TEST_SUITE_POPEN_SPAWN',
		'MMGEN_TERMINAL_WIDTH',
		'MMGEN_BOGUS_SEND',
		'MMGEN_DEBUG',
		'MMGEN_DEBUG_OPTS',
		'MMGEN_DEBUG_RPC',
		'MMGEN_DEBUG_ADDRLIST',
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
		'MMGEN_TRACEBACK',
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
		autoset_opts['rpc_backend'].choices.remove('aiohttp')
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

	scramble_hash_rounds = 10

	salt_len       = 16
	aesctr_iv_len  = 16
	aesctr_dfl_iv  = int.to_bytes(1,aesctr_iv_len,'big')
	hincog_chk_len = 8

	force_standalone_scrypt_module = False
	# Scrypt params: 'id_num': [N, r, p] (N is an exponent of two)
	# NB: hashlib.scrypt in Python (>=v3.6) supports max N value of 14.  This means that
	# for hash presets > 3 the standalone scrypt library must be used!
	_hp = namedtuple('scrypt_preset',['N','r','p'])
	hash_presets = {
		'1': _hp(12, 8, 1),
		'2': _hp(13, 8, 4),
		'3': _hp(14, 8, 8),
		'4': _hp(15, 8, 12),
		'5': _hp(16, 8, 16),
		'6': _hp(17, 8, 20),
		'7': _hp(18, 8, 24),
	}

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

g = GlobalContext()
