#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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

	skip_segwit_active_check = bool(os.getenv('MMGEN_TEST_SUITE'))

	def die(ev=0,s=''):
		if s: sys.stderr.write(s+'\n')
		sys.exit(ev)

	# Constants:

	version      = '0.9.8rc1'
	release_date = 'May 2018'

	proj_name = 'MMGen'
	proj_url  = 'https://github.com/mmgen/mmgen'
	prog_name = os.path.basename(sys.argv[0])
	author    = 'The MMGen Project'
	email     = '<mmgen@tuta.io>'
	Cdates    = '2013-2018'
	keywords  = 'Bitcoin, BTC, cryptocurrency, wallet, cold storage, offline, online, spending, open-source, command-line, Python, Linux, Bitcoin Core, bitcoind, hd, deterministic, hierarchical, secure, anonymous, Electrum, seed, mnemonic, brainwallet, Scrypt, utility, script, scriptable, blockchain, raw, transaction, permissionless, console, terminal, curses, ansi, color, tmux, remote, client, daemon, RPC, json, entropy, xterm, rxvt, PowerShell, MSYS, MinGW, mswin, Armbian, Raspbian, Raspberry Pi, Orange Pi, BCash, BCH, Litecoin, LTC, altcoin, ZEC, Zcash, DASH, Dashpay, ETH, Ethereum, Classic, SHA256Compress, XMR, Monero, EMC, Emercoin'
	max_int   = 0xffffffff
	stdin_tty = bool(sys.stdin.isatty() or os.getenv('MMGEN_TEST_SUITE'))
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
	debug                = False
	debug_opts           = False
	debug_rpc            = False
	debug_addrlist       = False
	quiet                = False
	no_license           = False
	color                = (False,True)[sys.stdout.isatty()]
	force_256_color      = False
	testnet              = False
	regtest              = False
	accept_defaults      = False
	chain                = None # set by first call to rpc_init()
	chains               = 'mainnet','testnet','regtest'
	daemon_version       = None # set by first call to rpc_init()
	rpc_host             = ''
	rpc_port             = 0
	rpc_user             = ''
	rpc_password         = ''
	rpch                 = None # global RPC handle

	bob                  = False
	alice                = False

	# test suite:
	bogus_wallet_data    = u''
	traceback_cmd        = 'scripts/traceback.py'
	debug_utf8           = False

	for k in ('win','linux'):
		if sys.platform[:len(k)] == k:
			platform = k; break
	else:
		die(1,"'{}': platform not supported by {}\n".format(sys.platform,proj_name))

	if os.getenv('HOME'):                             # Linux or MSYS
		home_dir = os.getenv('HOME').decode('utf8')
	elif platform == 'win': # Windows native:
		die(1,'$HOME not set!  {} for Windows must be run in MSYS environment'.format(proj_name))
	else:
		die(2,'$HOME is not set!  Unable to determine home directory')

	data_dir_root,data_dir,cfg_file = None,None,None
	daemon_data_dir = u'' # set by user or protocol

	# User opt sets global var:
	common_opts = (
		'color','no_license','rpc_host','rpc_port','testnet','rpc_user','rpc_password',
		'daemon_data_dir','force_256_color','regtest','coin','bob','alice',
		'accept_defaults'
	)
	required_opts = (
		'quiet','verbose','debug','outdir','echo_passphrase','passwd_file','stdout',
		'show_hash_presets','label','keep_passphrase','keep_hash_preset','yes',
		'brain_params','b16','usr_randchars','coin','bob','alice','key_generator'
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
		'btc_max_tx_fee','ltc_max_tx_fee','bch_max_tx_fee',
		'max_tx_file_size'
	)
	env_opts = (
		'MMGEN_BOGUS_WALLET_DATA',
		'MMGEN_DEBUG_ALL',
		'MMGEN_DEBUG',
		'MMGEN_DEBUG_OPTS',
		'MMGEN_DEBUG_RPC',
		'MMGEN_DEBUG_ADDRLIST',
		'MMGEN_DEBUG_UTF8',
		'MMGEN_QUIET',
		'MMGEN_DISABLE_COLOR',
		'MMGEN_FORCE_256_COLOR',
		'MMGEN_MIN_URANDCHARS',
		'MMGEN_NO_LICENSE',
		'MMGEN_RPC_HOST',
		'MMGEN_TESTNET',
		'MMGEN_REGTEST'
	)

	min_screen_width = 80
	minconf = 1
	max_tx_file_size = 100000

	# Global var sets user opt:
	global_sets_opt = ['minconf','seed_len','hash_preset','usr_randchars','debug',
						'quiet','tx_confs','tx_fee_adj','key_generator']

	passwd_max_tries = 5

	max_urandchars = 80
	min_urandchars = 10

	seed_lens = 128,192,256

	mmenc_ext      = 'mmenc'
	salt_len       = 16
	aesctr_iv_len  = 16
	hincog_chk_len = 8

	key_generators = 'python-ecdsa','secp256k1' # '1','2'
	key_generator  = 2 # secp256k1 is default

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
