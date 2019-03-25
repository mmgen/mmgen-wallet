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
globalvars.py:  Constants and configuration options for the MMGen suite
"""

import sys,os

# Global vars are set to dfl values in class g.
# They're overridden in this order:
#   1 - config file
#   2 - environmental vars
#   3 - command line

class g(object):

	def die(ev=0,s=''):
		if s: sys.stderr.write(s+'\n')
		sys.exit(ev)

	# Constants:

	version      = '0.10.099'
	release_date = 'February 2019'

	proj_name = 'MMGen'
	proj_url  = 'https://github.com/mmgen/mmgen'
	prog_name = os.path.basename(sys.argv[0])
	author    = 'The MMGen Project'
	email     = '<mmgen@tuta.io>'
	Cdates    = '2013-2019'
	keywords  = 'Bitcoin, BTC, cryptocurrency, wallet, cold storage, offline, online, spending, open-source, command-line, Python, Linux, Bitcoin Core, bitcoind, hd, deterministic, hierarchical, secure, anonymous, Electrum, seed, mnemonic, brainwallet, Scrypt, utility, script, scriptable, blockchain, raw, transaction, permissionless, console, terminal, curses, ansi, color, tmux, remote, client, daemon, RPC, json, entropy, xterm, rxvt, PowerShell, MSYS, MinGW, mswin, Armbian, Raspbian, Raspberry Pi, Orange Pi, BCash, BCH, Litecoin, LTC, altcoin, ZEC, Zcash, DASH, Dashpay, ETH, Ethereum, Classic, SHA256Compress, XMR, Monero, monerod, EMC, Emercoin, ERC20, token, deploy, contract, gas, fee, smart contract, solidity, Parity, testnet, devmode, Kovan'
	max_int   = 0xffffffff

	stdin_tty = bool(sys.stdin.isatty() or os.getenv('MMGEN_TEST_SUITE_POPEN_SPAWN'))
	stdout_fileno = sys.stdout.fileno()
	stderr_fileno = sys.stderr.fileno()

	http_timeout = 60

	# Variables - these might be altered at runtime:

	user_entropy   = ''
	hash_preset    = '3'
	usr_randchars  = 30

	tx_fee_adj   = 1.0
	tx_confs     = 3
	seed_len     = 256

	# Constant vars - some of these might be overriden in opts.py, but they don't change thereafter

	coin                 = 'BTC'
	dcoin                = None # the display coin unit
	token                = ''
	debug                = False
	debug_opts           = False
	debug_rpc            = False
	debug_addrlist       = False
	quiet                = False
	no_license           = False
	force_256_color      = False
	testnet              = False
	regtest              = False
	accept_defaults      = False
	use_internal_keccak_module = False

	chain                = None # set by first call to rpc_init()
	chains               = 'mainnet','testnet','regtest'

	# rpc:
	rpc_host             = ''
	rpc_port             = 0
	rpc_user             = ''
	rpc_password         = ''
	rpc_fail_on_command  = ''
	rpch                 = None # global RPC handle

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

	for k in ('linux','win','msys'):
		if sys.platform[:len(k)] == k:
			platform = { 'linux':'linux', 'win':'win', 'msys':'win' }[k]
			break
	else:
		die(1,"'{}': platform not supported by {}\n".format(sys.platform,proj_name))

	color = sys.stdout.isatty() and platform != 'win'

	if os.getenv('HOME'):                             # Linux or MSYS
		home_dir = os.getenv('HOME')
	elif platform == 'win': # Windows native:
		die(1,'$HOME not set!  {} for Windows must be run in MSYS environment'.format(proj_name))
	else:
		die(2,'$HOME is not set!  Unable to determine home directory')

	data_dir_root,data_dir,cfg_file = None,None,None
	daemon_data_dir = '' # set by user or protocol

	# global var sets user opt:
	global_sets_opt = ( 'minconf','seed_len','hash_preset','usr_randchars','debug',
						'quiet','tx_confs','tx_fee_adj','key_generator' )

	# user opt sets global var:
	opt_sets_global = ( 'use_internal_keccak_module', )

	# 'long' opts - opt sets global var
	common_opts = (
		'color','no_license','rpc_host','rpc_port','testnet','rpc_user','rpc_password',
		'daemon_data_dir','force_256_color','regtest','coin','bob','alice',
		'accept_defaults','token'
	)
	# opts initialized to None by opts.init() if not set by user
	required_opts = (
		'quiet','verbose','debug','outdir','echo_passphrase','passwd_file','stdout',
		'show_hash_presets','label','keep_passphrase','keep_hash_preset','yes',
		'brain_params','b16','usr_randchars','coin','bob','alice','key_generator',
		'hidden_incog_input_params','in_fmt'
	)
	incompatible_opts = (
		('base32','hex'), # mmgen-passgen
		('bob','alice'),
		('quiet','verbose'),
		('label','keep_label'),
		('tx_id','info'),
		('tx_id','terse_info'),
		('batch','rescan') # still incompatible as of Core 0.15.0
	)
	cfg_file_opts = (
		'color','debug','hash_preset','http_timeout','no_license','rpc_host','rpc_port',
		'quiet','tx_fee_adj','usr_randchars','testnet','rpc_user','rpc_password',
		'daemon_data_dir','force_256_color','regtest',
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
		'MMGEN_BOGUS_WALLET_DATA',
		'MMGEN_BOGUS_SEND',
		'MMGEN_DEBUG',
		'MMGEN_DEBUG_OPTS',
		'MMGEN_DEBUG_RPC',
		'MMGEN_DEBUG_ADDRLIST',
		'MMGEN_DEBUG_UTF8',
		'MMGEN_QUIET',
		'MMGEN_FORCE_256_COLOR',
		'MMGEN_MIN_URANDCHARS',
		'MMGEN_NO_LICENSE',
		'MMGEN_RPC_HOST',
		'MMGEN_RPC_FAIL_ON_COMMAND',
		'MMGEN_TESTNET',
		'MMGEN_REGTEST',
		'MMGEN_TRACEBACK',
		'MMGEN_USE_STANDALONE_SCRYPT_MODULE',

		'MMGEN_DISABLE_COLOR',
	)

	min_screen_width = 80
	minconf = 1
	max_tx_file_size = 100000
	max_input_size   = 1024 * 1024

	passwd_max_tries = 5

	max_urandchars = 80
	min_urandchars = 10

	seed_lens = 128,192,256

	mmenc_ext      = 'mmenc'
	salt_len       = 16
	aesctr_iv_len  = 16
	aesctr_dfl_iv  = b'\x00' * (aesctr_iv_len-1) + b'\x01'
	hincog_chk_len = 8

	key_generators = 'python-ecdsa','secp256k1' # '1','2'
	key_generator  = 2 # secp256k1 is default

	use_standalone_scrypt_module = False
	hash_presets = {
	#   Scrypt params:
	#   ID    N   p  r (N is an exponent of two)
		'1': [12, 8, 1],
		'2': [13, 8, 4],
		'3': [14, 8, 8],
		'4': [15, 8, 12],
		'5': [16, 8, 16],
		'6': [17, 8, 20],
		'7': [18, 8, 24],
	}
