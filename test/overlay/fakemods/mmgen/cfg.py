# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.overlay.fakemods.mmgen.cfg: overlay setup for cfg.py
"""

from .cfg_orig import *

GlobalConstants.CR = '\n'

for k, v in {
		# NB: check carefully that none of these attrs are required by Config(), Opts()
		# or anything they import or call before the lock is set in Config()

		### these are redefined:
		'color': bool(
			(sys.stdout.isatty() and not os.getenv('MMGEN_TEST_SUITE_PEXPECT')) or
			os.getenv('MMGEN_TEST_SUITE_ENABLE_COLOR')),
		'min_urandchars':     3,
		'err_disp_timeout':   0.1,
		'short_disp_timeout': 0.1,
		'test_suite':         True,

		### everything below is missing in Config:

		# these are referenced in production code:
		'test_suite_cfgtest':               False, # cfgfile - using getattr() with dfl val - OK
		'test_suite_popen_spawn':           False, # line_input() - using getattr() with dfl val - OK
		'test_suite_hold_protect_disable':  False, # init_term() - using getattr() with dfl val - OK
		'test_suite_autosign_threaded':     False, # autosign - OK
		'test_suite_root_pfx':              '',    # autosign - OK
		'test_suite_bogus_send':            False, # tx.online - OK
		'test_datadir':                     os.path.join('test', 'tmp', 'data_dir'), # cfg - OK

		# these are referenced in test suite only:
		'test_suite_autosign_led_simulate':    False,
		'test_suite_exec_wrapper':             False,
		'test_suite_bogus_unspent_data':       '',
		'test_suite_debug_utf8':               False,
		'test_suite_deterministic':            False,
		'test_suite_devnet_block_period':      0,
		'test_suite_devtools':                 False,
		'test_suite_enable_color':             False,
		'test_suite_ignore_test_py_exception': False,
		'test_suite_legacy_tx':                False,
		'test_suite_pexpect':                  False,
		'test_suite_pexpect_timeout':          0,
	}.items():
	setattr(Config, k, v)

Config._env_opts += (
	# these are referenced in test suite only, except as noted:
	'MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE',
	'MMGEN_TEST_SUITE_AUTOSIGN_THREADED',
	'MMGEN_TEST_SUITE_BOGUS_SEND',
	'MMGEN_TEST_SUITE_BOGUS_UNSPENT_DATA',
	'MMGEN_TEST_SUITE_CFGTEST',
	'MMGEN_TEST_SUITE_DEBUG_UTF8',
	'MMGEN_TEST_SUITE_DETERMINISTIC',
	'MMGEN_TEST_SUITE_DEVNET_BLOCK_PERIOD',
	'MMGEN_TEST_SUITE_DEVTOOLS',
	'MMGEN_TEST_SUITE_ENABLE_COLOR',
	'MMGEN_TEST_SUITE_EXEC_WRAPPER', # main - using os.getenv() - OK
	'MMGEN_TEST_SUITE_HOLD_PROTECT_DISABLE',
	'MMGEN_TEST_SUITE_IGNORE_TEST_PY_EXCEPTION',
	'MMGEN_TEST_SUITE_LEGACY_TX',
	'MMGEN_TEST_SUITE_PEXPECT',
	'MMGEN_TEST_SUITE_PEXPECT_TIMEOUT',
	'MMGEN_TEST_SUITE_POPEN_SPAWN',
	'MMGEN_TEST_SUITE_ROOT_PFX')

if os.getenv('MMGEN_TEST_SUITE_POPEN_SPAWN'):
	Config.stdin_tty = True

if gc.prog_name == 'modtest.py':
	Config._set_ok += ('debug_subseed',)
	Config._reset_ok += ('force_standalone_scrypt_module',)
