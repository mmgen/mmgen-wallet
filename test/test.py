#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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
test/test.py:  Test suite for the MMGen suite
"""

import sys,os,subprocess,shutil,time,re,json
from decimal import Decimal

repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path.__setitem__(0,repo_root)

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.test import *
from mmgen.protocol import CoinProtocol,init_coin

set_debug_all()

g.quiet = False # if 'quiet' was set in config file, disable here
os.environ['MMGEN_QUIET'] = '0' # and for the spawned scripts

log_file = u'test.py_log'

hincog_fn      = 'rand_data'
hincog_bytes   = 1024*1024
hincog_offset  = 98765
hincog_seedlen = 256

incog_id_fn  = u'incog_id'
non_mmgen_fn = u'coinkey'
pwfile = u'passwd_file'

ref_dir = os.path.join(u'test',u'ref')

rt_pw = u'abc-α'
ref_wallet_brainpass = 'abc'
ref_wallet_hash_preset = '1'
ref_wallet_incog_offset = 123

from mmgen.obj import MMGenTXLabel,PrivKey,ETHAmt
from mmgen.addr import AddrGenerator,KeyGenerator,AddrList,AddrData,AddrIdxList

ref_tx_label_jp = u'必要なのは、信用ではなく暗号化された証明に基づく電子取引システムであり、これにより希望する二者が信用できる第三者機関を介さずに直接取引できるよう' # 72 chars ('W'ide)
ref_tx_label_zh = u'所以，我們非常需要這樣一種電子支付系統，它基於密碼學原理而不基於信用，使得任何達成一致的雙方，能夠直接進行支付，從而不需要協力廠商仲介的參與。。' # 72 chars ('F'ull + 'W'ide)
ref_tx_label_lat_cyr_gr = u''.join(map(unichr,
									range(65,91) +
									range(1040,1072) + # cyrillic
									range(913,939) +   # greek
									range(97,123)))[:MMGenTXLabel.max_len] # 72 chars
ref_bw_hash_preset = '1'
ref_bw_file        = u'wallet.mmbrain'
ref_bw_file_spc    = u'wallet-spaced.mmbrain'

ref_kafile_pass        = 'kafile password'
ref_kafile_hash_preset = '1'

ref_enc_fn = u'sample-text.mmenc'
tool_enc_passwd = "Scrypt it, don't hash it!"
sample_text = \
	'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks\n'

# Laggy flash media cause pexpect to crash, so create a temporary directory
# under '/dev/shm' and put datadir and temp files here.
shortopts = ''.join([e[1:] for e in sys.argv if len(e) > 1 and e[0] == '-' and e[1] != '-'])
shortopts = ['-'+e for e in list(shortopts)]
data_dir_basename = u'data_dir' + ('',u'-α')[bool(os.getenv('MMGEN_DEBUG_UTF8'))]
data_dir = os.path.join(u'test',data_dir_basename)
trash_dir = os.path.join(u'test',u'trash')

if not any(e in ('--skip-deps','--resume','-S','-r') for e in sys.argv+shortopts):
	if g.platform == 'win':
		for tdir in (data_dir,trash_dir):
			try: os.listdir(tdir)
			except: pass
			else:
				try: shutil.rmtree(tdir)
				except: # we couldn't remove data dir - perhaps regtest daemon is running
					try: subprocess.call(['python',os.path.join('cmds','mmgen-regtest'),'stop'])
					except: rdie(1,"Unable to remove {!r}!".format(tdir))
					else:
						time.sleep(2)
						shutil.rmtree(tdir)
			os.mkdir(tdir,0755)
	else:
		d,pfx = '/dev/shm','mmgen-test-'
		try:
			subprocess.call('rm -rf {}/{}*'.format(d,pfx),shell=True)
		except Exception as e:
			die(2,'Unable to delete directory tree {}/{}* ({})'.format(d,pfx,e))
		try:
			import tempfile
			shm_dir = unicode(tempfile.mkdtemp('',pfx,d))
		except Exception as e:
			die(2,'Unable to create temporary directory in {} ({})'.format(d,e))
		for tdir in (data_dir,trash_dir):
			dd = os.path.join(shm_dir,os.path.basename(tdir))
			os.mkdir(dd,0755)
			try: os.unlink(tdir)
			except: pass
			os.symlink(dd,tdir)

opts_data = lambda: {
	'desc': 'Test suite for the MMGen suite',
	'usage':'[options] [command(s) or metacommand(s)]',
	'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-B, --bech32        Generate and use Bech32 addresses
-b, --buf-keypress  Use buffered keypresses as with real human input
-c, --print-cmdline Print the command line of each spawned command
-C, --coverage      Produce code coverage info using trace module
-x, --debug-pexpect Produce debugging output for pexpect calls
-D, --direct-exec   Bypass pexpect and execute a command directly (for
                    debugging only)
-e, --exact-output  Show the exact output of the MMGen script(s) being run
-g, --segwit        Generate and use Segwit addresses
-G, --segwit-random Generate and use a random mix of Segwit and Legacy addrs
-l, --list-cmds     List and describe the commands in the test suite
-L, --log           Log commands to file {lf}
-n, --names         Display command names instead of descriptions
-O, --popen-spawn   Use pexpect's popen_spawn instead of popen (always true, so ignored)
-p, --pause         Pause between tests, resuming on keypress
-P, --profile       Record the execution time of each script
-q, --quiet         Produce minimal output.  Suppress dependency info
-r, --resume=c      Resume at command 'c' after interrupted run
-s, --system        Test scripts and modules installed on system rather
                    than those in the repo root
-S, --skip-deps     Skip dependency checking for command
-u, --usr-random    Get random data interactively from user
-t, --traceback     Run the command inside the '{tbc}' script
-v, --verbose       Produce more verbose output
-W, --no-dw-delete  Don't remove default wallet from data dir after dw tests are done
-X, --exit-after=C  Exit after command 'C'
""".format(tbc=g.traceback_cmd,lf=log_file),
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

sys.argv = [sys.argv[0]] + ['--data-dir',data_dir] + sys.argv[1:]

cmd_args = opts.init(opts_data)
opt.popen_spawn = True # popen has issues, so use popen_spawn always

if not opt.system: os.environ['PYTHONPATH'] = repo_root

ref_subdir = '' if g.proto.base_coin == 'BTC' else 'ethereum_classic' if g.coin == 'ETC' else g.proto.name
altcoin_pfx = '' if g.proto.base_coin == 'BTC' else '-'+g.proto.base_coin
tn_ext = ('','.testnet')[g.testnet]

coin_sel = g.coin.lower()
if g.coin.lower() in ('eth','etc'): coin_sel = 'btc'

fork       = {'bch':'btc','btc':'btc','ltc':'ltc'}[coin_sel]
tx_fee     = {'btc':'0.0001','bch':'0.001','ltc':'0.01'}[coin_sel]
txbump_fee = {'btc':'123s','bch':'567s','ltc':'12345s'}[coin_sel]

rtFundAmt  = {'btc':'500','bch':'500','ltc':'5500'}[coin_sel]
rtFee = {
	'btc': ('20s','10s','60s','31s','10s','20s'),
	'bch': ('20s','10s','60s','0.0001','10s','20s'),
	'ltc': ('1000s','500s','1500s','0.05','400s','1000s')
}[coin_sel]
rtBals = {
	'btc': ('499.9999488','399.9998282','399.9998147','399.9996877',
			'52.99990000','946.99933647','999.99923647','52.9999','946.99933647'),
	'bch': ('499.9999484','399.9999194','399.9998972','399.9997692',
			'46.78900000','953.20966920','999.99866920','46.789','953.2096692'),
	'ltc': ('5499.99744','5399.994425','5399.993885','5399.987535',
			'52.99000000','10946.93753500','10999.92753500','52.99','10946.937535'),
}[coin_sel]
rtBals_gb = {
	'btc': ('116.77629233','283.22339537'),
	'bch': ('116.77637483','283.22339437'),
	'ltc': ('5116.77036263','283.21717237')
}[coin_sel]
rtBobOp3 = {'btc':'S:2','bch':'L:3','ltc':'S:2'}[coin_sel]

if opt.segwit and 'S' not in g.proto.mmtypes:
	die(1,'--segwit option incompatible with {}'.format(g.proto.__name__))
if opt.bech32 and 'B' not in g.proto.mmtypes:
	die(1,'--bech32 option incompatible with {}'.format(g.proto.__name__))

def randbool():
	return hexlify(os.urandom(1))[1] in '12345678'
def get_segwit_bool():
	return randbool() if opt.segwit_random else True if opt.segwit or opt.bech32 else False

def disable_debug():
	global save_debug
	save_debug = {}
	for k in g.env_opts:
		if k[:11] == 'MMGEN_DEBUG':
			save_debug[k] = os.getenv(k)
			os.environ[k] = ''
def restore_debug():
	for k in save_debug:
		os.environ[k] = save_debug[k] or ''

cfgs = {
	'15': {
		'tmpdir':        os.path.join(u'test',u'tmp15'),
		'wpasswd':       'Dorian-α',
		'kapasswd':      'Grok the blockchain',
		'addr_idx_list': '12,99,5-10,5,12', # 8 addresses
		'dep_generators':  {
			pwfile:        'walletgen_dfl_wallet',
			'addrs':       'addrgen_dfl_wallet',
			'rawtx':       'txcreate_dfl_wallet',
			'sigtx':       'txsign_dfl_wallet',
			'mmseed':      'export_seed_dfl_wallet',
			'del_dw_run':  'delete_dfl_wallet',
		},
		'segwit': get_segwit_bool()
	},
	'16': {
		'tmpdir':        os.path.join(u'test',u'tmp16'),
		'wpasswd':       'My changed password',
		'hash_preset':   '2',
		'dep_generators': {
			pwfile:        'passchg_dfl_wallet',
		},
		'segwit': get_segwit_bool()
	},
	'17': { 'tmpdir': os.path.join(u'test',u'tmp17') },
	'18': { 'tmpdir': os.path.join(u'test',u'tmp18') },
#	'19': { 'tmpdir': os.path.join(u'test',u'tmp19'), 'wpasswd':'abc' }, B2X

	'31': { 'tmpdir': os.path.join(u'test',u'tmp31'), # L
			'addr_idx_list':'1-2', 'segwit': False,
			'dep_generators': {'addrs':'ref_tx_addrgen1'} },
	'32': { 'tmpdir': os.path.join(u'test',u'tmp32'), # C
			'addr_idx_list':'1-2', 'segwit': False,
			'dep_generators': {'addrs':'ref_tx_addrgen2'} },
	'33': { 'tmpdir': os.path.join(u'test',u'tmp33'), # S
			'addr_idx_list':'1-2', 'segwit': True,
			'dep_generators': {'addrs':'ref_tx_addrgen3'} },
	'34': { 'tmpdir': os.path.join(u'test',u'tmp34'), # B
			'addr_idx_list':'1-2', 'segwit': True,
			'dep_generators': {'addrs':'ref_tx_addrgen4'} },

	'1': {
		'tmpdir':        os.path.join(u'test',u'tmp1'),
		'wpasswd':       u'Dorian-α',
		'kapasswd':      'Grok the blockchain',
		'addr_idx_list': '12,99,5-10,5,12', # 8 addresses
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
			hincog_fn:     u'export_incog_hidden',
			incog_id_fn:   u'export_incog_hidden',
			'akeys.mmenc': 'keyaddrgen'
		},
		'segwit': get_segwit_bool()
	},
	'2': {
		'tmpdir':        os.path.join(u'test',u'tmp2'),
		'wpasswd':       'Hodling away',
		'addr_idx_list': '37,45,3-6,22-23',  # 8 addresses
		'seed_len':      128,
		'dep_generators': {
			'mmdat':       'walletgen2',
			'addrs':       'addrgen2',
			'rawtx':         'txcreate2',
			'sigtx':         'txsign2',
			'mmwords':     'export_mnemonic2',
		},
		'segwit': get_segwit_bool()
	},
	'20': {
		'tmpdir':        os.path.join(u'test',u'tmp20'),
		'wpasswd':       'Vsize it',
		'addr_idx_list': '1-8',  # 8 addresses
		'seed_len':      256,
		'dep_generators': {
			'mmdat':       'walletgen5',
			'addrs':       'addrgen5',
			'rawtx':       'txcreate5',
			'sigtx':       'txsign5',
		},
		'segwit': get_segwit_bool()
	},
	'21': {
		'tmpdir':        os.path.join(u'test',u'tmp21'),
		'wpasswd':       'Vsize it',
		'addr_idx_list': '1-8',  # 8 addresses
		'seed_len':      256,
		'dep_generators': {
			'mmdat':       'walletgen6',
			'addrs':       'addrgen6',
			'rawtx':       'txcreate6',
			'sigtx':       'txsign6',
		},
		'segwit': get_segwit_bool()
	},
	'22': {
		'tmpdir': os.path.join(u'test',u'tmp22'),
		'parity_pidfile': 'parity.pid',
		'parity_keyfile': 'parity.devkey',
		},
	'3': {
		'tmpdir':        os.path.join(u'test',u'tmp3'),
		'wpasswd':       'Major miner',
		'addr_idx_list': '73,54,1022-1023,2-5', # 8 addresses
		'dep_generators': {
			'mmdat':       'walletgen3',
			'addrs':       'addrgen3',
			'rawtx':         'txcreate3',
			'sigtx':         'txsign3'
		},
		'segwit': get_segwit_bool()
	},
	'4': {
		'tmpdir':        os.path.join(u'test',u'tmp4'),
		'wpasswd':       'Hashrate good',
		'addr_idx_list': '63,1004,542-544,7-9', # 8 addresses
		'seed_len':      192,
		'dep_generators': {
			'mmdat':       'walletgen4',
			'mmbrain':     'walletgen4',
			'addrs':       'addrgen4',
			'rawtx':       'txcreate4',
			'sigtx':       'txsign4',
			'txdo':        'txdo4',
		},
		'bw_filename': u'brainwallet.mmbrain',
		'bw_params':   '192,1',
		'segwit': get_segwit_bool()
	},
	'14': {
		'kapasswd':      'Maxwell',
		'tmpdir':        os.path.join(u'test',u'tmp14'),
		'wpasswd':       'The Halving',
		'addr_idx_list': '61,998,502-504,7-9', # 8 addresses
		'seed_len':      256,
		'dep_generators': {
			'mmdat':       'walletgen14',
			'addrs':       'addrgen14',
			'akeys.mmenc': 'keyaddrgen14',
		},
		'segwit': get_segwit_bool()
	},
	'5': {
		'tmpdir':        os.path.join(u'test',u'tmp5'),
		'wpasswd':       'My changed password-α',
		'hash_preset':   '2',
		'dep_generators': {
			'mmdat':       'passchg',
			pwfile:        'passchg',
		},
		'segwit': get_segwit_bool()
	},
	'6': {
		'name':            'reference wallet check (128-bit)',
		'seed_len':        128,
		'seed_id':         'FE3C6545',
		'ref_bw_seed_id':  '33F10310',
		'addrfile_chk': {
			'btc': ('B230 7526 638F 38CB','A9DC 5A13 12CB 1317'),
			'ltc': ('2B23 5E97 848A B961','AEC3 E774 0B21 0202'),
		},
		'addrfile_segwit_chk': {
			'btc': ('9914 6D10 2307 F348','83C8 A6B6 ADA8 25B2'),
			'ltc': ('CC09 A190 B7DF B7CD','0425 7893 C6F1 ECA3'),
		},
		'addrfile_bech32_chk': {
			'btc': ('C529 D686 31AA ACD4','21D0 26AD 3A22 5465'),
			'ltc': ('3DFB CFCC E180 DC9D','8C72 D5C2 07E0 5F7B'),
		},
		'addrfile_compressed_chk': {
			'btc': ('95EB 8CC0 7B3B 7856','16E6 6170 154D 2202'),
			'ltc': ('35D5 8ECA 9A42 46C3','15B3 5492 D3D3 6854'),
		},
		'keyaddrfile_chk': {
			'btc': ('CF83 32FB 8A8B 08E2','1F67 B73A FF8C 5D15'),
			'ltc': ('1896 A26C 7F14 2D01','FA0E CD4E ADAF DBF4'),
		},
		'keyaddrfile_segwit_chk': {
			'btc': ('C13B F717 D4E8 CF59','BB71 175C 5416 19D8'),
			'ltc': ('054B 9794 55B4 5D82','DE85 3CF3 9636 FE2E'),
		},
		'keyaddrfile_bech32_chk': {
			'btc': ('934F 1C33 6C06 B18C','A283 5BAB 7AF3 3EA4'),
			'ltc': ('A6AD DF53 5968 7B6A','9572 43E0 A4DC 0B2E'),
		},
		'keyaddrfile_compressed_chk': {
			'btc': ('E43A FA46 5751 720A','FDEE 8E45 1C0A 02AD'),
			'ltc': ('7603 2FE3 2145 FFAD','3FE0 5A8E 5FBE FF3E'),
		},
		'passfile_chk':    'EB29 DC4F 924B 289F',
		'passfile32_chk':  '37B6 C218 2ABC 7508',
		'passfilehex_chk': '523A F547 0E69 8323',
		'wpasswd':         'reference password',
		'ref_wallet':      u'FE3C6545-D782B529[128,1].mmdat',
		'ic_wallet':       u'FE3C6545-E29303EA-5E229E30[128,1].mmincog',
		'ic_wallet_hex':   u'FE3C6545-BC4BE3F2-32586837[128,1].mmincox',

		'hic_wallet':       'FE3C6545-161E495F-BEB7548E[128,1].incog-offset123',
		'hic_wallet_old':   'FE3C6545-161E495F-9860A85B[128,1].incog-old.offset123',

		'tmpdir':        os.path.join(u'test',u'tmp6'),
		'kapasswd':      '',
		'addr_idx_list': '1010,500-501,31-33,1,33,500,1011', # 8 addresses
		'pass_idx_list': '1,4,9-11,1100',
		'dep_generators':  {
			'mmdat':       'refwalletgen1',
			pwfile:        'refwalletgen1',
			'addrs':       'refaddrgen1',
			'akeys.mmenc': 'refkeyaddrgen1'
		},
		'segwit': get_segwit_bool()
	},
	'7': {
		'name':            'reference wallet check (192-bit)',
		'seed_len':        192,
		'seed_id':         '1378FC64',
		'ref_bw_seed_id':  'CE918388',
		'addrfile_chk': {
			'btc': ('8C17 A5FA 0470 6E89','764C 66F9 7502 AAEA'),
			'ltc': ('2B77 A009 D5D0 22AD','51D1 979D 0A35 F24B'),
		},
		'addrfile_segwit_chk': {
			'btc': ('91C4 0414 89E4 2089','BF9F C67F ED22 A47B'),
			'ltc': ('8F12 FA7B 9F12 594C','2609 8494 A23C F836'),
		},
		'addrfile_bech32_chk': {
			'btc': ('2AA3 78DF B965 82EB','027B 1C1F 7FB2 D859'),
			'ltc': ('951C 8FB2 FCA5 87D1','4A5D 67E0 8210 FEF2'),
		},
		'addrfile_compressed_chk': {
			'btc': ('2615 8401 2E98 7ECA','A386 EE07 A356 906D'),
			'ltc': ('197C C48C 3C37 AB0F','8DDC 5FE3 BFF9 1226'),
		},
		'keyaddrfile_chk': {
			'btc': ('9648 5132 B98E 3AD9','1BD3 5A36 D51C 256D'),
			'ltc': ('DBD4 FAB6 7E46 CD07','8822 3FDF FEC0 6A8C'),
		},
		'keyaddrfile_segwit_chk': {
			'btc': ('C98B DF08 A3D5 204B','7E7F DF50 FE04 6F68'),
			'ltc': ('1829 7FE7 2567 CB91','BE92 D19C 7589 EF30'),
		},
		'keyaddrfile_bech32_chk': {
			'btc': ('4A6B 3762 DF30 9368','12DD 1888 36BA 85F7'),
			'ltc': ('5C12 FDD4 17AB F179','E195 B28C 59C4 C5EC'),
		},
		'keyaddrfile_compressed_chk': {
			'btc': ('6D6D 3D35 04FD B9C3','94BF 4BCF 10B2 394B'),
			'ltc': ('F5DA 9D60 6798 C4E9','7918 88DE 9096 DD7A'),
		},
		'passfile_chk':    'ADEA 0083 094D 489A',
		'passfile32_chk':  '2A28 C5C7 36EC 217A',
		'passfilehex_chk': 'B11C AC6A 1464 608D',
		'wpasswd':         'reference password',
		'ref_wallet':      u'1378FC64-6F0F9BB4[192,1].mmdat',
		'ic_wallet':       u'1378FC64-2907DE97-F980D21F[192,1].mmincog',
		'ic_wallet_hex':   u'1378FC64-4DCB5174-872806A7[192,1].mmincox',

		'hic_wallet':      u'1378FC64-B55E9958-77256FC1[192,1].incog.offset123',
		'hic_wallet_old':  u'1378FC64-B55E9958-D85FF20C[192,1].incog-old.offset123',

		'tmpdir':        os.path.join(u'test',u'tmp7'),
		'kapasswd':      '',
		'addr_idx_list': '1010,500-501,31-33,1,33,500,1011', # 8 addresses
		'pass_idx_list': '1,4,9-11,1100',
		'dep_generators':  {
			'mmdat':       'refwalletgen2',
			pwfile:       'refwalletgen2',
			'addrs':       'refaddrgen2',
			'akeys.mmenc': 'refkeyaddrgen2'
		},
		'segwit': get_segwit_bool()
	},
	'8': {
		'name':            'reference wallet check (256-bit)',
		'seed_len':        256,
		'seed_id':         '98831F3A',
		'ref_bw_seed_id':  'B48CD7FC',
		'addrfile_chk': {
			'btc': ('6FEF 6FB9 7B13 5D91','424E 4326 CFFE 5F51'),
			'ltc': ('AD52 C3FE 8924 AAF0','4EBE 2E85 E969 1B30'),
		},
		'addrfile_segwit_chk': {
			'btc': ('06C1 9C87 F25C 4EE6','072C 8B07 2730 CB7A'),
			'ltc': ('63DF E42A 0827 21C3','5DD1 D186 DBE1 59F2'),
		},
		'addrfile_bech32_chk': {
			'btc': ('9D2A D4B6 5117 F02E','0527 9C39 6C1B E39A'),
			'ltc': ('FF1C 7939 5967 AB82','ED3D 8AA4 BED4 0B40'),
		},
		'addrfile_compressed_chk': {
			'btc': ('A33C 4FDE F515 F5BC','6C48 AA57 2056 C8C8'),
			'ltc': ('3FC0 8F03 C2D6 BD19','4C0A 49B6 2DD1 1BE0'),
		},
		'keyaddrfile_chk': {
			'btc': ('9F2D D781 1812 8BAD','88CC 5120 9A91 22C2'),
			'ltc': ('B804 978A 8796 3ED4','98B5 AC35 F334 0398'),
		},
		'keyaddrfile_segwit_chk': {
			'btc': ('A447 12C2 DD14 5A9B','C770 7391 C415 21F9'),
			'ltc': ('E8A3 9F6E E164 A521','D3D5 BFDD F5D5 20BD'),
		},
		'keyaddrfile_bech32_chk': {
			'btc': ('D0DD BDE3 87BE 15AE','7552 D70C AAB8 DEAA'),
			'ltc': ('74A0 7DD5 963B 6326','2CDA A007 4B9F E9A5'),
		},
		'keyaddrfile_compressed_chk': {
			'btc': ('420A 8EB5 A9E2 7814','F43A CB4A 81F3 F735'),
			'ltc': ('8D1C 781F EB7F 44BC','05F3 5C68 FD31 FCEF'),
		},
		'passfile_chk':    '2D6D 8FBA 422E 1315',
		'passfile32_chk':  'F6C1 CDFB 97D9 FCAE',
		'passfilehex_chk': 'BD4F A0AC 8628 4BE4',
		'wpasswd':         'reference password',
		'ref_wallet':      u'98831F3A-{}[256,1].mmdat'.format(('27F2BF93','E2687906')[g.testnet]),
		'ref_addrfile':    u'98831F3A{}[1,31-33,500-501,1010-1011]{}.addrs',
		'ref_segwitaddrfile':u'98831F3A{}-S[1,31-33,500-501,1010-1011]{}.addrs',
		'ref_bech32addrfile':u'98831F3A{}-B[1,31-33,500-501,1010-1011]{}.addrs',
		'ref_keyaddrfile': u'98831F3A{}[1,31-33,500-501,1010-1011]{}.akeys.mmenc',
		'ref_passwdfile':  u'98831F3A-фубар@crypto.org-b58-20[1,4,9-11,1100].pws',
		'ref_addrfile_chksum': {
			'btc': ('6FEF 6FB9 7B13 5D91','424E 4326 CFFE 5F51'),
			'ltc': ('AD52 C3FE 8924 AAF0','4EBE 2E85 E969 1B30'),
		},
		'ref_segwitaddrfile_chksum': {
			'btc': ('06C1 9C87 F25C 4EE6','072C 8B07 2730 CB7A'),
			'ltc': ('63DF E42A 0827 21C3','5DD1 D186 DBE1 59F2'),
		},
		'ref_bech32addrfile_chksum': {
			'btc': ('9D2A D4B6 5117 F02E','0527 9C39 6C1B E39A'),
			'ltc': ('FF1C 7939 5967 AB82','ED3D 8AA4 BED4 0B40'),
		},
		'ref_keyaddrfile_chksum': {
			'btc': ('9F2D D781 1812 8BAD','88CC 5120 9A91 22C2'),
			'ltc': ('B804 978A 8796 3ED4','98B5 AC35 F334 0398'),
		},
		'ref_addrfile_chksum_zec': '903E 7225 DD86 6E01',
		'ref_addrfile_chksum_zec_z': '9C7A 72DC 3D4A B3AF',
		'ref_addrfile_chksum_xmr': '4369 0253 AC2C 0E38',
		'ref_addrfile_chksum_dash':'FBC1 6B6A 0988 4403',
		'ref_addrfile_chksum_eth': 'E554 076E 7AF6 66A3',
		'ref_addrfile_chksum_etc': 'E97A D796 B495 E8BC',
		'ref_keyaddrfile_chksum_zec': 'F05A 5A5C 0C8E 2617',
		'ref_keyaddrfile_chksum_zec_z': '6B87 9B2D 0D8D 8D1E',
		'ref_keyaddrfile_chksum_xmr': 'E0D7 9612 3D67 404A',
		'ref_keyaddrfile_chksum_dash': 'E83D 2C63 FEA2 4142',
		'ref_keyaddrfile_chksum_eth': 'E400 70D9 0AE3 C7C2',
		'ref_keyaddrfile_chksum_etc': 'EF49 967D BD6C FE45',
		'ref_passwdfile_chksum':   'A983 DAB9 5514 27FB',
		'ref_tx_file': {
			'btc': ('0B8D5A[15.31789,14,tl=1320969600].rawtx',
					'0C7115[15.86255,14,tl=1320969600].testnet.rawtx'),
			'bch': ('460D4D-BCH[10.19764,tl=1320969600].rawtx',
					'359FD5-BCH[6.68868,tl=1320969600].testnet.rawtx'),
			'ltc': ('AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx',
					'A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx'),
			'eth': ('88FEFD-ETH[23.45495,40000].rawtx',
					'B472BD-ETH[23.45495,40000].testnet.rawtx'),
			'erc20': ('5881D2-MM1[1.23456,50000].rawtx',
					'6BDB25-MM1[1.23456,50000].testnet.rawtx'),
			'etc': ('ED3848-ETC[1.2345,40000].rawtx','')
		},
		'ic_wallet':       u'98831F3A-5482381C-18460FB1[256,1].mmincog',
		'ic_wallet_hex':   u'98831F3A-1630A9F2-870376A9[256,1].mmincox',

		'hic_wallet':       u'98831F3A-F59B07A0-559CEF19[256,1].incog.offset123',
		'hic_wallet_old':   u'98831F3A-F59B07A0-848535F3[256,1].incog-old.offset123',

		'tmpdir':        os.path.join(u'test',u'tmp8'),
		'kapasswd':      '',
		'addr_idx_list': '1010,500-501,31-33,1,33,500,1011', # 8 addresses
		'pass_idx_list': '1,4,9-11,1100',

		'dep_generators':  {
			'mmdat':       'refwalletgen3',
			pwfile:       'refwalletgen3',
			'addrs':       'refaddrgen3',
			'akeys.mmenc': 'refkeyaddrgen3'
		},
		'segwit': get_segwit_bool()
	},
	'9': {
		'tmpdir':        os.path.join(u'test',u'tmp9'),
		'tool_enc_infn':      'tool_encrypt.in',
#		'tool_enc_ref_infn':  'tool_encrypt_ref.in',
		'wpasswd':         'reference password',
		'dep_generators': {
			'tool_encrypt.in':            'tool_encrypt',
			'tool_encrypt.in.mmenc':      'tool_encrypt',
#			'tool_encrypt_ref.in':        'tool_encrypt_ref',
#			'tool_encrypt_ref.in.mmenc':  'tool_encrypt_ref',
		},
	},
}

dfl_words = os.path.join(ref_dir,cfgs['8']['seed_id']+'.mmwords')

# The Parity dev address with lots of coins.  Create with "ethkey -b info ''":
eth_addr = '00a329c0648769a73afac7f9381e08fb43dbea72'
eth_key = '4d5db4107d237df6a3d58ee5f70ae63d73d7658d4026f2eefd2f204c81682cb7'
eth_burn_addr = 'deadbeef'*5
eth_amt1 = '999999.12345689012345678'
eth_amt2 = '888.111122223333444455'

def eth_args():
	assert g.coin in ('ETH','ETC'),'for ethdev tests, --coin must be set to either ETH or ETC'
	return [u'--outdir={}'.format(cfgs['22']['tmpdir']),'--rpc-port=8549','--quiet']

from copy import deepcopy
for a,b in (('6','11'),('7','12'),('8','13')):
	cfgs[b] = deepcopy(cfgs[a])
	cfgs[b]['tmpdir'] = os.path.join(u'test',u'tmp'+b)

if g.debug_utf8:
	for k in cfgs: cfgs[k]['tmpdir'] += u'-α'

from collections import OrderedDict

cmd_group = OrderedDict()

cmd_group['help'] = OrderedDict([
#     test               description                  depends
	['helpscreens',     (1,'help screens',             [])],
	['longhelpscreens', (1,'help screens (--longhelp)',[])],
])

cmd_group['dfl_wallet'] = OrderedDict([
	['walletgen_dfl_wallet', (15,'wallet generation (default wallet)',[[[],15]])],
	['export_seed_dfl_wallet',(15,'seed export to mmseed format (default wallet)',[[[pwfile],15]])],
	['addrgen_dfl_wallet',(15,'address generation (default wallet)',[[[pwfile],15]])],
	['txcreate_dfl_wallet',(15,'transaction creation (default wallet)',[[['addrs'],15]])],
	['txsign_dfl_wallet',(15,'transaction signing (default wallet)',[[['rawtx',pwfile],15]])],
	['passchg_dfl_wallet',(16,'password, label and hash preset change (default wallet)',[[[pwfile],15]])],
	['walletchk_newpass_dfl_wallet',(16,'wallet check with new pw, label and hash preset',[[[pwfile],16]])],
	['delete_dfl_wallet',(15,'delete default wallet',[[[pwfile],15]])],
])

cmd_group['main'] = OrderedDict([
	['walletgen',       (1,'wallet generation',        [[['del_dw_run'],15]])],
#	['walletchk',       (1,'wallet check',             [[['mmdat'],1]])],
	['passchg',         (5,'password, label and hash preset change',[[['mmdat',pwfile],1]])],
	['passchg_keeplabel',(5,'password, label and hash preset change (keep label)',[[['mmdat',pwfile],1]])],
	['passchg_usrlabel',(5,'password, label and hash preset change (interactive label)',[[['mmdat',pwfile],1]])],
	['walletchk_newpass',(5,'wallet check with new pw, label and hash preset',[[['mmdat',pwfile],5]])],
	['addrgen',         (1,'address generation',       [[['mmdat',pwfile],1]])],
	['txcreate',        (1,'transaction creation',     [[['addrs'],1]])],
	['txbump',          (1,'transaction fee bumping (no send)',[[['rawtx'],1]])],
	['txsign',          (1,'transaction signing',      [[['mmdat','rawtx',pwfile,'txbump'],1]])],
	['txsend',          (1,'transaction sending',      [[['sigtx'],1]])],
	# txdo must go after txsign
	['txdo',            (1,'online transaction',       [[['sigtx','mmdat'],1]])],

	['export_hex',      (1,'seed export to hexadecimal format',  [[['mmdat'],1]])],
	['export_seed',     (1,'seed export to mmseed format',   [[['mmdat'],1]])],
	['export_mnemonic', (1,'seed export to mmwords format',  [[['mmdat'],1]])],
	['export_incog',    (1,'seed export to mmincog format',  [[['mmdat'],1]])],
	['export_incog_hex',(1,'seed export to mmincog hex format', [[['mmdat'],1]])],
	['export_incog_hidden',(1,'seed export to hidden mmincog format', [[['mmdat'],1]])],

	['addrgen_hex',     (1,'address generation from mmhex file', [[['mmhex','addrs'],1]])],
	['addrgen_seed',    (1,'address generation from mmseed file', [[['mmseed','addrs'],1]])],
	['addrgen_mnemonic',(1,'address generation from mmwords file',[[['mmwords','addrs'],1]])],
	['addrgen_incog',   (1,'address generation from mmincog file',[[['mmincog','addrs'],1]])],
	['addrgen_incog_hex',(1,'address generation from mmincog hex file',[[['mmincox','addrs'],1]])],
	['addrgen_incog_hidden',(1,'address generation from hidden mmincog file', [[[hincog_fn,'addrs'],1]])],

	['keyaddrgen',    (1,'key-address file generation', [[['mmdat',pwfile],1]])],
	['txsign_keyaddr',(1,'transaction signing with key-address file', [[['akeys.mmenc','rawtx'],1]])],

	['txcreate_ni',   (1,'transaction creation (non-interactive)',     [[['addrs'],1]])],

	['walletgen2',(2,'wallet generation (2), 128-bit seed',     [[['del_dw_run'],15]])],
	['addrgen2',  (2,'address generation (2)',    [[['mmdat'],2]])],
	['txcreate2', (2,'transaction creation (2)',  [[['addrs'],2]])],
	['txsign2',   (2,'transaction signing, two transactions',[[['mmdat','rawtx'],1],[['mmdat','rawtx'],2]])],
	['export_mnemonic2', (2,'seed export to mmwords format (2)',[[['mmdat'],2]])],

	['walletgen3',(3,'wallet generation (3)',                  [[['del_dw_run'],15]])],
	['addrgen3',  (3,'address generation (3)',                 [[['mmdat'],3]])],
	['txcreate3', (3,'tx creation with inputs and outputs from two wallets', [[['addrs'],1],[['addrs'],3]])],
	['txsign3',   (3,'tx signing with inputs and outputs from two wallets',[[['mmdat'],1],[['mmdat','rawtx'],3]])],

	['walletgen14', (14,'wallet generation (14)',        [[['del_dw_run'],15]],14)],
	['addrgen14',   (14,'address generation (14)',        [[['mmdat'],14]])],
	['keyaddrgen14',(14,'key-address file generation (14)', [[['mmdat'],14]],14)],
	['walletgen4',(4,'wallet generation (4) (brainwallet)',    [[['del_dw_run'],15]])],
	['addrgen4',  (4,'address generation (4)',                 [[['mmdat'],4]])],
	['txcreate4', (4,'tx creation with inputs and outputs from four seed sources, key-address file and non-MMGen inputs and outputs', [[['addrs'],1],[['addrs'],2],[['addrs'],3],[['addrs'],4],[['addrs','akeys.mmenc'],14]])],
	['txsign4',   (4,'tx signing with inputs and outputs from incog file, mnemonic file, wallet, brainwallet, key-address file and non-MMGen inputs and outputs', [[['mmincog'],1],[['mmwords'],2],[['mmdat'],3],[['mmbrain','rawtx'],4],[['akeys.mmenc'],14]])],
	['txdo4', (4,'tx creation,signing and sending with inputs and outputs from four seed sources, key-address file and non-MMGen inputs and outputs', [[['addrs'],1],[['addrs'],2],[['addrs'],3],[['addrs'],4],[['addrs','akeys.mmenc'],14],[['mmincog'],1],[['mmwords'],2],[['mmdat'],3],[['mmbrain','rawtx'],4],[['akeys.mmenc'],14]])], # must go after txsign4
	['txbump4', (4,'tx fee bump + send with inputs and outputs from four seed sources, key-address file and non-MMGen inputs and outputs', [[['akeys.mmenc'],14],[['mmincog'],1],[['mmwords'],2],[['mmdat'],3],[['akeys.mmenc'],14],[['mmbrain','sigtx','mmdat','txdo'],4]])], # must go after txsign4

	['walletgen5',(20,'wallet generation (5)',                   [[['del_dw_run'],15]],20)],
	['addrgen5',  (20,'address generation (5)',                  [[['mmdat'],20]])],
	['txcreate5', (20,'transaction creation with bad vsize (5)', [[['addrs'],20]])],
	['txsign5',   (20,'transaction signing with bad vsize',      [[['mmdat','rawtx'],20]])],
	['walletgen6',(21,'wallet generation (6)',                   [[['del_dw_run'],15]],21)],
	['addrgen6',  (21,'address generation (6)',                  [[['mmdat'],21]])],
	['txcreate6', (21,'transaction creation with corrected vsize (6)', [[['addrs'],21]])],
	['txsign6',   (21,'transaction signing with corrected vsize',      [[['mmdat','rawtx'],21]])],
])

cmd_group['tool'] = OrderedDict([
	['tool_encrypt',     (9,"'mmgen-tool encrypt' (random data)",     [])],
	['tool_decrypt',     (9,"'mmgen-tool decrypt' (random data)", [[[cfgs['9']['tool_enc_infn'],cfgs['9']['tool_enc_infn']+'.mmenc'],9]])],
#	['tool_encrypt_ref', (9,"'mmgen-tool encrypt' (reference text)",  [])],
	['tool_find_incog_data', (9,"'mmgen-tool find_incog_data'", [[[hincog_fn],1],[[incog_id_fn],1]])],
#	['pywallet', (9,"'mmgen-pywallet'", [])],
])

# generated reference data
cmd_group['ref'] = (
	# reading
	('ref_wallet_chk', ([],'saved reference wallet')),
	('ref_seed_chk',   ([],'saved seed file')),
	('ref_hex_chk',    ([],'saved mmhex file')),
	('ref_mn_chk',     ([],'saved mnemonic file')),
	('ref_hincog_chk', ([],'saved hidden incog reference wallet')),
	('ref_brain_chk',  ([],'saved brainwallet')),
	# generating new reference ('abc' brainwallet) files:
	('refwalletgen',   ([],'gen new refwallet')),
	('refaddrgen',     (['mmdat',pwfile],'new refwallet addr chksum')),
	('refkeyaddrgen',  (['mmdat',pwfile],'new refwallet key-addr chksum')),
	('refaddrgen_compressed',    (['mmdat',pwfile],'new refwallet addr chksum (compressed)')),
	('refkeyaddrgen_compressed', (['mmdat',pwfile],'new refwallet key-addr chksum (compressed)')),
	('refpasswdgen',   (['mmdat',pwfile],'new refwallet passwd file chksum')),
	('ref_b32passwdgen',(['mmdat',pwfile],'new refwallet passwd file chksum (base32)')),
	('ref_hexpasswdgen',(['mmdat',pwfile],'new refwallet passwd file chksum (base32)')),
)

# reference files
cmd_group['ref_files'] = (
	('ref_addrfile_chk',   'saved reference address file'),
	('ref_segwitaddrfile_chk','saved reference address file (segwit)'),
	('ref_bech32addrfile_chk','saved reference address file (bech32)'),
	('ref_keyaddrfile_chk','saved reference key-address file'),
	('ref_passwdfile_chk', 'saved reference password file'),
#	Create the fake inputs:
#	('txcreate8',          'transaction creation (8)'),
	('ref_tx_chk',         'saved reference tx file'),
	('ref_brain_chk_spc3', 'saved brainwallet (non-standard spacing)'),
	('ref_tool_decrypt',   'decryption of saved MMGen-encrypted file'),
)

# mmgen-walletconv:
cmd_group['conv_in'] = ( # reading
	('ref_wallet_conv',    'conversion of saved reference wallet'),
	('ref_mn_conv',        'conversion of saved mnemonic'),
	('ref_seed_conv',      'conversion of saved seed file'),
	('ref_hex_conv',       'conversion of saved hexadecimal seed file'),
	('ref_brain_conv',     'conversion of ref brainwallet'),
	('ref_incog_conv',     'conversion of saved incog wallet'),
	('ref_incox_conv',     'conversion of saved hex incog wallet'),
	('ref_hincog_conv',    'conversion of saved hidden incog wallet'),
	('ref_hincog_conv_old','conversion of saved hidden incog wallet (old format)')
)

cmd_group['conv_out'] = ( # writing
	('ref_wallet_conv_out', 'ref seed conversion to wallet'),
	('ref_mn_conv_out',     'ref seed conversion to mnemonic'),
	('ref_hex_conv_out',    'ref seed conversion to hex seed'),
	('ref_seed_conv_out',   'ref seed conversion to seed'),
	('ref_incog_conv_out',  'ref seed conversion to incog data'),
	('ref_incox_conv_out',  'ref seed conversion to hex incog data'),
	('ref_hincog_conv_out', 'ref seed conversion to hidden incog data')
)

cmd_group['regtest'] = (
	('regtest_setup',              'regtest (Bob and Alice) mode setup'),
	('regtest_walletgen_bob',      'wallet generation (Bob)'),
	('regtest_walletgen_alice',    'wallet generation (Alice)'),
	('regtest_addrgen_bob',        'address generation (Bob)'),
	('regtest_addrgen_alice',      'address generation (Alice)'),
	('regtest_addrimport_bob',     "importing Bob's addresses"),
	('regtest_addrimport_alice',   "importing Alice's addresses"),
	('regtest_fund_bob',           "funding Bob's wallet"),
	('regtest_fund_alice',         "funding Alice's wallet"),
	('regtest_bob_bal1',           "Bob's balance"),
	('regtest_bob_add_label',      "adding a 40-character UTF-8 encoded label"),
	('regtest_bob_split1',         "splitting Bob's funds"),
	('regtest_generate',           'mining a block'),
	('regtest_bob_bal2',           "Bob's balance"),
	('regtest_bob_rbf_send',       'sending funds to Alice (RBF)'),
	('regtest_get_mempool1',       'mempool (before RBF bump)'),
	('regtest_bob_rbf_bump',       'bumping RBF transaction'),
	('regtest_get_mempool2',       'mempool (after RBF bump)'),
	('regtest_generate',           'mining a block'),
	('regtest_bob_bal3',           "Bob's balance"),
	('regtest_bob_pre_import',     'sending to non-imported address'),
	('regtest_generate',           'mining a block'),
	('regtest_bob_import_addr',    'importing non-MMGen address with --rescan'),
	('regtest_bob_bal4',           "Bob's balance (after import with rescan)"),
	('regtest_bob_import_list',    'importing flat address list'),
	('regtest_bob_split2',         "splitting Bob's funds"),
	('regtest_generate',           'mining a block'),
	('regtest_bob_bal5',           "Bob's balance"),
	('regtest_bob_bal5_getbalance',"Bob's balance"),
	('regtest_bob_send_non_mmgen', 'sending funds to Alice (from non-MMGen addrs)'),
	('regtest_generate',           'mining a block'),
	('regtest_alice_add_label1',   'adding a label'),
	('regtest_alice_chk_label1',   'the label'),
	('regtest_alice_add_label2',   'adding a label'),
	('regtest_alice_chk_label2',   'the label'),
	('regtest_alice_edit_label1',  'editing a label'),
	('regtest_alice_chk_label3',   'the label'),
	('regtest_alice_remove_label1','removing a label'),
	('regtest_alice_chk_label4',   'the label'),
	('regtest_alice_add_label_coinaddr','adding a label using the coin address'),
	('regtest_alice_chk_label_coinaddr','the label'),
	('regtest_alice_add_label_badaddr1','adding a label with invalid address'),
	('regtest_alice_add_label_badaddr2','adding a label with invalid address for this chain'),
	('regtest_alice_add_label_badaddr3','adding a label with wrong MMGen address'),
	('regtest_alice_add_label_badaddr4','adding a label with wrong coin address'),
	('regtest_alice_add_label_rpcfail','RPC failure code'),
	('regtest_alice_send_estimatefee','tx creation with no fee on command line'),
	('regtest_generate',           'mining a block'),
	('regtest_bob_bal6',            "Bob's balance"),
	('regtest_bob_alice_bal',      "Bob and Alice's balances"),
	('regtest_alice_bal2',         "Alice's balance"),
	('regtest_stop',               'stopping regtest daemon'),
)

cmd_group['regtest_split'] = (
	('regtest_split_setup',        'regtest forking scenario setup'),
	('regtest_walletgen_bob',      "generating Bob's wallet"),
	('regtest_addrgen_bob',        "generating Bob's addresses"),
	('regtest_addrimport_bob',     "importing Bob's addresses"),
	('regtest_fund_bob',           "funding Bob's wallet"),
	('regtest_split_fork',         'regtest split fork'),
	('regtest_split_start_btc',    'start regtest daemon (BTC)'),
	('regtest_split_start_b2x',    'start regtest daemon (B2X)'),
	('regtest_split_gen_btc',      'mining a block (BTC)'),
	('regtest_split_gen_b2x',      'mining 100 blocks (B2X)'),
	('regtest_split_do_split',     'creating coin splitting transactions'),
	('regtest_split_sign_b2x',     'signing B2X split transaction'),
	('regtest_split_sign_btc',     'signing BTC split transaction'),
	('regtest_split_send_b2x',     'sending B2X split transaction'),
	('regtest_split_send_btc',     'sending BTC split transaction'),
	('regtest_split_gen_btc',      'mining a block (BTC)'),
	('regtest_split_gen_b2x2',     'mining a block (B2X)'),
	('regtest_split_txdo_timelock_bad_btc', 'sending transaction with bad locktime (BTC)'),
	('regtest_split_txdo_timelock_good_btc','sending transaction with good locktime (BTC)'),
	('regtest_split_txdo_timelock_bad_b2x', 'sending transaction with bad locktime (B2X)'),
	('regtest_split_txdo_timelock_good_b2x','sending transaction with good locktime (B2X)'),
)

cmd_group['ethdev'] = (
	('ethdev_setup',               'Ethereum Parity dev mode tests for coin {} (start parity)'.format(g.coin)),
	('ethdev_addrgen',             'generating addresses'),
	('ethdev_addrimport',          'importing addresses'),
	('ethdev_addrimport_dev_addr', "importing Parity dev address 'Ox00a329c..'"),

	('ethdev_txcreate1',           'creating a transaction (spend from dev address)'),
	('ethdev_txsign1',             'signing the transaction'),
	('ethdev_txsign1_ni',          'signing the transaction (non-interactive)'),
	('ethdev_txsend1',             'sending the transaction'),

	('ethdev_txcreate2',           'creating a transaction (spend to address 11)'),
	('ethdev_txsign2',             'signing the transaction'),
	('ethdev_txsend2',             'sending the transaction'),

	('ethdev_txcreate3',           'creating a transaction (spend to address 21)'),
	('ethdev_txsign3',             'signing the transaction'),
	('ethdev_txsend3',             'sending the transaction'),

	('ethdev_tx_status1',          'getting the transaction status'),

	('ethdev_txcreate4',           'creating a transaction (spend from MMGen address, low TX fee)'),
	('ethdev_txbump',              'bumping the transaction fee'),

	('ethdev_txsign4',             'signing the transaction'),
	('ethdev_txsend4',             'sending the transaction'),

	('ethdev_txcreate5',           'creating a transaction (fund burn address)'),
	('ethdev_txsign5',             'signing the transaction'),
	('ethdev_txsend5',             'sending the transaction'),

	('ethdev_addrimport_burn_addr',"importing burn address"),

	('ethdev_bal1',                'the balance'),

	('ethdev_add_label',           'adding a UTF-8 label'),
	('ethdev_chk_label',           'the label'),
	('ethdev_remove_label',        'removing the label'),

	('ethdev_token_compile1',       'compiling ERC20 token #1'),

	('ethdev_token_deploy1a',       'deploying ERC20 token #1 (SafeMath)'),
	('ethdev_token_deploy1b',       'deploying ERC20 token #1 (Owned)'),
	('ethdev_token_deploy1c',       'deploying ERC20 token #1 (Token)'),

	('ethdev_tx_status2',           'getting the transaction status'),

	('ethdev_token_compile2',       'compiling ERC20 token #2'),

	('ethdev_token_deploy2a',       'deploying ERC20 token #2 (SafeMath)'),
	('ethdev_token_deploy2b',       'deploying ERC20 token #2 (Owned)'),
	('ethdev_token_deploy2c',       'deploying ERC20 token #2 (Token)'),

	('ethdev_contract_deploy',      'deploying contract (create,sign,send)'),

	('ethdev_token_transfer_funds','transferring token funds from dev to user'),
	('ethdev_token_addrgen',       'generating token addresses'),
	('ethdev_token_addrimport',    'importing token addresses'),

	('ethdev_token_txcreate1',     'creating a token transaction'),
	('ethdev_token_txsign1',       'signing the transaction'),
	('ethdev_token_txsend1',       'sending the transaction'),

	('ethdev_token_twview1',       'viewing token tracking wallet'),

	('ethdev_token_txcreate2',     'creating a token transaction (to burn address)'),
	('ethdev_token_txbump',        'bumping the transaction fee'),

	('ethdev_token_txsign2',       'signing the transaction'),
	('ethdev_token_txsend2',       'sending the transaction'),

	('ethdev_del_dev_addr',        "deleting the dev address"),

	('ethdev_bal2',                'the {} balance'.format(g.coin)),
	('ethdev_bal2_getbalance',     'the {} balance (getbalance)'.format(g.coin)),

	('ethdev_addrimport_token_burn_addr',"importing the token burn address"),

	('ethdev_token_bal1',          'the token balance'),
	('ethdev_token_bal_getbalance','the token balance (getbalance)'),

	('ethdev_txcreate_noamt',     'creating a transaction (full amount send)'),
	('ethdev_txsign_noamt',       'signing the transaction'),
	('ethdev_txsend_noamt',       'sending the transaction'),

	('ethdev_token_bal2',          'the token balance'),
	('ethdev_bal3',                'the {} balance'.format(g.coin)),

	('ethdev_token_txcreate_noamt', 'creating a token transaction (full amount send)'),
	('ethdev_token_txsign_noamt',   'signing the transaction'),
	('ethdev_token_txsend_noamt',   'sending the transaction'),

	('ethdev_token_bal3',          'the token balance'),

#	('ethdev_stop',                'stopping parity'),
)

cmd_group['autosign'] = (
	('autosign', 'transaction autosigning (BTC,BCH,LTC,ETH,ETC)'),
)

cmd_group['ref_alt'] = (
	('ref_addrfile_gen_eth',  'generate address file (ETH)'),
	('ref_addrfile_gen_etc',  'generate address file (ETC)'),
	('ref_addrfile_gen_dash', 'generate address file (DASH)'),
	('ref_addrfile_gen_zec',  'generate address file (ZEC-T)'),
	('ref_addrfile_gen_zec_z','generate address file (ZEC-Z)'),
	('ref_addrfile_gen_xmr',  'generate address file (XMR)'),

	('ref_keyaddrfile_gen_eth',  'generate key-address file (ETH)'),
	('ref_keyaddrfile_gen_etc',  'generate key-address file (ETC)'),
	('ref_keyaddrfile_gen_dash', 'generate key-address file (DASH)'),
	('ref_keyaddrfile_gen_zec',  'generate key-address file (ZEC-T)'),
	('ref_keyaddrfile_gen_zec_z','generate key-address file (ZEC-Z)'),
	('ref_keyaddrfile_gen_xmr',  'generate key-address file (XMR)'),

	('ref_addrfile_chk_eth', 'reference address file (ETH)'),
	('ref_addrfile_chk_etc', 'reference address file (ETC)'),
	('ref_addrfile_chk_dash','reference address file (DASH)'),
	('ref_addrfile_chk_zec', 'reference address file (ZEC-T)'),
	('ref_addrfile_chk_zec_z','reference address file (ZEC-Z)'),
	('ref_addrfile_chk_xmr', 'reference address file (XMR)'),

	('ref_keyaddrfile_chk_eth', 'reference key-address file (ETH)'),
	('ref_keyaddrfile_chk_etc', 'reference key-address file (ETC)'),
	('ref_keyaddrfile_chk_dash','reference key-address file (DASH)'),
	('ref_keyaddrfile_chk_zec', 'reference key-address file (ZEC-T)'),
	('ref_keyaddrfile_chk_zec_z','reference key-address file (ZEC-Z)'),
	('ref_keyaddrfile_chk_xmr', 'reference key-address file (XMR)'),
)

# undocumented admin cmds - precede with 'admin'
cmd_group_admin = OrderedDict()
cmd_group_admin['create_ref_tx'] = OrderedDict([
	['ref_tx_addrgen1', (31,'address generation (legacy)', [[[],1]])],
	['ref_tx_addrgen2', (32,'address generation (compressed)', [[[],1]])],
	['ref_tx_addrgen3', (33,'address generation (segwit)', [[[],1]])],
	['ref_tx_addrgen4', (34,'address generation (bech32)', [[[],1]])],
	['ref_tx_txcreate', (31,'transaction creation', [[['addrs'],31],[['addrs'],32],[['addrs'],33],[['addrs'],34]])],
])
cmd_list_admin = OrderedDict()
for k in cmd_group_admin: cmd_list_admin[k] = []

cmd_data_admin = OrderedDict()
for k,v in [('create_ref_tx',('reference transaction creation',[31,32,33,34]))]:
	cmd_data_admin['info_'+k] = v
	for i in cmd_group_admin[k]:
		cmd_list_admin[k].append(i)
		cmd_data_admin[i] = cmd_group_admin[k][i]

cmd_data_admin['info_create_ref_tx'] = 'create reference tx',[8]

cmd_list = OrderedDict()
for k in cmd_group: cmd_list[k] = []

cmd_data = OrderedDict()
for k,v in (
		('help', ('help screens',[])),
		('dfl_wallet', ('basic operations with default wallet',[15,16])),
		('main', ('basic operations',[1,2,3,4,5,6,15,16])),
		('tool', ('tools',[9]))
	):
	cmd_data['info_'+k] = v
	for i in cmd_group[k]:
		cmd_list[k].append(i)
		cmd_data[i] = cmd_group[k][i]

cmd_data['info_ref'] = 'generated reference data',[6,7,8]
for a,b in cmd_group['ref']:
	for i,j in ((1,128),(2,192),(3,256)):
		k = a+str(i)
		cmd_list['ref'].append(k)
		cmd_data[k] = (5+i,'{} ({}-bit)'.format(b[1],j),[[b[0],5+i]])

cmd_data['info_ref_files'] = 'reference files',[8]
for a,b in cmd_group['ref_files']:
	cmd_list['ref_files'].append(a)
	cmd_data[a] = (8,b,[[[],8]])

cmd_data['info_conv_in'] = 'wallet conversion from reference data',[11,12,13]
for a,b in cmd_group['conv_in']:
	for i,j in ((1,128),(2,192),(3,256)):
		k = a+str(i)
		cmd_list['conv_in'].append(k)
		cmd_data[k] = (10+i,'{} ({}-bit)'.format(b,j),[[[],10+i]])

cmd_data['info_conv_out'] = 'wallet conversion to reference data',[11,12,13]
for a,b in cmd_group['conv_out']:
	for i,j in ((1,128),(2,192),(3,256)):
		k = a+str(i)
		cmd_list['conv_out'].append(k)
		cmd_data[k] = (10+i,'{} ({}-bit)'.format(b,j),[[[],10+i]])

cmd_data['info_regtest'] = 'regtest mode',[17]
for a,b in cmd_group['regtest']:
	cmd_list['regtest'].append(a)
	cmd_data[a] = (17,b,[[[],17]])

cmd_data['info_ethdev'] = 'Ethereum tracking wallet and transaction ops',[22]
for a,b in cmd_group['ethdev']:
	cmd_list['ethdev'].append(a)
	cmd_data[a] = (22,b,[[[],22]])

cmd_data['info_autosign'] = 'autosign',[18]
for a,b in cmd_group['autosign']:
	cmd_list['autosign'].append(a)
	cmd_data[a] = (18,b,[[[],18]])

cmd_data['info_ref_alt'] = 'altcoin reference files',[8]
for a,b in cmd_group['ref_alt']:
	cmd_list['ref_alt'].append(a)
	cmd_data[a] = (8,b,[[[],8]])

utils = {
	'check_deps': 'check dependencies for specified command',
	'clean':      'clean specified tmp dir(s) 1,2,3,4,5 or 6 (no arg = all dirs)',
}

addrs_per_wallet = 8

meta_cmds = OrderedDict([
	['gen',  ('walletgen','addrgen')],
	['pass', ('passchg','walletchk_newpass')],
	['tx',   ('txcreate','txsign','txsend')],
	['export', [k for k in cmd_data if k[:7] == 'export_' and cmd_data[k][0] == 1]],
	['gen_sp', [k for k in cmd_data if k[:8] == 'addrgen_' and cmd_data[k][0] == 1]],
	['online', ('keyaddrgen','txsign_keyaddr')],
	['2', [k for k in cmd_data if cmd_data[k][0] == 2]],
	['3', [k for k in cmd_data if cmd_data[k][0] == 3]],
	['4', [k for k in cmd_data if cmd_data[k][0] == 4]],
	['5', [k for k in cmd_data if cmd_data[k][0] == 20]],
	['6', [k for k in cmd_data if cmd_data[k][0] == 21]],

	['ref1', [c[0]+'1' for c in cmd_group['ref']]],
	['ref2', [c[0]+'2' for c in cmd_group['ref']]],
	['ref3', [c[0]+'3' for c in cmd_group['ref']]],

	['conv_in1', [c[0]+'1' for c in cmd_group['conv_in']]],
	['conv_in2', [c[0]+'2' for c in cmd_group['conv_in']]],
	['conv_in3', [c[0]+'3' for c in cmd_group['conv_in']]],

	['conv_out1', [c[0]+'1' for c in cmd_group['conv_out']]],
	['conv_out2', [c[0]+'2' for c in cmd_group['conv_out']]],
	['conv_out3', [c[0]+'3' for c in cmd_group['conv_out']]],
])

del cmd_group

if opt.profile: opt.names = True
if opt.resume: opt.skip_deps = True

log_fd = None
if opt.log:
	log_fd = open(log_file,'a')
	log_fd.write('\nLog started: {}\n'.format(make_timestr()))

usr_rand_chars = (5,30)[bool(opt.usr_random)]
usr_rand_arg = '-r{}'.format(usr_rand_chars)
cmd_total = 0

# Disable color in spawned scripts so we can parse their output
os.environ['MMGEN_DISABLE_COLOR'] = '1'
os.environ['MMGEN_NO_LICENSE'] = '1'
os.environ['MMGEN_MIN_URANDCHARS'] = '3'
os.environ['MMGEN_BOGUS_SEND'] = '1'

def get_segwit_arg(cfg):
	return ['--type='+('segwit','bech32')[bool(opt.bech32)]] if cfg['segwit'] else []

# Tell spawned programs they're running in the test suite
os.environ['MMGEN_TEST_SUITE'] = '1'

def imsg(s): sys.stderr.write(s+'\n') # never gets redefined

if opt.exact_output:
	def msg(s): pass
	vmsg = vmsg_r = msg_r = msg
else:
	def msg(s): sys.stderr.write(s+'\n')
	def vmsg(s):
		if opt.verbose: sys.stderr.write(s+'\n')
	def msg_r(s): sys.stderr.write(s)
	def vmsg_r(s):
		if opt.verbose: sys.stderr.write(s)

stderr_save = sys.stderr

def silence():
	if not (opt.verbose or opt.exact_output):
		f = ('/dev/null','stderr.out')[g.platform=='win']
		sys.stderr = open(f,'a')

def end_silence():
	if not (opt.verbose or opt.exact_output):
		sys.stderr = stderr_save

def errmsg(s): stderr_save.write(s+'\n')
def errmsg_r(s): stderr_save.write(s)

if opt.list_cmds:
	from mmgen.term import get_terminal_size
	tw = get_terminal_size()[0]
	fs = '  {:<{w}} - {}'

	Msg(green('AVAILABLE COMMANDS:'))
	w = max(map(len,cmd_data))
	for cmd in cmd_data:
		if cmd[:5] == 'info_':
			Msg(green('  {}:'.format(capfirst(cmd_data[cmd][0]))))
			continue
		Msg('  '+fs.format(cmd,cmd_data[cmd][1],w=w))

	for cl,lbl in ((meta_cmds,'METACOMMANDS'),(cmd_list,'COMMAND GROUPS')):
		w = max(map(len,cl))
		Msg('\n'+green('AVAILABLE {}:'.format(lbl)))
		for cmd in cl:
			ft = format_par(' '.join(cl[cmd]),width=tw,indent=4,as_list=True)
			sep = '' if not ft else ' ' if len(ft[0]) + len(cmd) < tw - 4 else '\n    '
			Msg('  {}{}{}'.format(yellow(cmd+':'),sep,'\n'.join(ft).lstrip()))

	Msg('\n'+green('AVAILABLE UTILITIES:'))
	w = max(map(len,utils))
	for cmd in sorted(utils):
		Msg(fs.format(cmd,utils[cmd],w=w))

	sys.exit(0)

NL = ('\r\n','\n')[g.platform=='linux' and bool(opt.popen_spawn)]

def get_file_with_ext(ext,mydir,delete=True,no_dot=False,return_list=False):

	dot = ('.','')[bool(no_dot)]
	flist = [os.path.join(mydir,f) for f in os.listdir(mydir) if f == ext or f[-len(dot+ext):] == dot+ext]

	if not flist: return False
	if return_list: return flist

	if len(flist) > 1:
		if delete:
			if not opt.quiet:
				msg(u"Multiple *.{} files in '{}' - deleting".format(ext,mydir))
			for f in flist:
				msg(f)
				os.unlink(f)
		return False
	else:
		return flist[0]

def find_generated_exts(cmd):
	out = []
	for k in cfgs:
		for ext,prog in cfgs[k]['dep_generators'].items():
			if prog == cmd:
				out.append((ext,cfgs[k]['tmpdir']))
	return out

def get_addrfile_checksum(display=False):
	addrfile = get_file_with_ext('addrs',cfg['tmpdir'])
	silence()
	chk = AddrList(addrfile).chksum
	if opt.verbose and display: msg('Checksum: {}'.format(cyan(chk)))
	end_silence()
	return chk

def verify_checksum_or_exit(checksum,chk):
	if checksum != chk:
		errmsg(red('Checksum error: {}'.format(chk)))
		sys.exit(1)
	vmsg(green('Checksums match: ') + cyan(chk))

from test.mmgen_pexpect import MMGenPexpect
class MMGenExpect(MMGenPexpect):

	def __init__(self,name,mmgen_cmd,cmd_args=[],extra_desc='',no_output=False,msg_only=False,no_msg=False):

		desc = ((cmd_data[name][1],name)[bool(opt.names)] + (' ' + extra_desc)).strip()
		passthru_args = ['testnet','rpc_host','rpc_port','regtest','coin']

		if not opt.system:
			mmgen_cmd = os.path.relpath(os.path.join(repo_root,'cmds',mmgen_cmd))
		elif g.platform == 'win':
			mmgen_cmd = os.path.join('/mingw64','opt','bin',mmgen_cmd)

		return MMGenPexpect.__init__(
			self,
			name,
			mmgen_cmd,
			cmd_args,
			desc,
			no_output=no_output,
			passthru_args=passthru_args,
			msg_only=msg_only,
			no_msg=no_msg,
			log_fd=log_fd)

def create_fake_unspent_entry(coinaddr,al_id=None,idx=None,lbl=None,non_mmgen=False,segwit=False):
	if 'S' not in g.proto.mmtypes: segwit = False
	if lbl: lbl = ' ' + lbl
	k = coinaddr.addr_fmt
	if not segwit and k == 'p2sh': k = 'p2pkh'
	s_beg,s_end = { 'p2pkh':  ('76a914','88ac'),
					'p2sh':   ('a914','87'),
					'bech32': (g.proto.witness_vernum_hex+'14','') }[k]
	amt1,amt2 = {'btc':(10,40),'bch':(10,40),'ltc':(1000,4000)}[coin_sel]
	ret = {
		'account': '{}:{}'.format(g.proto.base_coin.lower(),coinaddr) if non_mmgen \
			else (u'{}:{}{}'.format(al_id,idx,lbl)),
		'vout': int(getrandnum(4) % 8),
		'txid': unicode(hexlify(os.urandom(32))),
		'amount': g.proto.coin_amt('{}.{}'.format(amt1 + getrandnum(4) % amt2, getrandnum(4) % 100000000)),
		'address': coinaddr,
		'spendable': False,
		'scriptPubKey': '{}{}{}'.format(s_beg,coinaddr.hex,s_end),
		'confirmations': getrandnum(3) / 2 # max: 8388608 (7 digits)
	}
	return ret

labels = [
	"Automotive",
	"Travel expenses",
	"Healthcare",
	ref_tx_label_jp[:40],
	ref_tx_label_zh[:40],
	"Alice's allowance",
	"Bob's bequest",
	"House purchase",
	"Real estate fund",
	"Job 1",
	"XYZ Corp.",
	"Eddie's endowment",
	"Emergency fund",
	"Real estate fund",
	"Ian's inheritance",
	"",
	"Rainy day",
	"Fred's funds",
	"Job 2",
	"Carl's capital",
]

def get_label(do_shuffle=False):
	from random import shuffle
	global label_iter
	try:
		return unicode(next(label_iter))
	except:
		if do_shuffle: shuffle(labels)
		label_iter = iter(labels)
		return unicode(next(label_iter))

def create_fake_unspent_data(adata,tx_data,non_mmgen_input='',non_mmgen_input_compressed=True):

	out = []
	for d in tx_data.values():
		al = adata.addrlist(d['al_id'])
		for n,(idx,coinaddr) in enumerate(al.addrpairs()):
			lbl = get_label(do_shuffle=True)
			out.append(create_fake_unspent_entry(coinaddr,d['al_id'],idx,lbl,segwit=d['segwit']))
			if n == 0:  # create a duplicate address. This means addrs_per_wallet += 1
				out.append(create_fake_unspent_entry(coinaddr,d['al_id'],idx,lbl,segwit=d['segwit']))

	if non_mmgen_input:
		privkey = PrivKey(os.urandom(32),compressed=non_mmgen_input_compressed,pubkey_type='std')
		rand_coinaddr = AddrGenerator('p2pkh').to_addr(KeyGenerator('std').to_pubhex(privkey))
		of = os.path.join(cfgs[non_mmgen_input]['tmpdir'],non_mmgen_fn)
		write_data_to_file(of,  privkey.wif+'\n','compressed {} key'.format(g.proto.name),
								silent=True,ignore_opt_outdir=True)
		out.append(create_fake_unspent_entry(rand_coinaddr,non_mmgen=True,segwit=False))

#	msg('\n'.join([repr(o) for o in out])); sys.exit(0)
	return out

def write_fake_data_to_file(d):
	unspent_data_file = os.path.join(cfg['tmpdir'],u'unspent.json')
	write_data_to_file(unspent_data_file,d,'Unspent outputs',silent=True,ignore_opt_outdir=True)
	os.environ['MMGEN_BOGUS_WALLET_DATA'] = unspent_data_file.encode('utf8')
	bwd_msg = u'MMGEN_BOGUS_WALLET_DATA={}'.format(unspent_data_file)
	if opt.print_cmdline: msg(bwd_msg)
	if opt.log: log_fd.write(bwd_msg + ' ')
	if opt.verbose or opt.exact_output:
		sys.stderr.write(u"Fake transaction wallet data written to file {!r}\n".format(unspent_data_file))

def create_tx_data(sources,addrs_per_wallet=addrs_per_wallet):
	tx_data,ad = {},AddrData()
	for s in sources:
		afile = get_file_with_ext('addrs',cfgs[s]['tmpdir'])
		al = AddrList(afile)
		ad.add(al)
		aix = AddrIdxList(fmt_str=cfgs[s]['addr_idx_list'])
		if len(aix) != addrs_per_wallet:
			errmsg(red('Address index list length != {}: {}'.format(addrs_per_wallet,repr(aix))))
			sys.exit(0)
		tx_data[s] = {
			'addrfile': afile,
			'chk': al.chksum,
			'al_id': al.al_id,
			'addr_idxs': aix[-2:],
			'segwit': cfgs[s]['segwit']
		}
	return ad,tx_data

def make_txcreate_cmdline(tx_data):
	privkey = PrivKey(os.urandom(32),compressed=True,pubkey_type='std')
	t = ('p2pkh','segwit')['S' in g.proto.mmtypes]
	rand_coinaddr = AddrGenerator(t).to_addr(KeyGenerator('std').to_pubhex(privkey))

	# total of two outputs must be < 10 BTC (<1000 LTC)
	mods = {'btc':(6,4),'bch':(6,4),'ltc':(600,400)}[coin_sel]
	for k in cfgs:
		cfgs[k]['amts'] = [None,None]
		for idx,mod in enumerate(mods):
			cfgs[k]['amts'][idx] = '{}.{}'.format(getrandnum(4) % mod, str(getrandnum(4))[:5])

	cmd_args = ['--outdir='+cfg['tmpdir']]
	for num in tx_data:
		s = tx_data[num]
		cmd_args += [
			'{}:{},{}'.format(s['al_id'],s['addr_idxs'][0],cfgs[num]['amts'][0]),
		]
		# + one change address and one BTC address
		if num is tx_data.keys()[-1]:
			cmd_args += ['{}:{}'.format(s['al_id'],s['addr_idxs'][1])]
			cmd_args += ['{},{}'.format(rand_coinaddr,cfgs[num]['amts'][1])]

	return cmd_args + [tx_data[num]['addrfile'] for num in tx_data]

def add_comments_to_addr_file(addrfile,outfile,use_labels=False):
	silence()
	gmsg(u"Adding comments to address file '{}'".format(addrfile))
	a = AddrList(addrfile)
	for n,idx in enumerate(a.idxs(),1):
		if use_labels:
			a.set_comment(idx,get_label())
		else:
			if n % 2: a.set_comment(idx,'Test address {}'.format(n))
	a.format(enable_comments=True)
	write_data_to_file(outfile,a.fmt_data,silent=True,ignore_opt_outdir=True)
	end_silence()

# 100 words chosen randomly from here:
#   https://github.com/bitcoin/bips/pull/432/files/6332230d63149a950d05db78964a03bfd344e6b0
rwords = """
	алфавит алый амнезия амфора артист баян белый биатлон брат бульвар веревка вернуть весть возраст
	восток горло горный десяток дятел ежевика жест жизнь жрать заговор здание зона изделие итог кабина
	кавалер каждый канал керосин класс клятва князь кривой крыша крючок кузнец кукла ландшафт мальчик
	масса масштаб матрос мрак муравей мычать негодяй носок ночной нрав оборот оружие открытие оттенок
	палуба пароход период пехота печать письмо позор полтора понятие поцелуй почему приступ пруд пятно
	ранее режим речь роса рынок рябой седой сердце сквозь смех снимок сойти соперник спичка стон
	сувенир сугроб суть сцена театр тираж толк удивить улыбка фирма читатель эстония эстрада юность
	"""
def make_brainwallet_file(fn):
	# Print random words with random whitespace in between
	wl = rwords.split()
	nwords,ws_list,max_spaces = 10,'    \n',5
	def rand_ws_seq():
		nchars = getrandnum(1) % max_spaces + 1
		return ''.join([ws_list[getrandnum_range(1,200) % len(ws_list)] for i in range(nchars)])
	rand_pairs = [wl[getrandnum_range(1,200) % len(wl)] + rand_ws_seq() for i in range(nwords)]
	d = ''.join(rand_pairs).rstrip() + '\n'
	if opt.verbose: msg_r('Brainwallet password:\n{}'.format(cyan(d)))
	write_data_to_file(fn,d,'brainwallet password',silent=True,ignore_opt_outdir=True)

def do_between():
	if opt.pause:
		if keypress_confirm(green('Continue?'),default_yes=True):
			if opt.verbose or opt.exact_output: sys.stderr.write('\n')
		else:
			errmsg('Exiting at user request')
			sys.exit(0)
	elif opt.verbose or opt.exact_output:
		sys.stderr.write('\n')


rebuild_list = OrderedDict()

def check_needs_rerun(
		ts,
		cmd,
		build=False,
		root=True,
		force_delete=False,
		dpy=False
	):

	rerun = (False,True)[root] # force_delete is not passed to recursive call

	fns = []
	if force_delete or not root:
		# does cmd produce a needed dependency(ies)?
		ret = ts.get_num_exts_for_cmd(cmd,dpy)
		if ret:
			for ext in ret[1]:
				fn = get_file_with_ext(ext,cfgs[ret[0]]['tmpdir'],delete=build)
				if fn:
					if force_delete: os.unlink(fn)
					else: fns.append(fn)
				else: rerun = True

	fdeps = ts.generate_file_deps(cmd)
	cdeps = ts.generate_cmd_deps(fdeps)
#	print 'cmd,fdeps,cdeps,fns: ',cmd,fdeps,cdeps,fns # DEBUG

	for fn in fns:
		my_age = os.stat(fn).st_mtime
		for num,ext in fdeps:
			f = get_file_with_ext(ext,cfgs[num]['tmpdir'],delete=build)
			if f and os.stat(f).st_mtime > my_age:
				rerun = True

	for cdep in cdeps:
		if check_needs_rerun(ts,cdep,build=build,root=False,dpy=cmd):
			rerun = True

	if build:
		if rerun:
			for fn in fns:
				if not root: os.unlink(fn)
			if not (dpy and opt.skip_deps):
				ts.do_cmd(cmd)
			if not root: do_between()
	else:
		# If prog produces multiple files:
		if cmd not in rebuild_list or rerun == True:
			rebuild_list[cmd] = (rerun,fns[0] if fns else '') # FIX

	return rerun

def refcheck(desc,chk,refchk):
	vmsg("Comparing {} '{}' to stored reference".format(desc,chk))
	if chk == refchk:
		ok()
	else:
		if not opt.verbose: errmsg('')
		m = "Fatal error - {} '{}' does not match reference value '{}'.  Aborting test"
		errmsg(red(m.format(desc,chk,refchk)))
		sys.exit(3)

def check_deps(cmds):
	if len(cmds) != 1:
		die(1,'Usage: {} check_deps <command>'.format(g.prog_name))

	cmd = cmds[0]

	if cmd not in cmd_data:
		die(1,"'{}': unrecognized command".format(cmd))

	if not opt.quiet:
		msg("Checking dependencies for '{}'".format(cmd))

	check_needs_rerun(ts,cmd,build=False)

	w = max(map(len,rebuild_list)) + 1
	for cmd in rebuild_list:
		c = rebuild_list[cmd]
		m = 'Rebuild' if (c[0] and c[1]) else 'Build' if c[0] else 'OK'
		msg('cmd {:<{w}} {}'.format(cmd+':', m, w=w))
#			mmsg(cmd,c)


def clean(usr_dirs=[]):
	if opt.skip_deps: return
	all_dirs = MMGenTestSuite().list_tmp_dirs()
	dirnums = (usr_dirs or all_dirs)
	for d in sorted(dirnums):
		if str(d) in all_dirs:
			cleandir(all_dirs[str(d)])
		else:
			die(1,'{}: invalid directory number'.format(d))
	cleandir(data_dir)
	cleandir(trash_dir)

def skip_for_win():
	if g.platform == 'win':
		import traceback
		f = traceback.extract_stack()[-2][-2]
		msg("Skipping test '{}': not supported on Windows platform".format(f))
		return True
	else:
		return False

class MMGenTestSuite(object):

	def __init__(self):
		pass

	def list_tmp_dirs(self):
		d = {}
		for k in cfgs: d[k] = cfgs[k]['tmpdir']
		return d

	def get_num_exts_for_cmd(self,cmd,dpy=False): # dpy ignored here
		num = str(cmd_data[cmd][0])
		dgl = cfgs[num]['dep_generators']
#	mmsg(num,cmd,dgl)
		if cmd in dgl.values():
			exts = [k for k in dgl if dgl[k] == cmd]
			return (num,exts)
		else:
			return None

	def do_cmd(self,cmd):

		# delete files produced by this cmd
# 		for ext,tmpdir in find_generated_exts(cmd):
# 			print cmd, get_file_with_ext(ext,tmpdir)

		d = [(str(num),ext) for exts,num in cmd_data[cmd][2] for ext in exts]

		# delete files depended on by this cmd
		al = [get_file_with_ext(ext,cfgs[num]['tmpdir']) for num,ext in d]

		global cfg
		cfg = cfgs[str(cmd_data[cmd][0])]

		if opt.resume:
			if cmd == opt.resume:
				ymsg("Resuming at '{}'".format(cmd))
				opt.resume = False
				opt.skip_deps = False
			else:
				return

		if opt.profile: start = time.time()
		self.__class__.__dict__[cmd](*([self,cmd] + al))
		if opt.profile:
			msg('\r\033[50C{:.4f}'.format(time.time() - start))
		global cmd_total
		cmd_total += 1

		if cmd == opt.exit_after:
			sys.exit(0)

	def generate_file_deps(self,cmd):
		return [(str(n),e) for exts,n in cmd_data[cmd][2] for e in exts]

	def generate_cmd_deps(self,fdeps):
		return [cfgs[str(n)]['dep_generators'][ext] for n,ext in fdeps]

	def helpscreens(self,name,arg='--help'):
		scripts = (
			'walletgen','walletconv','walletchk','txcreate','txsign','txsend','txdo','txbump',
			'addrgen','addrimport','keygen','passchg','tool','passgen','regtest','autosign')
		for s in scripts:
			t = MMGenExpect(name,('mmgen-'+s),[arg],extra_desc='(mmgen-{})'.format(s),no_output=True)
			t.read()
			t.ok()

	def longhelpscreens(self,name): self.helpscreens(name,arg='--longhelp')

	def walletgen(self,name,del_dw_run='dummy',seed_len=None,gen_dfl_wallet=False):
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd']+'\n')
		args = ['-p1']
		if not gen_dfl_wallet: args += ['-d',cfg['tmpdir']]
		if seed_len: args += ['-l',str(seed_len)]
		t = MMGenExpect(name,'mmgen-walletgen', args + [usr_rand_arg])
		t.license()
		t.usr_rand(usr_rand_chars)
		t.passphrase_new('new MMGen wallet',cfg['wpasswd'])
		t.label()
		global have_dfl_wallet
		if not have_dfl_wallet and gen_dfl_wallet:
			t.expect('move it to the data directory? (Y/n): ','y')
			have_dfl_wallet = True
		t.written_to_file('MMGen wallet')
		t.ok()

	def walletgen_dfl_wallet(self,name,seed_len=None):
		self.walletgen(name,seed_len=seed_len,gen_dfl_wallet=True)

	def brainwalletgen_ref(self,name):
		sl_arg = '-l{}'.format(cfg['seed_len'])
		hp_arg = '-p{}'.format(ref_wallet_hash_preset)
		label = u"test.py ref. wallet (pw '{}', seed len {}) α".format(ref_wallet_brainpass,cfg['seed_len'])
		bf = 'ref.mmbrain'
		args = ['-d',cfg['tmpdir'],hp_arg,sl_arg,'-ib','-L',label]
		write_to_tmpfile(cfg,bf,ref_wallet_brainpass)
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd'])
		t = MMGenExpect(name,'mmgen-walletconv', args + [usr_rand_arg])
		t.license()
		t.expect('Enter brainwallet: ', ref_wallet_brainpass+'\n')
		t.passphrase_new('new MMGen wallet',cfg['wpasswd'])
		t.usr_rand(usr_rand_chars)
		sid = os.path.basename(t.written_to_file('MMGen wallet')).split('-')[0]
		refcheck('Seed ID',sid,cfg['seed_id'])

	def refwalletgen(self,name): self.brainwalletgen_ref(name)

	def passchg(self,name,wf,pf,label_action='cmdline'):
		silence()
		write_to_tmpfile(cfg,pwfile,get_data_from_file(pf))
		end_silence()
		add_args = {'cmdline': ['-d',cfg['tmpdir'],'-L',u'Changed label (UTF-8) α'],
					'keep':    ['-d',trash_dir,'--keep-label'],
					'user':    ['-d',trash_dir]
					}[label_action]
		t = MMGenExpect(name,'mmgen-passchg', add_args + [usr_rand_arg, '-p2'] + ([],[wf])[bool(wf)])
		t.license()
		t.passphrase('MMGen wallet',cfgs['1']['wpasswd'],pwtype='old')
		t.expect_getend('Hash preset changed to ')
		t.passphrase('MMGen wallet',cfg['wpasswd'],pwtype='new') # reuse passphrase?
		t.expect('Repeat passphrase: ',cfg['wpasswd']+'\n')
		t.usr_rand(usr_rand_chars)
		if label_action == 'user':
			t.expect('Enter a wallet label.*: ',u'Interactive Label (UTF-8) α\n',regex=True)
		t.expect_getend(('Label changed to ','Reusing label ')[label_action=='keep'])
#		t.expect_getend('Key ID changed: ')
		if not wf:
			t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
			t.written_to_file('New wallet')
			t.expect('Securely deleting old wallet')
#			t.expect('Okay to WIPE 1 regular file ? (Yes/No)','Yes\n')
			t.expect('Wallet passphrase has changed')
			t.expect_getend('has been changed to ')
		else:
			t.written_to_file('MMGen wallet')
		t.ok()

	def passchg_keeplabel(self,name,wf,pf):
		return self.passchg(name,wf,pf,label_action='keep')

	def passchg_usrlabel(self,name,wf,pf):
		return self.passchg(name,wf,pf,label_action='user')

	def passchg_dfl_wallet(self,name,pf):
		return self.passchg(name=name,wf=None,pf=pf)

	def walletchk(self,name,wf,pf,desc='MMGen wallet',add_args=[],sid=None,pw=False,extra_desc=''):
		args = []
		hp = cfg['hash_preset'] if 'hash_preset' in cfg else '1'
		wf_arg = [wf] if wf else []
		t = MMGenExpect(name,'mmgen-walletchk',
				add_args+args+['-p',hp]+wf_arg,
				extra_desc=extra_desc)
		if desc != 'hidden incognito data':
			t.expect("Getting {} from file '".format(desc))
		if pw:
			t.passphrase(desc,cfg['wpasswd'])
			t.expect(['Passphrase is OK', 'Passphrase.* are correct'],regex=True)
		chk = t.expect_getend('Valid {} for Seed ID '.format(desc))[:8]
		if sid: t.cmp_or_die(chk,sid)
		else: t.ok()

	def walletchk_newpass(self,name,wf,pf):
		return self.walletchk(name,wf,pf,pw=True)

	def walletchk_newpass_dfl_wallet(self,name,pf):
		return self.walletchk_newpass(name,wf=None,pf=pf)

	def delete_dfl_wallet(self,name,pf):
		with open(os.path.join(cfg['tmpdir'],'del_dw_run'),'w') as f: pass
		if opt.no_dw_delete: return True
		for wf in [f for f in os.listdir(g.data_dir) if f[-6:]=='.mmdat']:
			os.unlink(os.path.join(g.data_dir,wf))
		MMGenExpect(name,'',msg_only=True)
		global have_dfl_wallet
		have_dfl_wallet = False
		ok()

	def addrgen(self,name,wf,pf=None,check_ref=False,ftype='addr',id_str=None,extra_args=[],mmtype=None):
		if ftype[:4] != 'pass' and not mmtype:
			if cfg['segwit']: mmtype = ('segwit','bech32')[bool(opt.bech32)]
		cmd_pfx = (ftype,'pass')[ftype[:4]=='pass']
		t = MMGenExpect(name,'mmgen-{}gen'.format(cmd_pfx),
				['-d',cfg['tmpdir']] +
				extra_args +
				([],['--type='+str(mmtype)])[bool(mmtype)] +
				([],[wf])[bool(wf)] +
				([id_str] if id_str else []) +
				[cfg['{}_idx_list'.format(cmd_pfx)]],
				extra_desc='({})'.format(mmtype) if mmtype in ('segwit','bech32') else '')
		t.license()
		t.passphrase('MMGen wallet',cfg['wpasswd'])
		t.expect('Passphrase is OK')
		desc = ('address','password')[ftype[:4]=='pass']
		chk = t.expect_getend(r'Checksum for {} data .*?: '.format(desc),regex=True)
		if ftype[:4] == 'pass':
			t.expect('Encrypt password list? (y/N): ','\n')
			t.written_to_file('Password list',oo=True)
		else:
			t.written_to_file('Addresses',oo=True)
		if check_ref:
			try:    k =   { 'pass32':  'passfile32_chk',
							'passhex': 'passfilehex_chk',
							'pass':    'passfile_chk'}[ftype]
			except: k = '{}file{}_chk'.format(ftype,'_'+mmtype if mmtype else '')
			chk_ref = cfg[k] if ftype[:4] == 'pass' else cfg[k][fork][g.testnet]
			refcheck('{}list data checksum'.format(ftype),chk,chk_ref)
		else:
			t.ok()

	def addrgen_dfl_wallet(self,name,pf=None,check_ref=False):
		return self.addrgen(name,wf=None,pf=pf,check_ref=check_ref)

	def refaddrgen(self,name,wf,pf):
		self.addrgen(name,wf,pf=pf,check_ref=True)

	def refaddrgen_compressed(self,name,wf,pf):
		if opt.segwit or opt.bech32:
			msg('Skipping non-Segwit address generation'); return True
		self.addrgen(name,wf,pf=pf,check_ref=True,mmtype='compressed')

	def txcreate_ui_common(self,t,name,
							menu=[],inputs='1',
							file_desc='Transaction',
							input_sels_prompt='to spend',
							bad_input_sels=False,non_mmgen_inputs=0,
							interactive_fee='',
							fee_desc='transaction fee',fee_res=None,
							add_comment='',view='t',save=True,no_ok=False):
		for choice in menu + ['q']:
			t.expect(r"'q'=quit view, .*?:.",choice,regex=True)
		if bad_input_sels:
			for r in ('x','3-1','9999'):
				t.expect(input_sels_prompt+': ',r+'\n')
		t.expect(input_sels_prompt+': ',inputs+'\n')

		if not name[:4] == 'txdo':
			for i in range(non_mmgen_inputs):
				t.expect('Accept? (y/N): ','y')

		have_est_fee = t.expect([fee_desc+': ','OK? (Y/n): ']) == 1
		if have_est_fee and not interactive_fee:
			t.send('y')
		else:
			if have_est_fee: t.send('n')
			t.send(interactive_fee+'\n')
			if fee_res: t.expect(fee_res)
			t.expect('OK? (Y/n): ','y')

		t.expect('(Y/n): ','\n')     # chg amt OK?
		t.do_comment(add_comment)
		t.view_tx(view)
		if not name[:4] == 'txdo':
			t.expect('(y/N): ',('n','y')[save])
			t.written_to_file(file_desc)
			if not no_ok: t.ok()

	def txsign_ui_common(self,t,name,   view='t',add_comment='',
										ni=False,save=True,do_passwd=False,
										file_desc='Signed transaction',no_ok=False,has_label=False):
		txdo = name[:4] == 'txdo'

		if do_passwd:
			t.passphrase('MMGen wallet',cfg['wpasswd'])

		if not ni and not txdo:
			t.view_tx(view)
			t.do_comment(add_comment,has_label=has_label)
			t.expect('(Y/n): ',('n','y')[save])

		t.written_to_file(file_desc)

		if not txdo and not no_ok: t.ok()

	def do_confirm_send(self,t,quiet=False,confirm_send=True):
		t.expect('Are you sure you want to broadcast this')
		m = ('YES, I REALLY WANT TO DO THIS','YES')[quiet]
		t.expect("'{}' to confirm: ".format(m),('',m)[confirm_send]+'\n')

	def txsend_ui_common(self,t,name,   view='n',add_comment='',
										confirm_send=True,bogus_send=True,quiet=False,
										file_desc='Sent transaction',no_ok=False,has_label=False):

		txdo = name[:4] == 'txdo'
		if not txdo:
			t.license() # MMGEN_NO_LICENSE is set, so does nothing
			t.view_tx(view)
			t.do_comment(add_comment,has_label=has_label)

		self.do_confirm_send(t,quiet=quiet,confirm_send=confirm_send)

		if bogus_send:
			txid = ''
			t.expect('BOGUS transaction NOT sent')
		else:
			txid = t.expect_getend('Transaction sent: ')
			assert len(txid) == 64,"'{}': Incorrect txid length!".format(txid)

		t.written_to_file(file_desc)
		if not txdo and not no_ok: t.ok()

		return txid

	def txcreate_common(self,name,
						sources=['1'],
						non_mmgen_input='',
						do_label=False,
						txdo_args=[],
						add_args=[],
						view='n',
						addrs_per_wallet=addrs_per_wallet,
						non_mmgen_input_compressed=True,
						cmdline_inputs=False):

		if opt.verbose or opt.exact_output:
			sys.stderr.write(green('Generating fake tracking wallet info\n'))

		silence()
		ad,tx_data = create_tx_data(sources,addrs_per_wallet)
		dfake = create_fake_unspent_data(ad,tx_data,non_mmgen_input,non_mmgen_input_compressed)
		write_fake_data_to_file(repr(dfake))
		cmd_args = make_txcreate_cmdline(tx_data)
		if cmdline_inputs:
			from mmgen.tx import TwLabel
			cmd_args = ['--inputs={},{},{},{},{},{}'.format(
				TwLabel(dfake[0]['account']).mmid,dfake[1]['address'],
				TwLabel(dfake[2]['account']).mmid,dfake[3]['address'],
				TwLabel(dfake[4]['account']).mmid,dfake[5]['address']
				),'--outdir='+trash_dir] + cmd_args[1:]
		end_silence()

		if opt.verbose or opt.exact_output: sys.stderr.write('\n')

		t = MMGenExpect(name,
			'mmgen-'+('txcreate','txdo')[bool(txdo_args)],
			([],['--rbf'])[g.proto.cap('rbf')] +
			['-f',tx_fee,'-B'] + add_args + cmd_args + txdo_args)

		if cmdline_inputs:
			t.written_to_file('Transaction')
			t.ok()
			return

		t.license()

		if txdo_args and add_args: # txdo4
			t.do_decrypt_ka_data(hp='1',pw=cfgs['14']['kapasswd'])

		for num in tx_data:
			t.expect_getend('Getting address data from file ')
			chk=t.expect_getend(r'Checksum for address data .*?: ',regex=True)
			verify_checksum_or_exit(tx_data[num]['chk'],chk)

		# not in tracking wallet warning, (1 + num sources) times
		if t.expect(['Continue anyway? (y/N): ',
				'Unable to connect to {}'.format(g.proto.daemon_name)]) == 0:
			t.send('y')
		else:
			errmsg(red('Error: unable to connect to {}.  Exiting'.format(g.proto.daemon_name)))
			sys.exit(1)

		for num in tx_data:
			t.expect('Continue anyway? (y/N): ','y')

		outputs_list = [(addrs_per_wallet+1)*i + 1 for i in range(len(tx_data))]
		if non_mmgen_input: outputs_list.append(len(tx_data)*(addrs_per_wallet+1) + 1)

		self.txcreate_ui_common(t,name,
					menu=(['M'],['M','D','m','g'])[name=='txcreate'],
					inputs=' '.join(map(str,outputs_list)),
					add_comment=('',ref_tx_label_lat_cyr_gr)[do_label],
					non_mmgen_inputs=(0,1)[bool(non_mmgen_input and not txdo_args)],
					view=view)

		return t

	def txcreate(self,name,addrfile):
		self.txcreate_common(name,sources=['1'],add_args=['--vsize-adj=1.01'])

	def txcreate_ni(self,name,addrfile):
		self.txcreate_common(name,sources=['1'],cmdline_inputs=True,add_args=['--yes'])

	def txbump(self,name,txfile,prepend_args=[],seed_args=[]):
		if not g.proto.cap('rbf'):
			msg('Skipping RBF'); return True
		args = prepend_args + ['--quiet','--outdir='+cfg['tmpdir'],txfile] + seed_args
		t = MMGenExpect(name,'mmgen-txbump',args)
		if seed_args:
			t.do_decrypt_ka_data(hp='1',pw=cfgs['14']['kapasswd'])
		t.expect('deduct the fee from (Hit ENTER for the change output): ','1\n')
		# Fee must be > tx_fee + network relay fee (currently 0.00001)
		t.expect('OK? (Y/n): ','\n')
		t.expect('Enter transaction fee: ',txbump_fee+'\n')
		t.expect('OK? (Y/n): ','\n')
		if seed_args: # sign and send
			t.do_comment(False,has_label=True)
			for cnum,desc in (('1','incognito data'),('3','MMGen wallet'),('4','MMGen wallet')):
				t.passphrase(desc,cfgs[cnum]['wpasswd'])
			self.do_confirm_send(t,quiet=not g.debug,confirm_send=True)
			if g.debug:
				t.written_to_file('Transaction')
		else:
			t.do_comment(False)
			t.expect('Save transaction? (y/N): ','y')
			t.written_to_file('Transaction')
		os.unlink(txfile) # our tx file replaces the original
		cmd = 'touch ' + os.path.join(cfg['tmpdir'],u'txbump')
		os.system(cmd.encode('utf8'))
		t.ok()

	def txdo(self,name,addrfile,wallet):
		t = self.txcreate_common(name,sources=['1'],txdo_args=[wallet])
		self.txsign_ui_common(t,name,view='n',do_passwd=True)
		self.txsend_ui_common(t,name)
		t.ok()

	def txcreate_dfl_wallet(self,name,addrfile):
		self.txcreate_common(name,sources=['15'])

	def txsign_end(self,t,tnum=None,has_label=False):
		t.expect('Signing transaction')
		t.do_comment(False,has_label=has_label)
		t.expect('Save signed transaction.*?\? \(Y/n\): ','y',regex=True)
		t.written_to_file('Signed transaction' + (' #' + tnum if tnum else ''), oo=True)

	def txsign(self,name,txfile,wf,pf='',bumpf='',save=True,has_label=False,do_passwd=True,extra_opts=[]):
		t = MMGenExpect(name,'mmgen-txsign', extra_opts + ['-d',cfg['tmpdir'],txfile]+([],[wf])[bool(wf)])
		t.license()
		t.view_tx('n')
		if do_passwd: t.passphrase('MMGen wallet',cfg['wpasswd'])
		if save:
			self.txsign_end(t,has_label=has_label)
			t.ok()
		else:
			t.do_comment(False,has_label=has_label)
			t.expect('Save signed transaction? (Y/n): ','n')
			t.ok(exit_val=1)

	def txsign_dfl_wallet(self,name,txfile,pf='',save=True,has_label=False):
		return self.txsign(name,txfile,wf=None,pf=pf,save=save,has_label=has_label)

	def txsend(self,name,sigfile,bogus_send=True,extra_opts=[]):
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = ''
		t = MMGenExpect(name,'mmgen-txsend', extra_opts + ['-d',cfg['tmpdir'],sigfile])
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = '1'
		self.txsend_ui_common(t,name,view='t',add_comment='')

	def walletconv_export(self,name,wf,desc,uargs=[],out_fmt='w',pf=None,out_pw=False):
		opts = ['-d',cfg['tmpdir'],'-o',out_fmt] + uargs + \
			([],[wf])[bool(wf)] + ([],['-P',pf])[bool(pf)]
		t = MMGenExpect(name,'mmgen-walletconv',opts)
		t.license()
		if not pf:
			t.passphrase('MMGen wallet',cfg['wpasswd'])
		if out_pw:
			t.passphrase_new('new '+desc,cfg['wpasswd'])
			t.usr_rand(usr_rand_chars)

		if ' '.join(desc.split()[-2:]) == 'incognito data':
			m = 'Generating encryption key from OS random data '
			t.expect(m); t.expect(m)
			ic_id = t.expect_getend('New Incog Wallet ID: ')
			t.expect(m)
		if desc == 'hidden incognito data':
			write_to_tmpfile(cfg,incog_id_fn,ic_id)
			ret = t.expect(['Create? (Y/n): ',"'YES' to confirm: "])
			if ret == 0:
				t.send('\n')
				t.expect('Enter file size: ',str(hincog_bytes)+'\n')
			else:
				t.send('YES\n')
		if out_fmt == 'w': t.label()
		return t.written_to_file(capfirst(desc),oo=True),t

	def export_seed(self,name,wf,desc='seed data',out_fmt='seed',pf=None):
		f,t = self.walletconv_export(name,wf,desc=desc,out_fmt=out_fmt,pf=pf)
		silence()
		msg(u'{}: {}'.format(capfirst(desc),cyan(get_data_from_file(f,desc))))
		end_silence()
		t.ok()

	def export_hex(self,name,wf,desc='hexadecimal seed data',out_fmt='hex',pf=None):
		self.export_seed(name,wf,desc=desc,out_fmt=out_fmt,pf=pf)

	def export_seed_dfl_wallet(self,name,pf,desc='seed data',out_fmt='seed'):
		self.export_seed(name,wf=None,desc=desc,out_fmt=out_fmt,pf=pf)

	def export_mnemonic(self,name,wf):
		self.export_seed(name,wf,desc='mnemonic data',out_fmt='words')

	def export_incog(self,name,wf,desc='incognito data',out_fmt='i',add_args=[]):
		uargs = ['-p1',usr_rand_arg] + add_args
		f,t = self.walletconv_export(name,wf,desc=desc,out_fmt=out_fmt,uargs=uargs,out_pw=True)
		t.ok()

	def export_incog_hex(self,name,wf):
		self.export_incog(name,wf,desc='hex incognito data',out_fmt='xi')

	# TODO: make outdir and hidden incog compatible (ignore --outdir and warn user?)
	def export_incog_hidden(self,name,wf):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		add_args = ['-J',u'{},{}'.format(rf,hincog_offset)]
		self.export_incog(
			name,wf,desc='hidden incognito data',out_fmt='hi',add_args=add_args)

	def addrgen_seed(self,name,wf,foo,desc='seed data',in_fmt='seed'):
		stdout = (False,True)[desc=='seed data'] #capture output to screen once
		add_args = ([],['-S'])[bool(stdout)] + get_segwit_arg(cfg)
		t = MMGenExpect(name,'mmgen-addrgen', add_args +
				['-i'+in_fmt,'-d',cfg['tmpdir'],wf,cfg['addr_idx_list']])
		t.license()
		t.expect_getend('Valid {} for Seed ID '.format(desc))
		vmsg('Comparing generated checksum with checksum from previous address file')
		chk = t.expect_getend(r'Checksum for address data .*?: ',regex=True)
		if stdout: t.read()
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
		if in_fmt == 'seed':
			t.ok()
		else:
			t.no_overwrite()
			t.ok(exit_val=1)

	def addrgen_hex(self,name,wf,foo,desc='hexadecimal seed data',in_fmt='hex'):
		self.addrgen_seed(name,wf,foo,desc=desc,in_fmt=in_fmt)

	def addrgen_mnemonic(self,name,wf,foo):
		self.addrgen_seed(name,wf,foo,desc='mnemonic data',in_fmt='words')

	def addrgen_incog(self,name,wf=[],foo='',in_fmt='i',desc='incognito data',args=[]):
		t = MMGenExpect(name,'mmgen-addrgen', args + get_segwit_arg(cfg) + ['-i'+in_fmt,'-d',cfg['tmpdir']]+
				([],[wf])[bool(wf)] + [cfg['addr_idx_list']])
		t.license()
		t.expect_getend('Incog Wallet ID: ')
		t.hash_preset(desc,'1')
		t.passphrase('{} \w{{8}}'.format(desc),cfg['wpasswd'])
		vmsg('Comparing generated checksum with checksum from address file')
		chk = t.expect_getend(r'Checksum for address data .*?: ',regex=True)
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
		t.no_overwrite()
		t.ok(exit_val=1)

	def addrgen_incog_hex(self,name,wf,foo):
		self.addrgen_incog(name,wf,'',in_fmt='xi',desc='hex incognito data')

	def addrgen_incog_hidden(self,name,wf,foo):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		self.addrgen_incog(name,[],'',in_fmt='hi',desc='hidden incognito data',
			args=['-H',u'{},{}'.format(rf,hincog_offset),'-l',str(hincog_seedlen)])

	def keyaddrgen(self,name,wf,pf=None,check_ref=False,mmtype=None):
		if cfg['segwit'] and not mmtype:
			mmtype = ('segwit','bech32')[bool(opt.bech32)]
		args = ['-d',cfg['tmpdir'],usr_rand_arg,wf,cfg['addr_idx_list']]
		t = MMGenExpect(name,'mmgen-keygen',
				([],['--type='+str(mmtype)])[bool(mmtype)] + args,
				extra_desc='({})'.format(mmtype) if mmtype in ('segwit','bech32') else '')
		t.license()
		t.passphrase('MMGen wallet',cfg['wpasswd'])
		chk = t.expect_getend(r'Checksum for key-address data .*?: ',regex=True)
		if check_ref:
			k = 'keyaddrfile{}_chk'.format('_'+mmtype if mmtype else '')
			refcheck('key-address data checksum',chk,cfg[k][fork][g.testnet])
			return
		t.expect('Encrypt key list? (y/N): ','y')
		t.usr_rand(usr_rand_chars)
		t.hash_preset('new key list','1')
		t.passphrase_new('new key list',cfg['kapasswd'])
		t.written_to_file('Encrypted secret keys',oo=True)
		t.ok()

	def refkeyaddrgen(self,name,wf,pf):
		self.keyaddrgen(name,wf,pf,check_ref=True)

	def refkeyaddrgen_compressed(self,name,wf,pf):
		if opt.segwit or opt.bech32:
			msg('Skipping non-Segwit key-address generation'); return True
		self.keyaddrgen(name,wf,pf,check_ref=True,mmtype='compressed')

	def refpasswdgen(self,name,wf,pf):
		self.addrgen(name,wf,pf,check_ref=True,ftype='pass',id_str='alice@crypto.org')

	def ref_b32passwdgen(self,name,wf,pf):
		ea = ['--base32','--passwd-len','17']
		self.addrgen(name,wf,pf,check_ref=True,ftype='pass32',id_str=u'фубар@crypto.org',extra_args=ea)

	def ref_hexpasswdgen(self,name,wf,pf):
		ea = ['--hex']
		self.addrgen(name,wf,pf,check_ref=True,ftype='passhex',id_str=u'фубар@crypto.org',extra_args=ea)

	def txsign_keyaddr(self,name,keyaddr_file,txfile):
		t = MMGenExpect(name,'mmgen-txsign', ['-d',cfg['tmpdir'],'-M',keyaddr_file,txfile])
		t.license()
		t.do_decrypt_ka_data(hp='1',pw=cfg['kapasswd'])
		t.view_tx('n')
		self.txsign_end(t)
		t.ok()

	def walletgen2(self,name,del_dw_run='dummy'):
		self.walletgen(name,seed_len=128)

	def addrgen2(self,name,wf):
		self.addrgen(name,wf,pf='')

	def txcreate2(self,name,addrfile):
		self.txcreate_common(name,sources=['2'])

	def txsign2(self,name,txf1,wf1,txf2,wf2):
		t = MMGenExpect(name,'mmgen-txsign', ['-d',cfg['tmpdir'],txf1,wf1,txf2,wf2])
		t.license()
		for cnum in ('1','2'):
			t.view_tx('n')
			t.passphrase('MMGen wallet',cfgs[cnum]['wpasswd'])
			self.txsign_end(t,cnum)
		t.ok()

	def export_mnemonic2(self,name,wf):
		self.export_mnemonic(name,wf)

	def walletgen3(self,name,del_dw_run='dummy'):
		self.walletgen(name)

	def addrgen3(self,name,wf):
		self.addrgen(name,wf,pf='')

	def txcreate3(self,name,addrfile1,addrfile2):
		self.txcreate_common(name,sources=['1','3'])

	def txsign3(self,name,wf1,wf2,txf2):
		t = MMGenExpect(name,'mmgen-txsign', ['-d',cfg['tmpdir'],wf1,wf2,txf2])
		t.license()
		t.view_tx('n')
		for cnum in ('1','3'):
			t.passphrase('MMGen wallet',cfgs[cnum]['wpasswd'])
		self.txsign_end(t)
		t.ok()

	def walletgen4(self,name,del_dw_run='dummy'):
		bwf = os.path.join(cfg['tmpdir'],cfg['bw_filename'])
		make_brainwallet_file(bwf)
		seed_len = str(cfg['seed_len'])
		args = ['-d',cfg['tmpdir'],'-p1',usr_rand_arg,'-l'+seed_len,'-ib']
		t = MMGenExpect(name,'mmgen-walletconv', args + [bwf])
		t.license()
		t.passphrase_new('new MMGen wallet',cfg['wpasswd'])
		t.usr_rand(usr_rand_chars)
		t.label()
		t.written_to_file('MMGen wallet')
		t.ok()

	def addrgen4(self,name,wf):
		self.addrgen(name,wf,pf='')

	def txcreate4(self,name,f1,f2,f3,f4,f5,f6):
		self.txcreate_common(name,sources=['1','2','3','4','14'],non_mmgen_input='4',do_label=True,view='y')

	def txdo4(self,name,f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12):
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		add_args = ['-d',cfg['tmpdir'],'-i','brain','-b'+cfg['bw_params'],'-p1','-k',non_mm_fn,'-M',f12]
		t = self.txcreate_common(name,sources=['1','2','3','4','14'],
					non_mmgen_input='4',do_label=True,txdo_args=[f7,f8,f9,f10],add_args=add_args)
		os.system('rm -f {}/*.sigtx'.format(cfg['tmpdir'].encode('utf8')))

		for cnum,desc in (('1','incognito data'),('3','MMGen wallet')):
			t.passphrase('{}'.format(desc),cfgs[cnum]['wpasswd'])

		self.txsign_ui_common(t,name)
		self.txsend_ui_common(t,name)

		cmd = 'touch ' + os.path.join(cfg['tmpdir'],u'txdo')
		os.system(cmd.encode('utf8'))
		t.ok()

	def txbump4(self,name,f1,f2,f3,f4,f5,f6,f7,f8,f9): # f7:txfile,f9:'txdo'
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		self.txbump(name,f7,prepend_args=['-p1','-k',non_mm_fn,'-M',f1],seed_args=[f2,f3,f4,f5,f6,f8])

	def txsign4(self,name,f1,f2,f3,f4,f5,f6):
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		a = ['-d',cfg['tmpdir'],'-i','brain','-b'+cfg['bw_params'],'-p1','-k',non_mm_fn,'-M',f6,f1,f2,f3,f4,f5]
		t = MMGenExpect(name,'mmgen-txsign',a)
		t.license()
		t.do_decrypt_ka_data(hp='1',pw=cfgs['14']['kapasswd'])
		t.view_tx('t')

		for cnum,desc in (('1','incognito data'),('3','MMGen wallet')):
			t.passphrase('{}'.format(desc),cfgs[cnum]['wpasswd'])

		self.txsign_end(t,has_label=True)
		t.ok()

	def walletgen5(self,name,del_dw_run='dummy'):
		self.walletgen(name)

	def addrgen5(self,name,wf):
		self.addrgen(name,wf,pf='')

	def txcreate5(self,name,addrfile):
		self.txcreate_common(name,sources=['20'],non_mmgen_input='20',non_mmgen_input_compressed=False)

	def txsign5(self,name,txf,wf,bad_vsize=True,add_args=[]):
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		t = MMGenExpect(name,'mmgen-txsign', add_args + ['-d',cfg['tmpdir'],'-k',non_mm_fn,txf,wf])
		t.license()
		t.view_tx('n')
		t.passphrase('MMGen wallet',cfgs['20']['wpasswd'])
		if bad_vsize:
			t.expect('ERROR: Estimated transaction vsize is')
		else:
			t.do_comment(False)
			t.expect('Save signed transaction? (Y/n): ','y')
		t.read()
		t.ok(exit_val=(0,2)[bad_vsize])

	def walletgen6(self,name,del_dw_run='dummy'):
		self.walletgen(name)

	def addrgen6(self,name,wf):
		self.addrgen(name,wf,pf='')

	def txcreate6(self,name,addrfile):
		self.txcreate_common(
			name,sources=['21'],non_mmgen_input='21',non_mmgen_input_compressed=False,add_args=['--vsize-adj=1.08'])

	def txsign6(self,name,txf,wf):
		return self.txsign5(name,txf,wf,bad_vsize=False,add_args=['--vsize-adj=1.08'])


	def tool_encrypt(self,name,infile=''):
		if infile:
			infn = infile
		else:
			d = os.urandom(1033)
			tmp_fn = cfg['tool_enc_infn']
			write_to_tmpfile(cfg,tmp_fn,d,binary=True)
			infn = get_tmpfile_fn(cfg,tmp_fn)
		t = MMGenExpect(name,'mmgen-tool',['-d',cfg['tmpdir'],usr_rand_arg,'encrypt',infn])
		t.usr_rand(usr_rand_chars)
		t.hash_preset('user data','1')
		t.passphrase_new('user data',tool_enc_passwd)
		t.written_to_file('Encrypted data')
		t.ok()

# Generate the reference mmenc file
# 	def tool_encrypt_ref(self,name):
# 		infn = get_tmpfile_fn(cfg,cfg['tool_enc_ref_infn'])
# 		write_data_to_file(infn,cfg['tool_enc_reftext'],silent=True)
# 		self.tool_encrypt(name,infn)

	def tool_decrypt(self,name,f1,f2):
		of = name + '.out'
		pre = []
		t = MMGenExpect(name,'mmgen-tool',
			pre+['-d',cfg['tmpdir'],'decrypt',f2,'outfile='+of,'hash_preset=1'])
		t.passphrase('user data',tool_enc_passwd)
		t.written_to_file('Decrypted data')
		d1 = read_from_file(f1,binary=True)
		d2 = read_from_file(get_tmpfile_fn(cfg,of),binary=True)
		cmp_or_die(d1,d2,skip_ok=False)

	def tool_find_incog_data(self,name,f1,f2):
		i_id = read_from_file(f2).rstrip()
		vmsg('Incog ID: {}'.format(cyan(i_id)))
		t = MMGenExpect(name,'mmgen-tool',
				['-d',cfg['tmpdir'],'find_incog_data',f1,i_id])
		o = t.expect_getend('Incog data for ID {} found at offset '.format(i_id))
		os.unlink(f1)
		cmp_or_die(hincog_offset,int(o))

	def autosign(self,name): # tests everything except device detection, mount/unmount
		if skip_for_win(): return
		fdata = (	('btc',''),
					('bch',''),
					('ltc','litecoin'),
					('eth','ethereum'),
					('erc20','ethereum'),
					('etc','ethereum_classic'))
		tfns  = [cfgs['8']['ref_tx_file'][c][1] for c,d in fdata] + \
				[cfgs['8']['ref_tx_file'][c][0] for c,d in fdata]
		tfs = [os.path.join(ref_dir,d[1],fn) for d,fn in zip(fdata+fdata,tfns)]
		try: os.mkdir(os.path.join(cfg['tmpdir'],'tx'))
		except: pass
		for f,fn in zip(tfs,tfns):
			if fn: # use empty fn to skip file
				shutil.copyfile(f,os.path.join(cfg['tmpdir'],'tx',fn))
		# make a bad tx file
		with open(os.path.join(cfg['tmpdir'],'tx','bad.rawtx'),'w') as f:
			f.write('bad tx data')
		opts = ['--mountpoint='+cfg['tmpdir'],'--coins=btc,bch,ltc,eth']
		mn_fn = os.path.join(ref_dir,cfgs['8']['seed_id']+'.mmwords')
		mn = read_from_file(mn_fn).strip().split()

		t = MMGenExpect(name,'mmgen-autosign',opts+['gen_key'],extra_desc='(gen_key)')
		t.expect_getend('Wrote key file ')
		t.ok()

		t = MMGenExpect(name,'mmgen-autosign',opts+['setup'],extra_desc='(setup)')
		t.expect('words: ','3')
		t.expect('OK? (Y/n): ','\n')
		for i in range(24):
			t.expect('word #{}: '.format(i+1),mn[i]+'\n')
		wf = t.written_to_file('Autosign wallet')
		t.ok()

		t = MMGenExpect(name,'mmgen-autosign',opts+['wait'],extra_desc='(sign)')
		t.expect('11 transactions signed')
		t.expect('1 transaction failed to sign')
		t.expect('Waiting.')
		t.kill(2)
		t.ok(exit_val=1)

	# Saved reference file tests
	def ref_wallet_conv(self,name):
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		self.walletconv_in(name,wf,'MMGen wallet',pw=True,oo=True)

	def ref_mn_conv(self,name,ext='mmwords',desc='Mnemonic data'):
		wf = os.path.join(ref_dir,cfg['seed_id']+'.'+ext)
		self.walletconv_in(name,wf,desc,oo=True)

	def ref_seed_conv(self,name):
		self.ref_mn_conv(name,ext='mmseed',desc='Seed data')

	def ref_hex_conv(self,name):
		self.ref_mn_conv(name,ext='mmhex',desc='Hexadecimal seed data')

	def ref_brain_conv(self,name):
		uopts = ['-i','b','-p','1','-l',str(cfg['seed_len'])]
		self.walletconv_in(name,None,'brainwallet',uopts,oo=True)

	def ref_incog_conv(self,name,wfk='ic_wallet',in_fmt='i',desc='incognito data'):
		uopts = ['-i',in_fmt,'-p','1','-l',str(cfg['seed_len'])]
		wf = os.path.join(ref_dir,cfg[wfk])
		self.walletconv_in(name,wf,desc,uopts,oo=True,pw=True)

	def ref_incox_conv(self,name):
		self.ref_incog_conv(name,in_fmt='xi',wfk='ic_wallet_hex',desc='hex incognito data')

	def ref_hincog_conv(self,name,wfk='hic_wallet',add_uopts=[]):
		ic_f = os.path.join(ref_dir,cfg[wfk])
		uopts = ['-i','hi','-p','1','-l',str(cfg['seed_len'])] + add_uopts
		hi_opt = ['-H','{},{}'.format(ic_f,ref_wallet_incog_offset)]
		self.walletconv_in(name,None,'hidden incognito data',uopts+hi_opt,oo=True,pw=True)

	def ref_hincog_conv_old(self,name):
		self.ref_hincog_conv(name,wfk='hic_wallet_old',add_uopts=['-O'])

	def ref_wallet_conv_out(self,name):
		self.walletconv_out(name,'MMGen wallet','w',pw=True)

	def ref_mn_conv_out(self,name):
		self.walletconv_out(name,'mnemonic data','mn')

	def ref_seed_conv_out(self,name):
		self.walletconv_out(name,'seed data','seed')

	def ref_hex_conv_out(self,name):
		self.walletconv_out(name,'hexadecimal seed data','hexseed')

	def ref_incog_conv_out(self,name):
		self.walletconv_out(name,'incognito data',out_fmt='i',pw=True)

	def ref_incox_conv_out(self,name):
		self.walletconv_out(name,'hex incognito data',out_fmt='xi',pw=True)

	def ref_hincog_conv_out(self,name,extra_uopts=[]):
		ic_f = os.path.join(cfg['tmpdir'],hincog_fn)
		hi_parms = u'{},{}'.format(ic_f,ref_wallet_incog_offset)
		sl_parm = '-l' + str(cfg['seed_len'])
		self.walletconv_out(name,
			'hidden incognito data', 'hi',
			uopts=['-J',hi_parms,sl_parm] + extra_uopts,
			uopts_chk=['-H',hi_parms,sl_parm],
			pw=True
		)

	def ref_wallet_chk(self,name):
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		self.walletchk(name,wf,pf=None,pw=True,sid=cfg['seed_id'])

	def ref_ss_chk(self,name,ss=None):
		wf = os.path.join(ref_dir,'{}.{}'.format(cfg['seed_id'],ss.ext))
		self.walletchk(name,wf,pf=None,desc=ss.desc,sid=cfg['seed_id'])

	def ref_seed_chk(self,name):
		from mmgen.seed import SeedFile
		self.ref_ss_chk(name,ss=SeedFile)

	def ref_hex_chk(self,name):
		from mmgen.seed import HexSeedFile
		self.ref_ss_chk(name,ss=HexSeedFile)

	def ref_mn_chk(self,name):
		from mmgen.seed import Mnemonic
		self.ref_ss_chk(name,ss=Mnemonic)

	def ref_brain_chk(self,name,bw_file=ref_bw_file):
		wf = os.path.join(ref_dir,bw_file)
		add_args = ['-l{}'.format(cfg['seed_len']), '-p'+ref_bw_hash_preset]
		self.walletchk(name,wf,pf=None,add_args=add_args,
			desc='brainwallet',sid=cfg['ref_bw_seed_id'])

	def ref_brain_chk_spc3(self,name):
		self.ref_brain_chk(name,bw_file=ref_bw_file_spc)

	def ref_hincog_chk(self,name,desc='hidden incognito data'):
		for wtype,edesc,of_arg in ('hic_wallet','',[]), \
								('hic_wallet_old','(old format)',['-O']):
			ic_arg = ['-H{},{}'.format(os.path.join(ref_dir,cfg[wtype]),ref_wallet_incog_offset)]
			slarg = ['-l{} '.format(cfg['seed_len'])]
			hparg = ['-p1']
			if wtype == 'hic_wallet_old' and opt.profile: msg('')
			t = MMGenExpect(name,'mmgen-walletchk',
				slarg + hparg + of_arg + ic_arg,
				extra_desc=edesc)
			t.passphrase(desc,cfg['wpasswd'])
			if wtype == 'hic_wallet_old':
				t.expect('Is the Seed ID correct? (Y/n): ','\n')
			chk = t.expect_getend('Seed ID: ')
			t.close()
			cmp_or_die(cfg['seed_id'],chk)

	def ref_addrfile_chk(self,name,ftype='addr',coin=None,subdir=None,pfx=None,mmtype=None,add_args=[]):
		af_key = 'ref_{}file'.format(ftype)
		af_fn = cfg[af_key].format(pfx or altcoin_pfx,'' if coin else tn_ext)
		af = os.path.join(ref_dir,(subdir or ref_subdir,'')[ftype=='passwd'],af_fn)
		coin_arg = [] if coin == None else ['--coin='+coin]
		tool_cmd = ftype.replace('segwit','').replace('bech32','')+'file_chksum'
		t = MMGenExpect(name,'mmgen-tool',coin_arg+[tool_cmd,af]+add_args)
		if ftype == 'keyaddr':
			t.do_decrypt_ka_data(hp=ref_kafile_hash_preset,pw=ref_kafile_pass)
		o = t.read().strip().split('\n')[-1]
		rc = cfg[   'ref_' + ftype + 'file_chksum' +
					('_'+coin.lower() if coin else '') +
					('_'+mmtype if mmtype else '')]
		ref_chksum = rc if (ftype == 'passwd' or coin) else rc[g.proto.base_coin.lower()][g.testnet]
		cmp_or_die(ref_chksum,o)

	def ref_altcoin_addrgen(self,name,coin,mmtype,gen_what='addr',coin_suf=''):
		wf = os.path.join(ref_dir,cfg['seed_id']+'.mmwords')
		t = MMGenExpect(name,'mmgen-{}gen'.format(gen_what),
				['-Sq','--coin='+coin] +
				(['--type='+mmtype] if mmtype else []) +
				[wf,cfg['addr_idx_list']])
		if gen_what == 'key':
			t.expect('Encrypt key list? (y/N): ','N')
		chk = t.expect_getend(r'.* data checksum for \S*: ',regex=True)
		chk_ref = cfg['ref_{}addrfile_chksum_{}{}'.format(('','key')[gen_what=='key'],coin.lower(),coin_suf)]
		t.read()
		refcheck('{}list data checksum'.format(gen_what),chk,chk_ref)


	def ref_addrfile_gen_eth(self,name):
		self.ref_altcoin_addrgen(name,coin='ETH',mmtype='ethereum')

	def ref_addrfile_gen_etc(self,name):
		self.ref_altcoin_addrgen(name,coin='ETC',mmtype='ethereum')

	def ref_addrfile_gen_dash(self,name):
		self.ref_altcoin_addrgen(name,coin='DASH',mmtype='compressed')

	def ref_addrfile_gen_zec(self,name):
		self.ref_altcoin_addrgen(name,coin='ZEC',mmtype='compressed')

	def ref_addrfile_gen_zec_z(self,name):
		self.ref_altcoin_addrgen(name,coin='ZEC',mmtype='zcash_z',coin_suf='_z')

	def ref_addrfile_gen_xmr(self,name):
		self.ref_altcoin_addrgen(name,coin='XMR',mmtype='monero')


	def ref_keyaddrfile_gen_eth(self,name):
		self.ref_altcoin_addrgen(name,coin='ETH',mmtype='ethereum',gen_what='key')

	def ref_keyaddrfile_gen_etc(self,name):
		self.ref_altcoin_addrgen(name,coin='ETC',mmtype='ethereum',gen_what='key')

	def ref_keyaddrfile_gen_dash(self,name):
		self.ref_altcoin_addrgen(name,coin='DASH',mmtype='compressed',gen_what='key')

	def ref_keyaddrfile_gen_zec(self,name):
		self.ref_altcoin_addrgen(name,coin='ZEC',mmtype='compressed',gen_what='key')

	def ref_keyaddrfile_gen_zec_z(self,name):
		self.ref_altcoin_addrgen(name,coin='ZEC',mmtype='zcash_z',coin_suf='_z',gen_what='key')

	def ref_keyaddrfile_gen_xmr(self,name):
		self.ref_altcoin_addrgen(name,coin='XMR',mmtype='monero',gen_what='key')


	def ref_addrfile_chk_eth(self,name):
		self.ref_addrfile_chk(name,ftype='addr',coin='ETH',subdir='ethereum',pfx='-ETH')

	def ref_addrfile_chk_etc(self,name):
		self.ref_addrfile_chk(name,ftype='addr',coin='ETC',subdir='ethereum_classic',pfx='-ETC')

	def ref_addrfile_chk_dash(self,name):
		self.ref_addrfile_chk(name,ftype='addr',coin='DASH',subdir='dash',pfx='-DASH-C')

	def ref_addrfile_chk_zec(self,name):
		self.ref_addrfile_chk(name,ftype='addr',coin='ZEC',subdir='zcash',pfx='-ZEC-C')

	def ref_addrfile_chk_zec_z(self,name):
		if skip_for_win(): return
		self.ref_addrfile_chk(name,ftype='addr',coin='ZEC',subdir='zcash',pfx='-ZEC-Z',
								mmtype='z',add_args=['mmtype=zcash_z'])

	def ref_addrfile_chk_xmr(self,name):
		self.ref_addrfile_chk(name,ftype='addr',coin='XMR',subdir='monero',pfx='-XMR-M')


	def ref_keyaddrfile_chk_eth(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr',coin='ETH',subdir='ethereum',pfx='-ETH')

	def ref_keyaddrfile_chk_etc(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr',coin='ETC',subdir='ethereum_classic',pfx='-ETC')

	def ref_keyaddrfile_chk_dash(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr',coin='DASH',subdir='dash',pfx='-DASH-C')

	def ref_keyaddrfile_chk_zec(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr',coin='ZEC',subdir='zcash',pfx='-ZEC-C')

	def ref_keyaddrfile_chk_zec_z(self,name):
		if skip_for_win(): return
		self.ref_addrfile_chk(name,ftype='keyaddr',coin='ZEC',subdir='zcash',pfx='-ZEC-Z',
								mmtype='z',add_args=['mmtype=zcash_z'])

	def ref_keyaddrfile_chk_xmr(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr',coin='XMR',subdir='monero',pfx='-XMR-M')


	def ref_keyaddrfile_chk(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr')

	def ref_passwdfile_chk(self,name):
		self.ref_addrfile_chk(name,ftype='passwd')

	def ref_segwitaddrfile_chk(self,name):
		if not 'S' in g.proto.mmtypes:
			msg_r('Skipping {} (not supported)'.format(name)); ok()
		else:
			self.ref_addrfile_chk(name,ftype='segwitaddr')

	def ref_bech32addrfile_chk(self,name):
		if not 'B' in g.proto.mmtypes:
			msg_r('Skipping {} (not supported)'.format(name)); ok()
		else:
			self.ref_addrfile_chk(name,ftype='bech32addr')

#	def txcreate8(self,name,addrfile):
#		self.txcreate_common(name,sources=['8'])

	def ref_tx_chk(self,name):
		fn = cfg['ref_tx_file'][g.coin.lower()][bool(tn_ext)]
		if not fn: return
		tf = os.path.join(ref_dir,ref_subdir,fn)
		wf = dfl_words
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd'])
		pf = get_tmpfile_fn(cfg,pwfile)
		self.txsign(name,tf,wf,pf,save=False,has_label=True,do_passwd=False)

	def ref_tool_decrypt(self,name):
		f = os.path.join(ref_dir,ref_enc_fn)
		disable_debug()
		t = MMGenExpect(name,'mmgen-tool', ['-q','decrypt',f,'outfile=-','hash_preset=1'])
		restore_debug()
		t.passphrase('user data',tool_enc_passwd)
		t.expect(NL,nonl=True)
		import re
		o = re.sub('\r\n','\n',t.read())
		cmp_or_die(sample_text,o)

	# wallet conversion tests
	def walletconv_in(self,name,infile,desc,uopts=[],pw=False,oo=False):
		opts = ['-d',cfg['tmpdir'],'-o','words',usr_rand_arg]
		if_arg = [infile] if infile else []
		d = '(convert)'
		t = MMGenExpect(name,'mmgen-walletconv',opts+uopts+if_arg,extra_desc=d)
		t.license()
		if desc == 'brainwallet':
			t.expect('Enter brainwallet: ',ref_wallet_brainpass+'\n')
		if pw:
			t.passphrase(desc,cfg['wpasswd'])
			if name[:19] == 'ref_hincog_conv_old':
				t.expect('Is the Seed ID correct? (Y/n): ','\n')
			else:
				t.expect(['Passphrase is OK',' are correct'])
		# Output
		wf = t.written_to_file('Mnemonic data',oo=oo)
		t.close()
		t.ok()
		# back check of result
		if opt.profile: msg('')
		self.walletchk(name,wf,pf=None,
				desc='mnemonic data',
				sid=cfg['seed_id'],
				extra_desc='(check)'
				)

	def walletconv_out(self,name,desc,out_fmt='w',uopts=[],uopts_chk=[],pw=False):
		opts = ['-d',cfg['tmpdir'],'-p1','-o',out_fmt] + uopts
		infile = os.path.join(ref_dir,cfg['seed_id']+'.mmwords')
		t = MMGenExpect(name,'mmgen-walletconv',[usr_rand_arg]+opts+[infile],extra_desc='(convert)')

		add_args = ['-l{}'.format(cfg['seed_len'])]
		t.license()
		if pw:
			t.passphrase_new('new '+desc,cfg['wpasswd'])
			t.usr_rand(usr_rand_chars)
		if ' '.join(desc.split()[-2:]) == 'incognito data':
			for i in (1,2,3):
				t.expect('Generating encryption key from OS random data ')
		if desc == 'hidden incognito data':
			ret = t.expect(['Create? (Y/n): ',"'YES' to confirm: "])
			if ret == 0:
				t.send('\n')
				t.expect('Enter file size: ',str(hincog_bytes)+'\n')
			else:
				t.send('YES\n')
		if out_fmt == 'w': t.label()
		wf = t.written_to_file(capfirst(desc),oo=True)
		pf = None
		t.ok()

		if desc == 'hidden incognito data':
			add_args += uopts_chk
			wf = None
		if opt.profile: msg('')
		self.walletchk(name,wf,pf=pf,
			desc=desc,sid=cfg['seed_id'],pw=pw,
			add_args=add_args,
			extra_desc='(check)')

	def regtest_setup(self,name):
		os.environ['MMGEN_BOGUS_WALLET_DATA'] = ''
		if g.testnet:
			die(2,'--testnet option incompatible with regtest test suite')
		try: shutil.rmtree(os.path.join(data_dir,'regtest'))
		except: pass
		os.environ['MMGEN_TEST_SUITE'] = '' # mnemonic is piped to stdin, so stop being a terminal
		t = MMGenExpect(name,'mmgen-regtest',['-n','setup'])
		os.environ['MMGEN_TEST_SUITE'] = '1'
		for s in 'Starting setup','Creating','Mined','Creating','Creating','Setup complete':
			t.expect(s)
		t.ok()

	def regtest_walletgen(self,name,user):
		t = MMGenExpect(name,'mmgen-walletgen',['-q','-r0','-p1','--'+user])
		t.passphrase_new('new MMGen wallet',rt_pw)
		t.label()
		t.expect('move it to the data directory? (Y/n): ','y')
		t.written_to_file('MMGen wallet')
		t.ok()

	def regtest_walletgen_bob(self,name):   return self.regtest_walletgen(name,'bob')
	def regtest_walletgen_alice(self,name): return self.regtest_walletgen(name,'alice')

	@staticmethod
	def regtest_user_dir(user,coin=None):
		return os.path.join(data_dir,u'regtest',coin or g.coin.lower(),user)

	def regtest_user_sid(self,user):
		return os.path.basename(get_file_with_ext('mmdat',self.regtest_user_dir(user)))[:8]

	def regtest_addrgen(self,name,user,wf=None,passwd=rt_pw,addr_range='1-5'):
		from mmgen.addr import MMGenAddrType
		for mmtype in g.proto.mmtypes:
			t = MMGenExpect(name,'mmgen-addrgen',
				['--quiet','--'+user,'--type='+mmtype,u'--outdir={}'.format(self.regtest_user_dir(user))] +
				([],[wf])[bool(wf)] + [addr_range],
				extra_desc='({})'.format(MMGenAddrType.mmtypes[mmtype]['name']))
			t.passphrase('MMGen wallet',passwd)
			t.written_to_file('Addresses')
			t.ok()

	def regtest_addrgen_bob(self,name):   self.regtest_addrgen(name,'bob')
	def regtest_addrgen_alice(self,name): self.regtest_addrgen(name,'alice')

	def regtest_addrimport(self,name,user,sid=None,addr_range='1-5',num_addrs=5):
		id_strs = { 'legacy':'', 'compressed':'-C', 'segwit':'-S', 'bech32':'-B' }
		if not sid: sid = self.regtest_user_sid(user)
		from mmgen.addr import MMGenAddrType
		for mmtype in g.proto.mmtypes:
			desc = MMGenAddrType.mmtypes[mmtype]['name']
			fn = os.path.join(self.regtest_user_dir(user),
				u'{}{}{}[{}]{x}.testnet.addrs'.format(
					sid,altcoin_pfx,id_strs[desc],addr_range,
					x=u'-α' if g.debug_utf8 else ''))
			if mmtype == g.proto.mmtypes[0] and user == 'bob':
				psave = g.proto
				g.proto = CoinProtocol(g.coin,True)
				add_comments_to_addr_file(fn,fn,use_labels=True)
				g.proto = psave
			t = MMGenExpect(name,'mmgen-addrimport', ['--quiet','--'+user,'--batch',fn],extra_desc='('+desc+')')
			if g.debug:
				t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
			t.expect('Importing')
			t.expect('{} addresses imported'.format(num_addrs))
			t.ok()

	def regtest_addrimport_bob(self,name):   self.regtest_addrimport(name,'bob')
	def regtest_addrimport_alice(self,name): self.regtest_addrimport(name,'alice')

	def regtest_fund_wallet(self,name,user,mmtype,amt,sid=None,addr_range='1-5'):
		if not sid: sid = self.regtest_user_sid(user)
		addr = self.get_addr_from_regtest_addrlist(user,sid,mmtype,0,addr_range=addr_range)
		t = MMGenExpect(name,'mmgen-regtest', ['send',str(addr),str(amt)])
		t.expect('Sending {} {}'.format(amt,g.coin))
		t.expect('Mined 1 block')
		t.ok()

	def regtest_fund_bob(self,name):   self.regtest_fund_wallet(name,'bob','C',rtFundAmt)
	def regtest_fund_alice(self,name): self.regtest_fund_wallet(name,'alice',('L','S')[g.proto.cap('segwit')],rtFundAmt)

	def regtest_user_bal(self,name,user,bal):
		t = MMGenExpect(name,'mmgen-tool',['--'+user,'listaddresses','showempty=1'])
		total = t.expect_getend('TOTAL: ')
		cmp_or_die('{} {}'.format(bal,g.coin),total)

	def regtest_alice_bal1(self,name):
		return self.regtest_user_bal(name,'alice',rtFundAmt)

	def regtest_alice_bal2(self,name):
		return self.regtest_user_bal(name,'alice',rtBals[8])

	def regtest_bob_bal1(self,name):
		return self.regtest_user_bal(name,'bob',rtFundAmt)

	def regtest_bob_bal2(self,name):
		return self.regtest_user_bal(name,'bob',rtBals[0])

	def regtest_bob_bal3(self,name):
		return self.regtest_user_bal(name,'bob',rtBals[1])

	def regtest_bob_bal4(self,name):
		return self.regtest_user_bal(name,'bob',rtBals[2])

	def regtest_bob_bal5(self,name):
		return self.regtest_user_bal(name,'bob',rtBals[3])

	def regtest_bob_bal6(self,name):
		return self.regtest_user_bal(name,'bob',rtBals[7])

	def regtest_bob_bal5_getbalance(self,name):
		t_ext,t_mmgen = rtBals_gb[0],rtBals_gb[1]
		assert Decimal(t_ext) + Decimal(t_mmgen) == Decimal(rtBals[3])
		t = MMGenExpect(name,'mmgen-tool',['--bob','getbalance'])
		t.expect(r'\n[0-9A-F]{8}: .* '+t_mmgen,regex=True)
		t.expect(r'\nNon-MMGen: .* '+t_ext,regex=True)
		t.expect(r'\nTOTAL: .* '+rtBals[3],regex=True)
		t.read()
		t.ok()

	def regtest_bob_alice_bal(self,name):
		t = MMGenExpect(name,'mmgen-regtest',['get_balances'])
		t.expect('Switching')
		ret = t.expect_getend("Bob's balance:").strip()
		cmp_or_die(rtBals[4],ret,skip_ok=True)
		ret = t.expect_getend("Alice's balance:").strip()
		cmp_or_die(rtBals[5],ret,skip_ok=True)
		ret = t.expect_getend("Total balance:").strip()
		cmp_or_die(rtBals[6],ret,skip_ok=True)
		t.ok()

	def regtest_user_txdo(  self,name,user,fee,
							outputs_cl,
							outputs_list,
							extra_args=[],
							wf=None,
							pw=rt_pw,
							do_label=False,
							bad_locktime=False,
							full_tx_view=False):
		os.environ['MMGEN_BOGUS_SEND'] = ''
		t = MMGenExpect(name,'mmgen-txdo',
			['-d',cfg['tmpdir'],'-B','--'+user] +
			(['--tx-fee='+fee] if fee else []) +
			extra_args + ([],[wf])[bool(wf)] + outputs_cl)
		os.environ['MMGEN_BOGUS_SEND'] = '1'

		self.txcreate_ui_common(t,'txdo',
								menu=['M'],inputs=outputs_list,
								file_desc='Signed transaction',
								interactive_fee=(tx_fee,'')[bool(fee)],
								add_comment=ref_tx_label_jp,
								view='t',save=True)

		t.passphrase('MMGen wallet',pw)
		t.written_to_file('Signed transaction')
		self.do_confirm_send(t)
		s,exit_val = (('Transaction sent',0),("can't be included",1))[bad_locktime]
		t.expect(s)
		t.ok(exit_val)

	def regtest_bob_split1(self,name):
		sid = self.regtest_user_sid('bob')
		outputs_cl = [sid+':C:1,100', sid+':L:2,200',sid+':'+rtBobOp3]
		return self.regtest_user_txdo(name,'bob',rtFee[0],outputs_cl,'1',do_label=True,full_tx_view=True)

	def get_addr_from_regtest_addrlist(self,user,sid,mmtype,idx,addr_range='1-5'):
		id_str = { 'L':'', 'S':'-S', 'C':'-C', 'B':'-B' }[mmtype]
		ext = u'{}{}{}[{}]{x}.testnet.addrs'.format(
			sid,altcoin_pfx,id_str,addr_range,x=u'-α' if g.debug_utf8 else '')
		fn = get_file_with_ext(ext,self.regtest_user_dir(user),no_dot=True)
		silence()
		psave = g.proto
		g.proto = CoinProtocol(g.coin,True)
		if hasattr(g.proto,'bech32_hrp_rt'):
			g.proto.bech32_hrp = g.proto.bech32_hrp_rt
		addr = AddrList(fn).data[idx].addr
		g.proto = psave
		end_silence()
		return addr

	def create_tx_outputs(self,user,data):
		sid = self.regtest_user_sid(user)
		return [self.get_addr_from_regtest_addrlist(user,sid,mmtype,idx-1)+amt_str for mmtype,idx,amt_str in data]

	def regtest_bob_rbf_send(self,name):
		outputs_cl = self.create_tx_outputs('alice',(('L',1,',60'),('C',1,',40'))) # alice_sid:L:1, alice_sid:C:1
		outputs_cl += [self.regtest_user_sid('bob')+':'+rtBobOp3]
		return self.regtest_user_txdo(name,'bob',rtFee[1],outputs_cl,'3',
					extra_args=([],['--rbf'])[g.proto.cap('rbf')])

	def regtest_bob_send_non_mmgen(self,name):
		outputs_cl = self.create_tx_outputs('alice',(
			(('L','S')[g.proto.cap('segwit')],2,',10'),
			(('L','S')[g.proto.cap('segwit')],3,'')
		)) # alice_sid:S:2, alice_sid:S:3
		fn = os.path.join(cfg['tmpdir'],'non-mmgen.keys')
		return self.regtest_user_txdo(name,'bob',rtFee[3],outputs_cl,'1,4-10',
			extra_args=['--keys-from-file='+fn,'--vsize-adj=1.02'])

	def regtest_alice_send_estimatefee(self,name):
		outputs_cl = self.create_tx_outputs('bob',(('L',1,''),)) # bob_sid:L:1
		return self.regtest_user_txdo(name,'alice',None,outputs_cl,'1') # fee=None

	def regtest_user_txbump(self,name,user,txfile,fee,red_op):
		if not g.proto.cap('rbf'):
			msg('Skipping RBF'); return True
		os.environ['MMGEN_BOGUS_SEND'] = ''
		t = MMGenExpect(name,'mmgen-txbump',
			['-d',cfg['tmpdir'],'--send','--'+user,'--tx-fee='+fee,'--output-to-reduce='+red_op] + [txfile])
		os.environ['MMGEN_BOGUS_SEND'] = '1'
		t.expect('OK? (Y/n): ','y') # output OK?
		t.expect('OK? (Y/n): ','y') # fee OK?
		t.do_comment(False,has_label=True)
		t.passphrase('MMGen wallet',rt_pw)
		t.written_to_file('Signed transaction')
		self.txsend_ui_common(t,'txdo',bogus_send=False,file_desc='Signed transaction')
		t.read()
		t.ok()

	def regtest_bob_rbf_bump(self,name):
		ext = u',{}]{x}.testnet.sigtx'.format(rtFee[1][:-1],x=u'-α' if g.debug_utf8 else '')
		txfile = get_file_with_ext(ext,cfg['tmpdir'],delete=False,no_dot=True)
		return self.regtest_user_txbump(name,'bob',txfile,rtFee[2],'c')

	def regtest_generate(self,name,coin=None,num_blocks=1):
		int(num_blocks)
		if coin: opt.coin = coin
		t = MMGenExpect(name,'mmgen-regtest',['generate',str(num_blocks)])
		t.expect('Mined {} block'.format(num_blocks))
		t.ok()

	def regtest_get_mempool(self,name):
		disable_debug()
		ret = MMGenExpect(name,'mmgen-regtest',['show_mempool']).read()
		restore_debug()
		from ast import literal_eval
		return literal_eval(ret)

	def regtest_get_mempool1(self,name):
		mp = self.regtest_get_mempool(name)
		if len(mp) != 1:
			rdie(2,'Mempool has more or less than one TX!')
		write_to_tmpfile(cfg,'rbf_txid',mp[0]+'\n')
		ok()

	def regtest_get_mempool2(self,name):
		if not g.proto.cap('rbf'):
			msg('Skipping post-RBF mempool check'); return True
		mp = self.regtest_get_mempool(name)
		if len(mp) != 1:
			rdie(2,'Mempool has more or less than one TX!')
		chk = read_from_tmpfile(cfg,'rbf_txid')
		if chk.strip() == mp[0]:
			rdie(2,'TX in mempool has not changed!  RBF bump failed')
		ok()

	@staticmethod
	def gen_pairs(n):
		disable_debug()
		ret = [subprocess.check_output(
						['python',os.path.join('cmds','mmgen-tool'),'--testnet=1'] +
						(['--type=compressed'],[])[i==0] +
						['-r0','randpair']
					).split() for i in range(n)]
		restore_debug()
		return ret

	def regtest_bob_pre_import(self,name):
		pairs = self.gen_pairs(5)
		write_to_tmpfile(cfg,u'non-mmgen.keys','\n'.join([a[0] for a in pairs])+'\n')
		write_to_tmpfile(cfg,u'non-mmgen.addrs','\n'.join([a[1] for a in pairs])+'\n')
		return self.regtest_user_txdo(name,'bob',rtFee[4],[pairs[0][1]],'3')

	def regtest_user_import(self,name,user,args):
		t = MMGenExpect(name,'mmgen-addrimport',['--quiet','--'+user]+args)
		if g.debug:
			t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
		t.expect('Importing')
		t.expect('OK')
		t.ok()

	def regtest_bob_import_addr(self,name):
		addr = read_from_tmpfile(cfg,u'non-mmgen.addrs').split()[0]
		return self.regtest_user_import(name,'bob',['--rescan','--address='+addr])

	def regtest_bob_import_list(self,name):
		fn = os.path.join(cfg['tmpdir'],u'non-mmgen.addrs')
		return self.regtest_user_import(name,'bob',['--addrlist',fn])

	def regtest_bob_split2(self,name):
		addrs = read_from_tmpfile(cfg,u'non-mmgen.addrs').split()
		amts = (1.12345678,2.87654321,3.33443344,4.00990099,5.43214321)
		outputs1 = map('{},{}'.format,addrs,amts)
		sid = self.regtest_user_sid('bob')
		l1,l2 = (':S',':B') if 'B' in g.proto.mmtypes else (':S',':S') if g.proto.cap('segwit') else (':L',':L')
		outputs2 = [sid+':C:2,6.333', sid+':L:3,6.667',sid+l1+':4,0.123',sid+l2+':5']
		return self.regtest_user_txdo(name,'bob',rtFee[5],outputs1+outputs2,'1-2')

	def regtest_user_add_label(self,name,user,addr,label):
		t = MMGenExpect(name,'mmgen-tool',['--'+user,'add_label',addr,label])
		t.expect('Added label.*in tracking wallet',regex=True)
		t.ok()

	def regtest_user_remove_label(self,name,user,addr):
		t = MMGenExpect(name,'mmgen-tool',['--'+user,'remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		t.ok()

# 	utf8_label     =  u'Edited label (40 characters, UTF8/JP) 月へ' # '\xe6\x9c\x88\xe3\x81\xb8' (Jp.)
# 	utf8_label_pat = ur'Edited label \(40 characters, UTF8/JP\) ......'
	utf8_label     = ref_tx_label_zh[:40]
	utf8_label_pat = utf8_label

	def regtest_bob_add_label(self,name):
		sid = self.regtest_user_sid('bob')
		return self.regtest_user_add_label(name,'bob',sid+':C:1',self.utf8_label)

	def regtest_alice_add_label1(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_add_label(name,'alice',sid+':C:1',u'Original Label - 月へ')

	def regtest_alice_add_label2(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_add_label(name,'alice',sid+':C:1','Replacement Label')

	def regtest_alice_add_label_coinaddr(self,name):
		mmaddr = self.regtest_user_sid('alice') + ':C:2'
		t = MMGenExpect(name,'mmgen-tool',['--alice','listaddress',mmaddr],no_msg=True)
		btcaddr = [i for i in t.read().splitlines() if i.lstrip()[0:len(mmaddr)] == mmaddr][0].split()[1]
		return self.regtest_user_add_label(name,'alice',btcaddr,'Label added using coin address')

	def regtest_alice_chk_label_coinaddr(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_chk_label(name,'alice',sid+':C:2','Label added using coin address')

	def regtest_alice_add_label_badaddr(self,name,addr,reply):
		t = MMGenExpect(name,'mmgen-tool',['--alice','add_label',addr,'(none)'])
		t.expect(reply.encode('utf8'),regex=True)
		t.ok()

	def regtest_alice_add_label_badaddr1(self,name):
		return self.regtest_alice_add_label_badaddr(name,rt_pw,u'Invalid coin address for this chain: '+rt_pw)

	def regtest_alice_add_label_badaddr2(self,name):
		addr = g.proto.pubhash2addr('00'*20,False) # mainnet zero address
		return self.regtest_alice_add_label_badaddr(name,addr,'Invalid coin address for this chain: '+addr)

	def regtest_alice_add_label_badaddr3(self,name):
		addr = self.regtest_user_sid('alice') + ':C:123'
		return self.regtest_alice_add_label_badaddr(name,addr,
			"MMGen address '{}' not found in tracking wallet".format(addr))

	def regtest_alice_add_label_badaddr4(self,name):
		addr = CoinProtocol(g.coin,True).pubhash2addr('00'*20,False) # testnet zero address
		return self.regtest_alice_add_label_badaddr(name,addr,
			"Address '{}' not found in tracking wallet".format(addr))

	def regtest_alice_add_label_rpcfail(self,name):
		addr = self.regtest_user_sid('alice') + ':C:2'
		os.environ['MMGEN_RPC_FAIL_ON_COMMAND'] = 'importaddress'
		self.regtest_alice_add_label_badaddr(name,addr,'Label could not be added')
		os.environ['MMGEN_RPC_FAIL_ON_COMMAND'] = ''

	def regtest_alice_remove_label1(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_remove_label(name,'alice',sid+':C:1')

	def regtest_user_chk_label(self,name,user,addr,label,label_pat=None):
		t = MMGenExpect(name,'mmgen-tool',['--'+user,'listaddresses','all_labels=1'])
		t.expect(r'{}\s+\S{{30}}\S+\s+{}\s+'.format(addr,(label_pat or label).encode('utf8')),regex=True)
		t.ok()

	def regtest_alice_chk_label1(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_chk_label(name,'alice',sid+':C:1',u'Original Label - 月へ')

	def regtest_alice_chk_label2(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_chk_label(name,'alice',sid+':C:1','Replacement Label')

	def regtest_alice_edit_label1(self,name):
		return self.regtest_user_edit_label(name,'alice','1',self.utf8_label)

	def regtest_alice_chk_label3(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_chk_label(name,'alice',sid+':C:1',self.utf8_label,label_pat=self.utf8_label_pat)

	def regtest_alice_chk_label4(self,name):
		sid = self.regtest_user_sid('alice')
		return self.regtest_user_chk_label(name,'alice',sid+':C:1','-')

	def regtest_user_edit_label(self,name,user,output,label):
		t = MMGenExpect(name,'mmgen-txcreate',['-B','--'+user,'-i'])
		t.expect(r"'q'=quit view, .*?:.",'M',regex=True)
		t.expect(r"'q'=quit view, .*?:.",'l',regex=True)
		t.expect(r"Enter unspent.*return to main menu\):.",output+'\n',regex=True)
		t.expect(r"Enter label text.*return to main menu\):.",label+'\n',regex=True)
		t.expect(r"'q'=quit view, .*?:.",'q',regex=True)
		t.ok()

	def regtest_stop(self,name):
		t = MMGenExpect(name,'mmgen-regtest',['stop'])
		t.ok()

	def regtest_split_setup(self,name):
		if g.coin != 'BTC': die(1,'Test valid only for coin BTC')
		opt.coin = 'BTC'
		return self.regtest_setup(name)

	def regtest_split_fork(self,name):
		opt.coin = 'B2X'
		t = MMGenExpect(name,'mmgen-regtest',['fork','btc'])
		t.expect('Creating fork from coin')
		t.expect('successfully created')
		t.ok()

	def regtest_split_start(self,name,coin):
		opt.coin = coin
		t = MMGenExpect(name,'mmgen-regtest',['bob'])
		t.expect('Starting')
		t.expect('done')
		t.ok()

	def regtest_split_start_btc(self,name): self.regtest_split_start(name,coin='BTC')
	def regtest_split_start_b2x(self,name): self.regtest_split_start(name,coin='B2X')
	def regtest_split_gen_btc(self,name):   self.regtest_generate(name,coin='BTC')
	def regtest_split_gen_b2x(self,name):   self.regtest_generate(name,coin='B2X',num_blocks=100)
	def regtest_split_gen_b2x2(self,name):  self.regtest_generate(name,coin='B2X')

	def regtest_split_do_split(self,name):
		opt.coin = 'B2X'
		sid = self.regtest_user_sid('bob')
		t = MMGenExpect(name,'mmgen-split',[
			'--bob',
			'--outdir='+cfg['tmpdir'],
			'--tx-fees=0.0001,0.0003',
			sid+':S:1',sid+':S:2'])
		t.expect(r"'q'=quit view, .*?:.",'q', regex=True)
		t.expect('outputs to spend: ','1\n')

		for tx in ('timelocked','split'):
			for q in ('fee','change'): t.expect('OK? (Y/n): ','y')
			t.do_comment(False)
			t.view_tx('t')

		t.written_to_file('Long chain (timelocked) transaction')
		t.written_to_file('Short chain transaction')
		t.ok()

	def regtest_split_sign(self,name,coin,ext):
		wf = get_file_with_ext('mmdat',self.regtest_user_dir('bob',coin=coin.lower()))
		txfile = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True)
		opt.coin = coin
		self.txsign(name,txfile,wf,extra_opts=['--bob'])

	def regtest_split_sign_b2x(self,name):
		return self.regtest_split_sign(name,coin='B2X',ext='533].rawtx')

	def regtest_split_sign_btc(self,name):
		return self.regtest_split_sign(name,coin='BTC',ext='9997].rawtx')

	def regtest_split_send(self,name,coin,ext):
		opt.coin = coin
		txfile = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True)
		self.txsend(name,txfile,bogus_send=False,extra_opts=['--bob'])

	def regtest_split_send_b2x(self,name):
		return self.regtest_split_send(name,coin='B2X',ext='533].sigtx')

	def regtest_split_send_btc(self,name):
		return self.regtest_split_send(name,coin='BTC',ext='9997].sigtx')

	def regtest_split_txdo_timelock(self,name,coin,locktime,bad_locktime):
		opt.coin = coin
		sid = self.regtest_user_sid('bob')
		self.regtest_user_txdo(
			name,'bob','0.0001',[sid+':S:5'],'1',pw=rt_pw,
			extra_args=['--locktime='+str(locktime)],
			bad_locktime=bad_locktime)

	def regtest_split_txdo_timelock_bad_btc(self,name):
		self.regtest_split_txdo_timelock(name,'BTC',locktime=8888,bad_locktime=True)
	def regtest_split_txdo_timelock_good_btc(self,name):
		self.regtest_split_txdo_timelock(name,'BTC',locktime=1321009871,bad_locktime=False)
	def regtest_split_txdo_timelock_bad_b2x(self,name):
		self.regtest_split_txdo_timelock(name,'B2X',locktime=8888,bad_locktime=True)
	def regtest_split_txdo_timelock_good_b2x(self,name):
		self.regtest_split_txdo_timelock(name,'B2X',locktime=1321009871,bad_locktime=False)

	def ethdev_setup(self,name):
		os.environ['MMGEN_BOGUS_WALLET_DATA'] = ''
		lf_arg = '--log-file=' + os.path.join(data_dir,'parity.log')
		try:
			pid = subprocess.check_output(['pgrep','-af','parity.*{}'.format(lf_arg)]).split()[0]
			os.kill(int(pid),9)
		except: pass
		# '--base-path' doesn't work together with daemon mode, so we have to clobber the main dev chain
		dc_dir = os.path.join(os.environ['HOME'],'.local/share/io.parity.ethereum/chains/DevelopmentChain')
		shutil.rmtree(dc_dir,ignore_errors=True)
		bdir = os.path.join(data_dir,'parity')
		try: os.mkdir(bdir)
		except: pass
		pid_fn = get_tmpfile_fn(cfg,cfg['parity_pidfile'])
		MMGenExpect(name,'',msg_only=True)
		subprocess.check_call(['parity',lf_arg,'--ports-shift=4','--config=dev','daemon',pid_fn]) # port 8549
		time.sleep(1) # race condition
		pid = read_from_tmpfile(cfg,cfg['parity_pidfile'])
		ok()

	def ethdev_addrgen(self,name,addrs='1-3,11-13,21-23'):
		from mmgen.addr import MMGenAddrType
		t = MMGenExpect(name,'mmgen-addrgen', eth_args() + [dfl_words,addrs])
		t.written_to_file('Addresses')
		t.read()
		t.ok()

	def ethdev_addrimport(self,name,ext='21-23].addrs',expect='9/9',add_args=[]):
		fn = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True,delete=False)
		t = MMGenExpect(name,'mmgen-addrimport', eth_args()[1:] + add_args + [fn])
		if g.debug: t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
		t.expect('Importing')
		t.expect(expect)
		t.read()
		t.ok()

	def ethdev_addrimport_one_addr(self,name,addr=None,extra_args=[]):
		t = MMGenExpect(name,'mmgen-addrimport', eth_args()[1:] + extra_args + ['--address='+addr])
		t.expect('OK')
		t.ok()

	def ethdev_addrimport_dev_addr(self,name):
		self.ethdev_addrimport_one_addr(name,addr=eth_addr)

	def ethdev_addrimport_burn_addr(self,name):
		self.ethdev_addrimport_one_addr(name,addr=eth_burn_addr)

	def ethdev_txcreate(self,name,args=[],menu=[],acct='1',non_mmgen_inputs=0,
						interactive_fee='50G',
						fee_res='0.00105 {} (50 gas price in Gwei)'.format(g.coin),
						fee_desc = 'gas price'):
		t = MMGenExpect(name,'mmgen-txcreate', eth_args() + ['-B'] + args)
		t.expect(r"'q'=quit view, .*?:.",'p', regex=True)
		t.written_to_file('Account balances listing')
		self.txcreate_ui_common(t,name,
								menu=menu,
								input_sels_prompt='to spend from',
								inputs=acct,file_desc='Ethereum transaction',
								bad_input_sels=True,non_mmgen_inputs=non_mmgen_inputs,
								interactive_fee=interactive_fee,fee_res=fee_res,fee_desc=fee_desc,
								add_comment=ref_tx_label_jp)

	def ethdev_txsign(self,name,ni=False,ext='.rawtx',add_args=[]):
		key_fn = get_tmpfile_fn(cfg,cfg['parity_keyfile'])
		write_to_tmpfile(cfg,cfg['parity_keyfile'],eth_key+'\n')
		tx_fn = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True)
		t = MMGenExpect(name,'mmgen-txsign',eth_args()+add_args + ([],['--yes'])[ni] + ['-k',key_fn,tx_fn,dfl_words])
		self.txsign_ui_common(t,name,ni=ni,has_label=True)

	def ethdev_txsend(self,name,ni=False,bogus_send=False,ext='.sigtx',add_args=[]):
		tx_fn = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True)
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = ''
		t = MMGenExpect(name,'mmgen-txsend', eth_args()+add_args + [tx_fn])
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = '1'
		self.txsend_ui_common(t,name,quiet=True,bogus_send=bogus_send,has_label=True)

	def ethdev_txcreate1(self,name):
		menu = ['a','d','A','r','M','D','e','m','m']
		args = ['98831F3A:E:1,123.456']
		return self.ethdev_txcreate(name,args=args,menu=menu,acct='1',non_mmgen_inputs=1)

	def ethdev_txsign1(self,name): self.ethdev_txsign(name)
	def ethdev_txsign1_ni(self,name): self.ethdev_txsign(name,ni=True)
	def ethdev_txsend1(self,name): self.ethdev_txsend(name)

	def ethdev_txcreate2(self,name):
		args = ['98831F3A:E:11,1.234']
		return self.ethdev_txcreate(name,args=args,acct='10',non_mmgen_inputs=1)
	def ethdev_txsign2(self,name): self.ethdev_txsign(name,ni=True,ext='1.234,50000].rawtx')
	def ethdev_txsend2(self,name): self.ethdev_txsend(name,ext='1.234,50000].sigtx')

	def ethdev_txcreate3(self,name):
		args = ['98831F3A:E:21,2.345']
		return self.ethdev_txcreate(name,args=args,acct='10',non_mmgen_inputs=1)
	def ethdev_txsign3(self,name): self.ethdev_txsign(name,ni=True,ext='2.345,50000].rawtx')
	def ethdev_txsend3(self,name): self.ethdev_txsend(name,ext='2.345,50000].sigtx')

	def ethdev_tx_status(self,name,ext,expect_str):
		tx_fn = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True)
		t = MMGenExpect(name,'mmgen-txsend', eth_args() + ['--status',tx_fn])
		t.expect(expect_str)
		t.read()
		t.ok()

	def ethdev_tx_status1(self,name):
		self.ethdev_tx_status(name,ext='2.345,50000].sigtx',expect_str='has 1 confirmation')

	def ethdev_txcreate4(self,name):
		args = ['98831F3A:E:2,23.45495']
		interactive_fee='40G'
		fee_res='0.00084 {} (40 gas price in Gwei)'.format(g.coin)
		return self.ethdev_txcreate(name,args=args,acct='1',non_mmgen_inputs=0,
					interactive_fee=interactive_fee,fee_res=fee_res)

	def ethdev_txbump(self,name,ext=',40000].rawtx',fee='50G',add_args=[]):
		tx_fn = get_file_with_ext(ext,cfg['tmpdir'],no_dot=True)
		t = MMGenExpect(name,'mmgen-txbump', eth_args() + add_args + ['--yes',tx_fn])
		t.expect('or gas price: ',fee+'\n')
		t.read()
		t.ok()

	def ethdev_txsign4(self,name): self.ethdev_txsign(name,ni=True,ext='.45495,50000].rawtx')
	def ethdev_txsend4(self,name): self.ethdev_txsend(name,ext='.45495,50000].sigtx')

	def ethdev_txcreate5(self,name):
		args = [eth_burn_addr + ','+eth_amt1]
		return self.ethdev_txcreate(name,args=args,acct='10',non_mmgen_inputs=1)
	def ethdev_txsign5(self,name): self.ethdev_txsign(name,ni=True,ext=eth_amt1+',50000].rawtx')
	def ethdev_txsend5(self,name): self.ethdev_txsend(name,ext=eth_amt1+',50000].sigtx')

	def ethdev_bal(self,name,expect_str=''):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + ['twview'])
		t.expect(expect_str,regex=True)
		t.read()
		t.ok()

	def ethdev_bal_getbalance(self,name,t_non_mmgen='',t_mmgen='',extra_args=[]):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + extra_args + ['getbalance'])
		t.expect(r'\n[0-9A-F]{8}: .* '+t_mmgen,regex=True)
		t.expect(r'\nNon-MMGen: .* '+t_non_mmgen,regex=True)
		total = t.expect_getend(r'\nTOTAL:\s+',regex=True).split()[0]
		t.read()
		assert Decimal(t_non_mmgen) + Decimal(t_mmgen) == Decimal(total)
		t.ok()

	def ethdev_bal1(self,name,expect_str=''):
		self.ethdev_bal(name,expect_str=r'98831F3A:E:2\s+23\.45495\s+')

	def ethdev_add_label(self,name,addr='98831F3A:E:3',lbl=utf8_label):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + ['add_label',addr,lbl])
		t.expect('Added label.*in tracking wallet',regex=True)
		t.ok()

	def ethdev_chk_label(self,name,addr='98831F3A:E:3',label_pat=utf8_label_pat):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + ['listaddresses','all_labels=1'])
		t.expect(r'{}\s+\S{{30}}\S+\s+{}\s+'.format(addr,(label_pat or label).encode('utf8')),regex=True)
		t.ok()

	def ethdev_remove_label(self,name,addr='98831F3A:E:3'):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + ['remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		t.ok()

	def init_ethdev_common(self):
		g.testnet = True
		init_coin(g.coin)
		g.proto.rpc_port = 8549
		rpc_init()

	def ethdev_token_compile(self,name,token_data={}):
		MMGenExpect(name,'',msg_only=True)
		cmd_args = ['--{}={}'.format(k,v) for k,v in token_data.items()]
		silence()
		imsg("Compiling solidity token contract '{}' with 'solc'".format(token_data['symbol']))
		cmd = ['scripts/create-token.py','--coin='+g.coin,'--outdir='+cfg['tmpdir']] + cmd_args + [eth_addr]
		imsg("Executing: {}".format(' '.join(cmd)))
		subprocess.check_output(cmd)
		imsg("ERC20 token '{}' compiled".format(token_data['symbol']))
		end_silence()
		ok()

	def ethdev_token_compile1(self,name):
		token_data = { 'name':'MMGen Token 1', 'symbol':'MM1', 'supply':10**26, 'decimals':18 }
		self.ethdev_token_compile(name,token_data)

	def ethdev_token_compile2(self,name):
		token_data = { 'name':'MMGen Token 2', 'symbol':'MM2', 'supply':10**18, 'decimals':10 }
		self.ethdev_token_compile(name,token_data)

	def ethdev_token_deploy(self,name,num,key,gas,mmgen_cmd='txdo',tx_fee='8G'):
		self.init_ethdev_common()
		key_fn = get_tmpfile_fn(cfg,cfg['parity_keyfile'])
		fn = os.path.join(cfg['tmpdir'],key+'.bin')
		os.environ['MMGEN_BOGUS_SEND'] = ''
		args = ['-B','--tx-fee='+tx_fee,'--tx-gas={}'.format(gas),'--contract-data='+fn,'--inputs='+eth_addr,'--yes']
		if mmgen_cmd == 'txdo': args += ['-k',key_fn]
		t = MMGenExpect(name,'mmgen-'+mmgen_cmd, eth_args() + args)
		if mmgen_cmd == 'txcreate':
			t.written_to_file('Ethereum transaction')
			tx_fn = get_file_with_ext('[0,8000].rawtx',cfg['tmpdir'],no_dot=True)
			t = MMGenExpect(name,'mmgen-txsign', eth_args() + ['--yes','-k',key_fn,tx_fn],no_msg=True)
			self.txsign_ui_common(t,name,ni=True,no_ok=True)
			tx_fn = tx_fn.replace('.rawtx','.sigtx')
			t = MMGenExpect(name,'mmgen-txsend', eth_args() + [tx_fn],no_msg=True)

		os.environ['MMGEN_BOGUS_SEND'] = '1'
		txid = self.txsend_ui_common(t,mmgen_cmd,quiet=True,bogus_send=False,no_ok=True)
		addr = t.expect_getend('Contract address: ')
		from mmgen.altcoins.eth.tx import EthereumMMGenTX as etx
		assert etx.get_exec_status(txid,True) != 0,"Contract '{}:{}' failed to execute. Aborting".format(num,key)
		if key == 'Token':
			write_to_tmpfile(cfg,'token_addr{}'.format(num),addr+'\n')
			silence()
			imsg('\nToken #{} ({}) deployed!'.format(num,addr))
			end_silence()
		t.ok()

	def ethdev_token_deploy1a(self,name): self.ethdev_token_deploy(name,num=1,key='SafeMath',gas=200000)
	def ethdev_token_deploy1b(self,name): self.ethdev_token_deploy(name,num=1,key='Owned',gas=250000)
	def ethdev_token_deploy1c(self,name): self.ethdev_token_deploy(name,num=1,key='Token',gas=1100000,tx_fee='7G')

	def ethdev_tx_status2(self,name):
		self.ethdev_tx_status(name,ext=g.coin+'[0,7000].sigtx',expect_str='successfully executed')

	def ethdev_token_deploy2a(self,name): self.ethdev_token_deploy(name,num=2,key='SafeMath',gas=200000)
	def ethdev_token_deploy2b(self,name): self.ethdev_token_deploy(name,num=2,key='Owned',gas=250000)
	def ethdev_token_deploy2c(self,name): self.ethdev_token_deploy(name,num=2,key='Token',gas=1100000)

	def ethdev_contract_deploy(self,name): # test create,sign,send
		self.ethdev_token_deploy(name,num=2,key='SafeMath',gas=1100000,mmgen_cmd='txcreate')

	def ethdev_token_transfer_funds(self,name):
		MMGenExpect(name,'',msg_only=True)
		sid = cfgs['8']['seed_id']
		cmd = lambda i: ['mmgen-tool','--coin='+g.coin,'gen_addr','{}:E:{}'.format(sid,i),'wallet='+dfl_words]
		silence()
		usr_addrs = [subprocess.check_output(cmd(i),stderr=sys.stderr).strip() for i in 11,21]
		self.init_ethdev_common()
		from mmgen.altcoins.eth.contract import Token
		from mmgen.altcoins.eth.tx import EthereumMMGenTX as etx
		for i in range(2):
			tk = Token(read_from_tmpfile(cfg,'token_addr{}'.format(i+1)).strip())
			imsg('\n'+tk.info())
			txid = tk.transfer(eth_addr,usr_addrs[i],1000,eth_key,
								start_gas=ETHAmt(60000,'wei'),gasPrice=ETHAmt(8,'Gwei'))
			assert etx.get_exec_status(txid,True) != 0,'Transfer of token funds failed. Aborting'
			imsg('dev token balance: {}'.format(tk.balance(eth_addr)))
			imsg('usr{} token balance: {}'.format(i+1,tk.balance(usr_addrs[i])))
		end_silence()
		ok()

	def ethdev_token_addrgen(self,name):
		self.ethdev_addrgen(name,addrs='11-13')
		self.ethdev_addrgen(name,addrs='21-23')

	def ethdev_token_addrimport(self,name):
		for n,r in ('1','11-13'),('2','21-23'):
			tk_addr = read_from_tmpfile(cfg,'token_addr'+n).strip()
			self.ethdev_addrimport(name,ext='['+r+'].addrs',expect='3/3',add_args=['--token='+tk_addr])

	def ethdev_token_txcreate(self,name,args=[],token='',inputs='1',fee='50G'):
		t = MMGenExpect(name,'mmgen-txcreate', eth_args() + ['--token='+token,'-B','--tx-fee='+fee] + args)
		self.txcreate_ui_common(t,name,menu=[],
								input_sels_prompt='to spend from',
								inputs=inputs,file_desc='Ethereum token transaction',
								add_comment=ref_tx_label_lat_cyr_gr)
		return t
	def ethdev_token_txsign(self,name,ext='',token=''):
		self.ethdev_txsign(name,ni=True,ext=ext,add_args=['--token='+token])
	def ethdev_token_txsend(self,name,ext='',token=''):
		self.ethdev_txsend(name,ext=ext,add_args=['--token=mm1'])

	def ethdev_token_txcreate1(self,name):
		return self.ethdev_token_txcreate(name,args=['98831F3A:E:12,1.23456'],token='mm1')
	def ethdev_token_txsign1(self,name):
		self.ethdev_token_txsign(name,ext='1.23456,50000].rawtx',token='mm1')
	def ethdev_token_txsend1(self,name):
		self.ethdev_token_txsend(name,ext='1.23456,50000].sigtx',token='mm1')

	def ethdev_twview(self,name,args,expect_str):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + args + ['twview'])
		t.expect(expect_str,regex=True)
		t.read()
		t.ok()

	bal_corr = Decimal('0.0000032') # gas use varies for token sends!
	def ethdev_token_twview1(self,name):
		ebal = Decimal('1.2314236')
		if g.coin == 'ETC': ebal += self.bal_corr
		s = '98831F3A:E:11\s+998.76544\s+' + str(ebal)
		return self.ethdev_twview(name,args=['--token=mm1'],expect_str=s)

	def ethdev_token_txcreate2(self,name):
		return self.ethdev_token_txcreate(name,args=[eth_burn_addr+','+eth_amt2],token='mm1')

	def ethdev_token_txbump(self,name):
		self.ethdev_txbump(name,ext=eth_amt2+',50000].rawtx',fee='56G',add_args=['--token=mm1'])

	def ethdev_token_txsign2(self,name):
		self.ethdev_token_txsign(name,ext=eth_amt2+',50000].rawtx',token='mm1')
	def ethdev_token_txsend2(self,name):
		self.ethdev_token_txsend(name,ext=eth_amt2+',50000].sigtx',token='mm1')

	def ethdev_del_dev_addr(self,name):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + ['remove_address',eth_addr])
		t.read() # TODO
		t.ok()

	def ethdev_addrimport_token_burn_addr(self,name):
		self.ethdev_addrimport_one_addr(name,addr=eth_burn_addr,extra_args=['--token=mm1'])

	def ethdev_bal2(self,name,expect_str=''):
		self.ethdev_bal(name,expect_str=r'deadbeef.* 999999.12345689012345678')

	def ethdev_bal2_getbalance(self,name,t_non_mmgen='',t_mmgen=''):
		ebal = Decimal('127.0287876')
		if g.coin == 'ETC': ebal += self.bal_corr
		self.ethdev_bal_getbalance(name,t_non_mmgen='999999.12345689012345678',t_mmgen=str(ebal))

	def ethdev_token_bal(self,name,expect_str):
		t = MMGenExpect(name,'mmgen-tool', eth_args() + ['--token=mm1','twview','wide=1'])
		t.expect(expect_str,regex=True)
		t.read()
		t.ok()

	def ethdev_token_bal1(self,name):
		self.ethdev_token_bal(name,expect_str=r'deadbeef.* '+eth_amt2)

	def ethdev_token_bal_getbalance(self,name):
		self.ethdev_bal_getbalance(name,
			t_non_mmgen='888.111122223333444455',t_mmgen='111.888877776666555545',extra_args=['--token=mm1'])

	def ethdev_txcreate_noamt(self,name):
		return self.ethdev_txcreate(name,args=['98831F3A:E:12'])
	def ethdev_txsign_noamt(self,name):
		self.ethdev_txsign(name,ext='99.99895,50000].rawtx')
	def ethdev_txsend_noamt(self,name):
		self.ethdev_txsend(name,ext='99.99895,50000].sigtx')

	def ethdev_token_bal2(self,name):
		self.ethdev_token_bal(name,expect_str=r'98831F3A:E:12\s+1.23456\s+99.99895\s')

	def ethdev_bal3(self,name,expect_str=''):
		self.ethdev_bal(name,expect_str=r'98831F3A:E:1\s+0\n')

	def ethdev_token_txcreate_noamt(self,name):
		return self.ethdev_token_txcreate(name,args=['98831F3A:E:13'],token='mm1',inputs='2',fee='51G')
	def ethdev_token_txsign_noamt(self,name):
		self.ethdev_token_txsign(name,ext='1.23456,51000].rawtx',token='mm1')
	def ethdev_token_txsend_noamt(self,name):
		self.ethdev_token_txsend(name,ext='1.23456,51000].sigtx',token='mm1')

	def ethdev_token_bal3(self,name):
		self.ethdev_token_bal(name,expect_str=r'98831F3A:E:13\s+1.23456\s')

	def ethdev_stop(self,name):
		MMGenExpect(name,'',msg_only=True)
		pid = read_from_tmpfile(cfg,cfg['parity_pidfile'])
		assert pid,'No parity pid file!'
		subprocess.check_call(['kill',pid])
		ok()

	# undocumented admin commands
	def ref_tx_addrgen(self,name,atype='L'):
		if atype not in g.proto.mmtypes: return
		t = MMGenExpect(name,'mmgen-addrgen',['--outdir='+cfg['tmpdir'],'--type='+atype,dfl_words,'1-2'])
		t.read()

	def ref_tx_addrgen1(self,name): self.ref_tx_addrgen(name,atype='L')
	def ref_tx_addrgen2(self,name): self.ref_tx_addrgen(name,atype='C')
	def ref_tx_addrgen3(self,name): self.ref_tx_addrgen(name,atype='S')
	def ref_tx_addrgen4(self,name): self.ref_tx_addrgen(name,atype='B')

	def ref_tx_txcreate(self,name,f1,f2,f3,f4):
		sources = ['31','32']
		if 'S' in g.proto.mmtypes: sources += ['33']
		if 'B' in g.proto.mmtypes: sources += ['34']
		self.txcreate_common(name,  sources=sources,
									addrs_per_wallet=2,
									add_args=['--locktime=1320969600'],
									do_label=True)

	# END methods
	for k in (
			'ref_wallet_conv',
			'ref_mn_conv',
			'ref_seed_conv',
			'ref_hex_conv',
			'ref_brain_conv',
			'ref_incog_conv',
			'ref_incox_conv',
			'ref_hincog_conv',
			'ref_hincog_conv_old',
			'ref_wallet_conv_out',
			'ref_mn_conv_out',
			'ref_seed_conv_out',
			'ref_hex_conv_out',
			'ref_incog_conv_out',
			'ref_incox_conv_out',
			'ref_hincog_conv_out',
			'ref_wallet_chk',
			'refwalletgen',
			'ref_seed_chk',
			'ref_hex_chk',
			'ref_mn_chk',
			'ref_brain_chk',
			'ref_hincog_chk',
			'refaddrgen',
			'refkeyaddrgen',
			'refaddrgen_compressed',
			'refkeyaddrgen_compressed',
			'refpasswdgen',
			'ref_b32passwdgen',
			'ref_hexpasswdgen'
		):
		for i in ('1','2','3'):
			locals()[k+i] = locals()[k]

	for k in ('walletgen','addrgen','keyaddrgen'): locals()[k+'14'] = locals()[k]

# create temporary dirs
if not opt.resume and not opt.skip_deps:
	if g.platform == 'win':
		for cfg in sorted(cfgs):
			mk_tmpdir(cfgs[cfg]['tmpdir'])
	else:
		for cfg in sorted(cfgs):
			src = os.path.join(shm_dir,cfgs[cfg]['tmpdir'].split('/')[-1])
			mk_tmpdir(src)
			try:
				os.unlink(cfgs[cfg]['tmpdir'])
			except OSError as e:
				if e.errno != 2: raise
			finally:
				os.symlink(src,cfgs[cfg]['tmpdir'])

have_dfl_wallet = False

# main()
if opt.pause:
	import termios,atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	def at_exit():
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
	atexit.register(at_exit)

start_time = int(time.time())

def end_msg():
	t = int(time.time()) - start_time
	m = '{} test{} performed.  Elapsed time: {:02d}:{:02d}\n'
	sys.stderr.write(green(m.format(cmd_total,suf(cmd_total),t/60,t%60)))

ts = MMGenTestSuite()

if cmd_args and cmd_args[0] == 'admin':
	cmd_args.pop(0)
	cmd_data = cmd_data_admin
	cmd_list = cmd_list_admin

try:
	if cmd_args:
		for arg in cmd_args:
			if arg in utils:
				globals()[arg](cmd_args[cmd_args.index(arg)+1:])
				sys.exit(0)
			elif 'info_'+arg in cmd_data:
				dirs = cmd_data['info_'+arg][1]
				if dirs: clean(dirs)
				for cmd in cmd_list[arg]:
					check_needs_rerun(ts,cmd,build=True)
			elif arg in meta_cmds:
				for cmd in meta_cmds[arg]:
					check_needs_rerun(ts,cmd,build=True)
			elif arg in cmd_data:
				check_needs_rerun(ts,arg,build=True)
			else:
				die(1,'{}: unrecognized command'.format(arg))
	else:
		clean()
		for cmd in cmd_data:
			if cmd == 'info_regtest': break # don't run everything after this by default
			if cmd[:5] == 'info_':
				gmsg('{}Testing {}'.format(('\n','')[bool(opt.resume)],cmd_data[cmd][0]))
				continue
			ts.do_cmd(cmd)
			if cmd is not cmd_data.keys()[-1]: do_between()
except KeyboardInterrupt:
	die(1,'\nExiting at user request')
except opt.traceback and Exception:
	try:
		os.stat('my.err')
		with open('my.err') as f:
			t = f.readlines()
			if t: msg_r('\n'+yellow(''.join(t[:-1]))+red(t[-1]))
	except: pass
	die(1,blue('Test script exited with error'))
except:
	sys.stderr = stderr_save
	raise

end_msg()
