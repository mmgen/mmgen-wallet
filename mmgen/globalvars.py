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
	_set_ok = ('user_entropy','session')
	_reset_ok = ('stdout','stderr','accept_defaults')
	_use_class_attr = True

	# Constants:
	version      = '0.12.199'
	release_date = 'July 2020'

	proj_name = 'MMGen'
	proj_url  = 'https://github.com/mmgen/mmgen'
	prog_name = os.path.basename(sys.argv[0])
	author    = 'The MMGen Project'
	email     = '<mmgen@tuta.io>'
	Cdates    = '2013-2021'
	keywords  = 'Bitcoin, BTC, Ethereum, ETH, Monero, XMR, ERC20, cryptocurrency, wallet, BIP32, cold storage, offline, online, spending, open-source, command-line, Python, Linux, Bitcoin Core, bitcoind, hd, deterministic, hierarchical, secure, anonymous, Electrum, seed, mnemonic, brainwallet, Scrypt, utility, script, scriptable, blockchain, raw, transaction, permissionless, console, terminal, curses, ansi, color, tmux, remote, client, daemon, RPC, json, entropy, xterm, rxvt, PowerShell, MSYS, MSYS2, MinGW, MinGW64, MSWin, Armbian, Raspbian, Raspberry Pi, Orange Pi, BCash, BCH, Litecoin, LTC, altcoin, ZEC, Zcash, DASH, Dashpay, SHA256Compress, monerod, EMC, Emercoin, token, deploy, contract, gas, fee, smart contract, solidity, Parity, OpenEthereum, testnet, devmode, Kovan'
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
	dfl_seed_len    = 256
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
	use_internal_keccak_module = False

	# rpc:
	rpc_host             = ''
	rpc_port             = 0
	rpc_user             = ''
	rpc_password         = ''
	monero_wallet_rpc_host = 'localhost'
	monero_wallet_rpc_user = 'monero'
	monero_wallet_rpc_password = ''
	rpc_fail_on_command  = ''
	aiohttp_rpc_queue_len = 16
	session              = None
	cached_balances      = False

	# regtest:
	bob                  = False
	alice                = False

	# test suite:
	bogus_wallet_data    = ''
	bogus_send           = False
	debug_utf8           = False
	traceback            = False
	test_suite           = False
	test_suite_popen_spawn = False
	terminal_width       = 0

	mnemonic_entry_modes = {}
	color = bool(
		( sys.stdout.isatty() and not os.getenv('MMGEN_TEST_SUITE_PEXPECT') ) or
		os.getenv('MMGEN_FORCE_COLOR')
	)

	for k in ('linux','win','msys'):
		if sys.platform[:len(k)] == k:
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

	# https://wiki.debian.org/Python:
	#   Debian (Ubuntu) sys.prefix is '/usr' rather than '/usr/local, so add 'local'
	# This must match the configuration in setup.py
	shared_data_path = os.path.join(
		sys.prefix,
		*(['local','share'] if platform == 'linux' else ['share']),
		proj_name.lower()
	)
	data_dir_root,data_dir,cfg_file = None,None,None
	daemon_data_dir = '' # set by user

	# global var sets user opt:
	global_sets_opt = (
		'minconf','usr_randchars','debug', 'quiet','tx_confs','tx_fee_adj','key_generator' )

	# user opt sets global var:
	opt_sets_global = (
		'use_internal_keccak_module','subseeds','cached_balances' )

	# 'long' opts - opt sets global var
	common_opts = (
		'color','no_license','testnet',
		'rpc_host','rpc_port','rpc_user','rpc_password','rpc_backend','aiohttp_rpc_queue_len',
		'monero_wallet_rpc_host','monero_wallet_rpc_user','monero_wallet_rpc_password',
		'daemon_data_dir','force_256_color','regtest','coin','bob','alice',
		'accept_defaults','token'
	)
	# opts initialized to None by opts.init() if not set by user
	required_opts = (
		'quiet','verbose','debug','outdir','echo_passphrase','passwd_file','stdout',
		'show_hash_presets','label','keep_passphrase','keep_hash_preset','yes',
		'brain_params','b16','usr_randchars','coin','bob','alice','key_generator',
		'hidden_incog_input_params','in_fmt','hash_preset','seed_len',
	)
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
		'eth_mainnet_chain_name','eth_testnet_chain_name',
		'max_tx_file_size','max_input_size'
	)
	# Supported environmental vars
	# The corresponding vars (lowercase, minus 'mmgen_') must be initialized in g
	# 'DISABLE_' env vars disable the corresponding var in g
	env_opts = (
		'MMGEN_DEBUG_ALL', # special: there is no g.debug_all var

		'MMGEN_TEST_SUITE',
		'MMGEN_TEST_SUITE_POPEN_SPAWN',
		'MMGEN_TERMINAL_WIDTH',
		'MMGEN_BOGUS_WALLET_DATA',
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
		'MMGEN_USE_STANDALONE_SCRYPT_MODULE',

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
	}

	min_screen_width = 80
	minconf = 1
	max_tx_file_size = 100000
	max_input_size   = 1024 * 1024

	passwd_max_tries = 5

	max_urandchars = 80
	min_urandchars = 10

	seed_lens = 128,192,256
	scramble_hash_rounds = 10
	subseeds = 100

	mmenc_ext      = 'mmenc'
	salt_len       = 16
	aesctr_iv_len  = 16
	aesctr_dfl_iv  = int.to_bytes(1,aesctr_iv_len,'big')
	hincog_chk_len = 8

	key_generators = ('python-ecdsa','libsecp256k1') # '1','2'
	key_generator  = 2 # libsecp256k1 is default

	force_standalone_scrypt_module = False
	# Scrypt params: 'id_num': [N, p, r] (N is an exponent of two)
	# NB: hashlib.scrypt in Python (>=v3.6) supports max N value of 14.  This means that
	# for hash presets > 3 the standalone scrypt library must be used!
	hash_presets = {
		'1': [12, 8, 1],
		'2': [13, 8, 4],
		'3': [14, 8, 8],
		'4': [15, 8, 12],
		'5': [16, 8, 16],
		'6': [17, 8, 20],
		'7': [18, 8, 24],
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
