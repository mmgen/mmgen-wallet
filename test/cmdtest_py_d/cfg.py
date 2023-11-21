#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_py_d.cfg: configuration data for cmdtest.py
"""

from .common import pwfile,hincog_fn,incog_id_fn,randbool
from ..include.common import cfg

cmd_groups_altcoin = ['ref_altcoin','autosign','ethdev','xmrwallet','xmr_autosign']

cmd_groups_dfl = {
	'misc':             ('CmdTestMisc',{}),
	'opts':             ('CmdTestOpts',{'full_data':True}),
	'cfgfile':          ('CmdTestCfgFile',{'full_data':True}),
	'helpscreens':      ('CmdTestHelp',{'modname':'misc','full_data':True}),
	'main':             ('CmdTestMain',{'full_data':True}),
	'conv':             ('CmdTestWalletConv',{'is3seed':True,'modname':'wallet'}),
	'ref':              ('CmdTestRef',{}),
	'ref3':             ('CmdTestRef3Seed',{'is3seed':True,'modname':'ref_3seed'}),
	'ref3_addr':        ('CmdTestRef3Addr',{'is3seed':True,'modname':'ref_3seed'}),
	'ref_altcoin':      ('CmdTestRefAltcoin',{}),
	'seedsplit':        ('CmdTestSeedSplit',{}),
	'tool':             ('CmdTestTool',{'full_data':True}),
	'input':            ('CmdTestInput',{}),
	'output':           ('CmdTestOutput',{'modname':'misc','full_data':True}),
	'autosign':         ('CmdTestAutosign',{}),
	'regtest':          ('CmdTestRegtest',{}),
#	'chainsplit':       ('CmdTestChainsplit',{}),
	'ethdev':           ('CmdTestEthdev',{}),
	'xmrwallet':        ('CmdTestXMRWallet',{}),
	'xmr_autosign':     ('CmdTestXMRAutosign',{}),
}

cmd_groups_extra = {
	'autosign_btc':           ('CmdTestAutosignBTC',{'modname':'autosign'}),
	'autosign_live':          ('CmdTestAutosignLive',{'modname':'autosign'}),
	'autosign_live_simulate': ('CmdTestAutosignLiveSimulate',{'modname':'autosign'}),
	'create_ref_tx':          ('CmdTestRefTX',{'modname':'misc','full_data':True}),
}

cfgs = { # addr_idx_lists (except 31,32,33,34) must contain exactly 8 addresses
	'1':  { 'wpasswd':       'Dorian-α',
			'kapasswd':      'Grok the blockchain',
			'addr_idx_list': '12,99,5-10,5,12',
			'dep_generators':  {
				pwfile:        'walletgen',
				'mmdat':       'walletgen',
				'addrs':       'addrgen',
				'rawtx':       'txcreate',
				'txbump':      'txbump',
				'sigtx':       'txsign',
				'mmwords':     'export_mnemonic',
				'mmseed':      'export_seed',
				'mmhex':       'export_hex',
				'mmincog':     'export_incog',
				'mmincox':     'export_incog_hex',
				hincog_fn:     'export_incog_hidden',
				incog_id_fn:   'export_incog_hidden',
				'akeys.mmenc': 'keyaddrgen'
			},
	},
	'2':  { 'wpasswd':       'Hodling away',
			'addr_idx_list': '37,45,3-6,22-23',
			'seed_len':      128,
			'dep_generators': {
				'mmdat':   'walletgen2',
				'addrs':   'addrgen2',
				'rawtx':   'txcreate2',
				'sigtx':   'txsign2',
				'mmwords': 'export_mnemonic2',
			},
	},
	'3':  { 'wpasswd':       'Major miner',
			'addr_idx_list': '73,54,1022-1023,2-5',
			'dep_generators': {
				'mmdat': 'walletgen3',
				'addrs': 'addrgen3',
				'rawtx': 'txcreate3',
				'sigtx': 'txsign3'
			},
	},
	'4':  { 'wpasswd':       'Hashrate good',
			'addr_idx_list': '63,1004,542-544,7-9',
			'seed_len':      192,
			'dep_generators': {
				'mmdat':   'walletgen4',
				'mmbrain': 'walletgen4',
				'addrs':   'addrgen4',
				'rawtx':   'txcreate4',
				'sigtx':   'txsign4',
				'txdo':    'txdo4',
			},
			'bw_filename': 'brainwallet.mmbrain',
			'bw_params':   '192,1',
	},
	'5':  { 'wpasswd':     'My changed password-α',
			'hash_preset': '2',
			'dep_generators': {
				'mmdat': 'passchg',
				pwfile:  'passchg',
			},
	},
	'6':  { 'seed_len':       128,
			'seed_id':        'FE3C6545',
			'ref_bw_seed_id': '33F10310',
			'wpasswd':        'reference password',
			'kapasswd':      '',
			'dep_generators':  {
				'mmdat':       'ref_walletgen_brain_1',
				pwfile:        'ref_walletgen_brain_1',
				'addrs':       'refaddrgen_1',
				'akeys.mmenc': 'refkeyaddrgen_1'
			},
	},
	'7':  { 'seed_len':       192,
			'seed_id':        '1378FC64',
			'ref_bw_seed_id': 'CE918388',
			'wpasswd':        'reference password',
			'kapasswd':      '',
			'dep_generators':  {
				'mmdat':       'ref_walletgen_brain_2',
				pwfile:        'ref_walletgen_brain_2',
				'addrs':       'refaddrgen_2',
				'akeys.mmenc': 'refkeyaddrgen_2'
			},
	},
	'8':  { 'seed_len':       256,
			'seed_id':        '98831F3A',
			'ref_bw_seed_id': 'B48CD7FC',
			'wpasswd':        'reference password',
			'kapasswd':      '',
			'dep_generators':  {
				'mmdat':       'ref_walletgen_brain_3',
				pwfile:        'ref_walletgen_brain_3',
				'addrs':       'refaddrgen_3',
				'akeys.mmenc': 'refkeyaddrgen_3'
			},
	},
	'9':  { 'tool_enc_infn': 'tool_encrypt.in',
			'dep_generators': {
				'tool_encrypt.in':       'tool_encrypt',
				'tool_encrypt.in.mmenc': 'tool_encrypt',
			},
	},
	'11': {},
	'12': {},
	'13': {},
	'14': { 'kapasswd':      'Maxwell',
			'wpasswd':       'The Halving',
			'addr_idx_list': '61,998,502-504,7-9',
			'seed_len':      256,
			'dep_generators': {
				'mmdat':       'walletgen14',
				'addrs':       'addrgen14',
				'akeys.mmenc': 'keyaddrgen14',
			},
	},
	'15': { 'wpasswd':       'Dorian-α',
			'kapasswd':      'Grok the blockchain',
			'addr_idx_list': '12,99,5-10,5,12',
			'dep_generators':  {
				pwfile:       'walletgen_dfl_wallet',
				'addrs':      'addrgen_dfl_wallet',
				'rawtx':      'txcreate_dfl_wallet',
				'sigtx':      'txsign_dfl_wallet',
				'mmseed':     'export_seed_dfl_wallet',
				'del_dw_run': 'delete_dfl_wallet',
			},
	},
	'16': { 'wpasswd':     'My changed password',
			'hash_preset': '2',
			'dep_generators': {
				pwfile: 'passchg_dfl_wallet',
			},
	},
	'17': {},
	'18': {},
	'19': { 'wpasswd':'abc' },
	'20': { 'wpasswd':       'Vsize it',
			'addr_idx_list': '1-8',
			'seed_len':      256,
			'dep_generators': {
				'mmdat': 'walletgen5',
				'addrs': 'addrgen5',
				'rawtx': 'txcreate5',
				'sigtx': 'txsign5',
		},
	},
	'21': { 'wpasswd':       'Vsize it',
			'addr_idx_list': '1-8',
			'seed_len':      256,
			'dep_generators': {
				'mmdat': 'walletgen6',
				'addrs': 'addrgen6',
				'rawtx': 'txcreate6',
				'sigtx': 'txsign6',
		},
	},
	'22': {},
	'23': {},
	'26': {},
	'27': {},
	'28': {},
	'29': {}, # xmrwallet
	'31': {},
	'32': {},
	'33': {},
	'34': {},
	'39': {},
	'40': {},
	'41': {},
	'99': {}, # dummy
}

def fixup_cfgs():
	import os
	for src,target in (
			('6','11'),
			('7','12'),
			('8','13'),
			('6','26'),
			('7','27'),
			('8','28')
		):
		cfgs[target].update(cfgs[src])
		cfgs[target]['tmpdir'] = os.path.join('test','tmp',target)

	for k in cfgs:
		cfgs[k]['segwit'] = randbool() if cfg.segwit_random else bool(cfg.segwit or cfg.bech32)

	if cfg.debug_utf8:
		for k in cfgs:
			cfgs[k]['tmpdir'] += '-α'
