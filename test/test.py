#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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


import sys,os

def run_in_tb():
	fn = sys.argv[0]
	source = open(fn)
	try:
		exec source in {'inside_tb':1}
	except SystemExit:
		pass
	except:
		def color(s): return '\033[36;1m' + s + '\033[0m'
		e = sys.exc_info()
		sys.stdout.write(color('\nTest script returned: %s\n' % (e[0].__name__)))

if not 'inside_tb' in globals() and 'MMGEN_TEST_TRACEBACK' in os.environ:
	run_in_tb()
	sys.exit()

pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.test import *

g.quiet = False # if 'quiet' was set in config file, disable here
os.environ['MMGEN_QUIET'] = '0' # and for the spawned scripts

tb_cmd = 'scripts/traceback.py'
log_file = 'test.py_log'

scripts = (
	'addrgen', 'addrimport', 'keygen',
	'passchg', 'tool',
	'txcreate', 'txsend', 'txsign',
	'walletchk', 'walletconv', 'walletgen'
)

hincog_fn      = 'rand_data'
hincog_bytes   = 1024*1024
hincog_offset  = 98765
hincog_seedlen = 256

incog_id_fn  = 'incog_id'
non_mmgen_fn = 'btckey'
pwfile = 'passwd_file'

ref_dir = os.path.join('test','ref')

ref_wallet_brainpass = 'abc'
ref_wallet_hash_preset = '1'
ref_wallet_incog_offset = 123

from mmgen.obj import MMGenTXLabel
ref_tx_label = ''.join([unichr(i) for i in  range(65,91) +
											range(1040,1072) + # cyrillic
											range(913,939) +   # greek
											range(97,123)])[:MMGenTXLabel.max_len]

ref_bw_hash_preset = '1'
ref_bw_file        = 'wallet.mmbrain'
ref_bw_file_spc    = 'wallet-spaced.mmbrain'

ref_kafile_pass        = 'kafile password'
ref_kafile_hash_preset = '1'

ref_enc_fn = 'sample-text.mmenc'
tool_enc_passwd = "Scrypt it, don't hash it!"
sample_text = \
	'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks\n'

# Laggy flash media cause pexpect to crash, so create a temporary directory
# under '/dev/shm' and put datadir and temp files here.
shortopts = ''.join([e[1:] for e in sys.argv if len(e) > 1 and e[0] == '-' and e[1] != '-'])
shortopts = ['-'+e for e in list(shortopts)]
data_dir = os.path.join('test','data_dir')
if not any(e in ('--skip-deps','--resume','-S','-r') for e in sys.argv+shortopts):
	if g.platform == 'win':
		try: os.listdir(data_dir)
		except: pass
		else:
			import shutil
			shutil.rmtree(data_dir)
		os.mkdir(data_dir,0755)
	else:
		d,pfx = '/dev/shm','mmgen-test-'
		try:
			import subprocess
			subprocess.call('rm -rf %s/%s*'%(d,pfx),shell=True)
		except Exception as e:
			die(2,'Unable to delete directory tree %s/%s* (%s)'%(d,pfx,e))
		try:
			import tempfile
			shm_dir = tempfile.mkdtemp('',pfx,d)
		except Exception as e:
			die(2,'Unable to create temporary directory in %s (%s)'%(d,e))
		dd = os.path.join(shm_dir,'data_dir')
		os.mkdir(dd,0755)
		try: os.unlink(data_dir)
		except: pass
		os.symlink(dd,data_dir)

opts_data = {
#	'sets': [('interactive',bool,'verbose',None)],
	'desc': 'Test suite for the MMGen suite',
	'usage':'[options] [command(s) or metacommand(s)]',
	'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-b, --buf-keypress  Use buffered keypresses as with real human input
-c, --print-cmdline Print the command line of each spawned command
-d, --debug-scripts Turn on debugging output in executed scripts
-x, --debug-pexpect Produce debugging output for pexpect calls
-D, --direct-exec   Bypass pexpect and execute a command directly (for
                    debugging only)
-e, --exact-output  Show the exact output of the MMGen script(s) being run
-l, --list-cmds     List and describe the commands in the test suite
-L, --log           Log commands to file {lf}
-n, --names         Display command names instead of descriptions
-I, --interactive   Interactive mode (without pexpect)
-O, --popen-spawn   Use pexpect's popen_spawn instead of popen
-p, --pause         Pause between tests, resuming on keypress
-P, --profile       Record the execution time of each script
-q, --quiet         Produce minimal output.  Suppress dependency info
-r, --resume=c      Resume at command 'c' after interrupted run
-s, --system        Test scripts and modules installed on system rather
                    than those in the repo root
-S, --skip-deps     Skip dependency checking for command
-u, --usr-random    Get random data interactively from user
-t, --traceback     Run the command inside the '{tb_cmd}' script
-v, --verbose       Produce more verbose output
-W, --no-dw-delete  Don't remove default wallet from data dir after dw tests are done
""".format(tb_cmd=tb_cmd,lf=log_file),
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

sys.argv = [sys.argv[0]] + ['--data-dir',data_dir] + sys.argv[1:]

cmd_args = opts.init(opts_data)

tn_desc = ('','.testnet')[g.testnet]

cfgs = {
	'15': {
		'tmpdir':        os.path.join('test','tmp15'),
		'wpasswd':       'Dorian',
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
	},
	'16': {
		'tmpdir':        os.path.join('test','tmp16'),
		'wpasswd':       'My changed password',
		'hash_preset':   '2',
		'dep_generators': {
			pwfile:        'passchg_dfl_wallet',
		},
	},
	'1': {
		'tmpdir':        os.path.join('test','tmp1'),
		'wpasswd':       'Dorian',
		'kapasswd':      'Grok the blockchain',
		'addr_idx_list': '12,99,5-10,5,12', # 8 addresses
		'dep_generators':  {
			pwfile:        'walletgen',
			'mmdat':       'walletgen',
			'addrs':       'addrgen',
			'rawtx':         'txcreate',
			'sigtx':         'txsign',
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
	'2': {
		'tmpdir':        os.path.join('test','tmp2'),
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
	},
	'3': {
		'tmpdir':        os.path.join('test','tmp3'),
		'wpasswd':       'Major miner',
		'addr_idx_list': '73,54,1022-1023,2-5', # 8 addresses
		'dep_generators': {
			'mmdat':       'walletgen3',
			'addrs':       'addrgen3',
			'rawtx':         'txcreate3',
			'sigtx':         'txsign3'
		},
	},
	'4': {
		'tmpdir':        os.path.join('test','tmp4'),
		'wpasswd':       'Hashrate good',
		'addr_idx_list': '63,1004,542-544,7-9', # 8 addresses
		'seed_len':      192,
		'dep_generators': {
			'mmdat':       'walletgen4',
			'mmbrain':     'walletgen4',
			'addrs':       'addrgen4',
			'rawtx':       'txcreate4',
			'sigtx':       'txsign4',
		},
		'bw_filename': 'brainwallet.mmbrain',
		'bw_params':   '192,1',
	},
	'14': {
		'kapasswd':      'Maxwell',
		'tmpdir':        os.path.join('test','tmp14'),
		'wpasswd':       'The Halving',
		'addr_idx_list': '61,998,502-504,7-9', # 8 addresses
		'seed_len':      256,
		'dep_generators': {
			'mmdat':       'walletgen14',
			'addrs':       'addrgen14',
			'akeys.mmenc': 'keyaddrgen14',
		},
	},
	'5': {
		'tmpdir':        os.path.join('test','tmp5'),
		'wpasswd':       'My changed password',
		'hash_preset':   '2',
		'dep_generators': {
			'mmdat':       'passchg',
			pwfile:        'passchg',
		},
	},
	'6': {
		'name':            'reference wallet check (128-bit)',
		'seed_len':        128,
		'seed_id':         'FE3C6545',
		'ref_bw_seed_id':  '33F10310',
		'addrfile_chk':    ('B230 7526 638F 38CB','B64D 7327 EF2A 60FE')[g.testnet],
		'keyaddrfile_chk': ('CF83 32FB 8A8B 08E2','FEBF 7878 97BB CC35')[g.testnet],
		'wpasswd':         'reference password',
		'ref_wallet':      'FE3C6545-D782B529[128,1].mmdat',
		'ic_wallet':       'FE3C6545-E29303EA-5E229E30[128,1].mmincog',
		'ic_wallet_hex':   'FE3C6545-BC4BE3F2-32586837[128,1].mmincox',

		'hic_wallet':       'FE3C6545-161E495F-BEB7548E[128,1].incog-offset123',
		'hic_wallet_old':   'FE3C6545-161E495F-9860A85B[128,1].incog-old.offset123',

		'tmpdir':        os.path.join('test','tmp6'),
		'kapasswd':      '',
		'addr_idx_list': '1010,500-501,31-33,1,33,500,1011', # 8 addresses
		'dep_generators':  {
			'mmdat':       'refwalletgen1',
			pwfile:       'refwalletgen1',
			'addrs':       'refaddrgen1',
			'akeys.mmenc': 'refkeyaddrgen1'
		},

	},
	'7': {
		'name':            'reference wallet check (192-bit)',
		'seed_len':        192,
		'seed_id':         '1378FC64',
		'ref_bw_seed_id':  'CE918388',
		'addrfile_chk':    ('8C17 A5FA 0470 6E89','0A59 C8CD 9439 8B81')[g.testnet],
		'keyaddrfile_chk': ('9648 5132 B98E 3AD9','2F72 C83F 44C5 0FAC')[g.testnet],
		'wpasswd':         'reference password',
		'ref_wallet':      '1378FC64-6F0F9BB4[192,1].mmdat',
		'ic_wallet':       '1378FC64-2907DE97-F980D21F[192,1].mmincog',
		'ic_wallet_hex':   '1378FC64-4DCB5174-872806A7[192,1].mmincox',

		'hic_wallet':       '1378FC64-B55E9958-77256FC1[192,1].incog.offset123',
		'hic_wallet_old':   '1378FC64-B55E9958-D85FF20C[192,1].incog-old.offset123',

		'tmpdir':        os.path.join('test','tmp7'),
		'kapasswd':      '',
		'addr_idx_list': '1010,500-501,31-33,1,33,500,1011', # 8 addresses
		'dep_generators':  {
			'mmdat':       'refwalletgen2',
			pwfile:       'refwalletgen2',
			'addrs':       'refaddrgen2',
			'akeys.mmenc': 'refkeyaddrgen2'
		},

	},
	'8': {
		'name':            'reference wallet check (256-bit)',
		'seed_len':        256,
		'seed_id':         '98831F3A',
		'ref_bw_seed_id':  'B48CD7FC',
		'addrfile_chk':    ('6FEF 6FB9 7B13 5D91','3C2C 8558 BB54 079E')[g.testnet],
		'keyaddrfile_chk': ('9F2D D781 1812 8BAD','7410 8F95 4B33 B4B2')[g.testnet],
		'wpasswd':         'reference password',
		'ref_wallet':      '98831F3A-{}[256,1].mmdat'.format(('27F2BF93','E2687906')[g.testnet]),
		'ref_addrfile':    '98831F3A[1,31-33,500-501,1010-1011]{}.addrs'.format(tn_desc),
		'ref_keyaddrfile': '98831F3A[1,31-33,500-501,1010-1011]{}.akeys.mmenc'.format(tn_desc),
		'ref_addrfile_chksum':    ('6FEF 6FB9 7B13 5D91','3C2C 8558 BB54 079E')[g.testnet],
		'ref_keyaddrfile_chksum': ('9F2D D781 1812 8BAD','7410 8F95 4B33 B4B2')[g.testnet],

#		'ref_fake_unspent_data':'98831F3A_unspent.json',
		'ref_tx_file':     'FFB367[1.234]{}.rawtx'.format(tn_desc),
		'ic_wallet':       '98831F3A-5482381C-18460FB1[256,1].mmincog',
		'ic_wallet_hex':   '98831F3A-1630A9F2-870376A9[256,1].mmincox',

		'hic_wallet':       '98831F3A-F59B07A0-559CEF19[256,1].incog.offset123',
		'hic_wallet_old':   '98831F3A-F59B07A0-848535F3[256,1].incog-old.offset123',

		'tmpdir':        os.path.join('test','tmp8'),
		'kapasswd':      '',
		'addr_idx_list': '1010,500-501,31-33,1,33,500,1011', # 8 addresses
		'dep_generators':  {
			'mmdat':       'refwalletgen3',
			pwfile:       'refwalletgen3',
			'addrs':       'refaddrgen3',
			'akeys.mmenc': 'refkeyaddrgen3'
		},
	},
	'9': {
		'tmpdir':        os.path.join('test','tmp9'),
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

from copy import deepcopy
for a,b in ('6','11'),('7','12'),('8','13'):
	cfgs[b] = deepcopy(cfgs[a])
	cfgs[b]['tmpdir'] = os.path.join('test','tmp'+b)

from collections import OrderedDict

cmd_group = OrderedDict()

cmd_group['help'] = OrderedDict([
#     test               description                  depends
	['helpscreens',     (1,'help screens',             [],1)],
	['longhelpscreens', (1,'help screens (--longhelp)',[],1)],
])

cmd_group['dfl_wallet'] = OrderedDict([
	['walletgen_dfl_wallet', (15,'wallet generation (default wallet)',[[[],15]],1)],
	['export_seed_dfl_wallet',(15,'seed export to mmseed format (default wallet)',[[[pwfile],15]],1)],
	['addrgen_dfl_wallet',(15,'address generation (default wallet)',[[[pwfile],15]],1)],
	['txcreate_dfl_wallet',(15,'transaction creation (default wallet)',[[['addrs'],15]],1)],
	['txsign_dfl_wallet',(15,'transaction signing (default wallet)',[[['rawtx',pwfile],15]],1)],
	['passchg_dfl_wallet',(16,'password, label and hash preset change (default wallet)',[[[pwfile],15]],1)],
	['walletchk_newpass_dfl_wallet',(16,'wallet check with new pw, label and hash preset',[[[pwfile],16]],1)],
	['delete_dfl_wallet',(15,'delete default wallet',[[[pwfile],15]],1)],
])

cmd_group['main'] = OrderedDict([
	['walletgen',       (1,'wallet generation',        [[['del_dw_run'],15]],1)],
#	['walletchk',       (1,'wallet check',             [[['mmdat'],1]])],
	['passchg',         (5,'password, label and hash preset change',[[['mmdat',pwfile],1]],1)],
	['walletchk_newpass',(5,'wallet check with new pw, label and hash preset',[[['mmdat',pwfile],5]],1)],
	['addrgen',         (1,'address generation',       [[['mmdat',pwfile],1]],1)],
	['addrimport',      (1,'address import',           [[['addrs'],1]],1)],
	['txcreate',        (1,'transaction creation',     [[['addrs'],1]],1)],
	['txsign',          (1,'transaction signing',      [[['mmdat','rawtx',pwfile],1]],1)],
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
])

cmd_group['tool'] = OrderedDict([
	['tool_encrypt',     (9,"'mmgen-tool encrypt' (random data)",     [],1)],
	['tool_decrypt',     (9,"'mmgen-tool decrypt' (random data)", [[[cfgs['9']['tool_enc_infn'],cfgs['9']['tool_enc_infn']+'.mmenc'],9]],1)],
#	['tool_encrypt_ref', (9,"'mmgen-tool encrypt' (reference text)",  [])],
	['tool_find_incog_data', (9,"'mmgen-tool find_incog_data'", [[[hincog_fn],1],[[incog_id_fn],1]])],
#	['pywallet', (9,"'mmgen-pywallet'", [],1)],
])

# saved reference data
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
	('refkeyaddrgen',  (['mmdat',pwfile],'new refwallet key-addr chksum'))
)

# misc. saved reference data
cmd_group['ref_other'] = (
	('ref_addrfile_chk',   'saved reference address file'),
	('ref_keyaddrfile_chk','saved reference key-address file'),
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

cmd_list = OrderedDict()
for k in cmd_group: cmd_list[k] = []

cmd_data = OrderedDict()
for k,v in (
		('help', ('help screens',[])),
		('dfl_wallet', ('basic operations with default wallet',[15,16])),
		('main', ('basic operations',[1,2,3,4,5,15,16])),
		('tool', ('tools',[9]))
	):
	cmd_data['info_'+k] = v
	for i in cmd_group[k]:
		cmd_list[k].append(i)
		cmd_data[i] = cmd_group[k][i]

cmd_data['info_ref'] = 'reference data',[6,7,8]
for a,b in cmd_group['ref']:
	for i,j in (1,128),(2,192),(3,256):
		k = a+str(i)
		cmd_list['ref'].append(k)
		cmd_data[k] = (5+i,'%s (%s-bit)' % (b[1],j),[[b[0],5+i]],1)

cmd_data['info_ref_other'] = 'other reference data',[8]
for a,b in cmd_group['ref_other']:
	cmd_list['ref_other'].append(a)
	cmd_data[a] = (8,b,[[[],8]],1)

cmd_data['info_conv_in'] = 'wallet conversion from reference data',[11,12,13]
for a,b in cmd_group['conv_in']:
	for i,j in (1,128),(2,192),(3,256):
		k = a+str(i)
		cmd_list['conv_in'].append(k)
		cmd_data[k] = (10+i,'%s (%s-bit)' % (b,j),[[[],10+i]],1)

cmd_data['info_conv_out'] = 'wallet conversion to reference data',[11,12,13]
for a,b in cmd_group['conv_out']:
	for i,j in (1,128),(2,192),(3,256):
		k = a+str(i)
		cmd_list['conv_out'].append(k)
		cmd_data[k] = (10+i,'%s (%s-bit)' % (b,j),[[[],10+i]],1)

utils = {
	'check_deps': 'check dependencies for specified command',
	'clean':      'clean specified tmp dir(s) 1,2,3,4,5 or 6 (no arg = all dirs)',
}

addrs_per_wallet = 8

# total of two outputs must be < 10 BTC
for k in cfgs:
	cfgs[k]['amts'] = [0,0]
	for idx,mod in (0,6),(1,4):
		cfgs[k]['amts'][idx] = '%s.%s' % ((getrandnum(2) % mod), str(getrandnum(4))[:5])

meta_cmds = OrderedDict([
	['ref1', ('refwalletgen1','refaddrgen1','refkeyaddrgen1')],
	['ref2', ('refwalletgen2','refaddrgen2','refkeyaddrgen2')],
	['ref3', ('refwalletgen3','refaddrgen3','refkeyaddrgen3')],
	['gen',  ('walletgen','addrgen')],
	['pass', ('passchg','walletchk_newpass')],
	['tx',   ('addrimport','txcreate','txsign','txsend')],
	['export', [k for k in cmd_data if k[:7] == 'export_' and cmd_data[k][0] == 1]],
	['gen_sp', [k for k in cmd_data if k[:8] == 'addrgen_' and cmd_data[k][0] == 1]],
	['online', ('keyaddrgen','txsign_keyaddr')],
	['2', [k for k in cmd_data if cmd_data[k][0] == 2]],
	['3', [k for k in cmd_data if cmd_data[k][0] == 3]],
	['4', [k for k in cmd_data if cmd_data[k][0] == 4]],

	['saved_ref1', [c[0]+'1' for c in cmd_group['ref']]],
	['saved_ref2', [c[0]+'2' for c in cmd_group['ref']]],
	['saved_ref3', [c[0]+'3' for c in cmd_group['ref']]],

	['saved_ref_other', [c[0] for c in cmd_group['ref_other']]],

	['saved_ref_conv_in1', [c[0]+'1' for c in cmd_group['conv_in']]],
	['saved_ref_conv_in2', [c[0]+'2' for c in cmd_group['conv_in']]],
	['saved_ref_conv_in3', [c[0]+'3' for c in cmd_group['conv_in']]],

	['saved_ref_conv_out1', [c[0]+'1' for c in cmd_group['conv_out']]],
	['saved_ref_conv_out2', [c[0]+'2' for c in cmd_group['conv_out']]],
	['saved_ref_conv_out3', [c[0]+'3' for c in cmd_group['conv_out']]],
])

del cmd_group

add_spawn_args = ' '.join(['{} {}'.format(
	'--'+k.replace('_','-'),
	getattr(opt,k) if getattr(opt,k) != True else ''
	) for k in 'testnet','rpc_host' if getattr(opt,k)]).split()
add_spawn_args += ['--data-dir',data_dir]

if opt.profile: opt.names = True
if opt.resume: opt.skip_deps = True
if opt.log:
	log_fd = open(log_file,'a')
	log_fd.write('\nLog started: %s\n' % make_timestr())

usr_rand_chars = (5,30)[bool(opt.usr_random)]
usr_rand_arg = '-r%s' % usr_rand_chars

if opt.system: sys.path.pop(0)
ia = bool(opt.interactive)

# Disable color in spawned scripts so we can parse their output
os.environ['MMGEN_DISABLE_COLOR'] = '1'
os.environ['MMGEN_NO_LICENSE'] = '1'
os.environ['MMGEN_MIN_URANDCHARS'] = '3'
os.environ['MMGEN_BOGUS_SEND'] = '1'

if opt.debug_scripts: os.environ['MMGEN_DEBUG'] = '1'

if opt.buf_keypress:
	send_delay = 0.3
else:
	send_delay = 0
	os.environ['MMGEN_DISABLE_HOLD_PROTECT'] = '1'

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
	fs = '  {:<{w}} - {}'
	Msg(green('AVAILABLE COMMANDS:'))
	w = max([len(i) for i in cmd_data])
	for cmd in cmd_data:
		if cmd[:5] == 'info_':
			m = capfirst(cmd_data[cmd][0])
			Msg(green('  %s:' % m))
			continue
		Msg('  '+fs.format(cmd,cmd_data[cmd][1],w=w))

	w = max([len(i) for i in meta_cmds])
	Msg(green('\nAVAILABLE METACOMMANDS:'))
	for cmd in meta_cmds:
		Msg(fs.format(cmd,' '.join(meta_cmds[cmd]),w=w))

	w = max([len(i) for i in cmd_list])
	Msg(green('\nAVAILABLE COMMAND GROUPS:'))
	for g in cmd_list:
		Msg(fs.format(g,' '.join(cmd_list[g]),w=w))

	Msg(green('\nAVAILABLE UTILITIES:'))
	w = max([len(i) for i in utils])
	for cmd in sorted(utils):
		Msg(fs.format(cmd,utils[cmd],w=w))
	sys.exit()

import time,re
if g.platform == 'linux':
	import pexpect
	if opt.popen_spawn:
		import termios,atexit
		def at_exit(): os.system('stty sane')
		atexit.register(at_exit)
		from pexpect.popen_spawn import PopenSpawn
		use_popen_spawn,NL = True,'\n'
	else:
		use_popen_spawn,NL = False,'\r\n'
else: # Windows
	use_popen_spawn,NL = True,'\r\n'
	try:
		import pexpect
		from pexpect.popen_spawn import PopenSpawn
	except:
		ia = True
		m1 = ('Missing pexpect module detected.  Skipping some tests and running in'
			'\ninteractive mode.  User prompts and control value checks will be ')
		m2 = 'HIGHLIGHTED IN GREEN'
		m3 = '.\nControl values should be checked against the program output.\nContinue?'
		if not keypress_confirm(green(m1)+grnbg(m2)+green(m3),default_yes=True):
			errmsg('Exiting at user request')
			sys.exit()

def my_send(p,t,delay=send_delay,s=False):
	if delay: time.sleep(delay)
	ret = p.send(t) # returns num bytes written
	if delay: time.sleep(delay)
	if opt.verbose:
		ls = (' ','')[bool(opt.debug or not s)]
		es = ('  ','')[bool(s)]
		msg('%sSEND %s%s' % (ls,es,yellow("'%s'"%t.replace('\n',r'\n'))))
	return ret

def my_expect(p,s,t='',delay=send_delay,regex=False,nonl=False):
	quo = ('',"'")[type(s) == str]

	if opt.verbose: msg_r('EXPECT %s' % yellow(quo+str(s)+quo))
	else:       msg_r('+')

	try:
		if s == '': ret = 0
		else:
			f = (p.expect_exact,p.expect)[bool(regex)]
			ret = f(s,timeout=(60,5)[bool(opt.debug_pexpect)])
	except pexpect.TIMEOUT:
		if opt.debug_pexpect: raise
		errmsg(red('\nERROR.  Expect %s%s%s timed out.  Exiting' % (quo,s,quo)))
		sys.exit(1)
	debug_pexpect_msg(p)

	if opt.debug or (opt.verbose and type(s) != str): msg_r(' ==> %s ' % ret)

	if ret == -1:
		errmsg('Error.  Expect returned %s' % ret)
		sys.exit(1)
	else:
		if t == '':
			if not nonl: vmsg('')
		else:
			my_send(p,t,delay,s)
		return ret

def get_file_with_ext(ext,mydir,delete=True,no_dot=False):

	dot = ('.','')[bool(no_dot)]
	flist = [os.path.join(mydir,f) for f in os.listdir(mydir)
				if f == ext or f[-len(dot+ext):] == dot+ext]

	if not flist: return False

	if len(flist) > 1:
		if delete:
			if not opt.quiet:
				msg("Multiple *.%s files in '%s' - deleting" % (ext,mydir))
			for f in flist: os.unlink(f)
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
	from mmgen.addr import AddrList
	chk = AddrList(addrfile).chksum
	if opt.verbose and display: msg('Checksum: %s' % cyan(chk))
	end_silence()
	return chk

def verify_checksum_or_exit(checksum,chk):
	if checksum != chk:
		errmsg(red('Checksum error: %s' % chk))
		sys.exit(1)
	vmsg(green('Checksums match: %s') % (cyan(chk)))

def debug_pexpect_msg(p):
	if opt.debug_pexpect:
		errmsg('\n{}{}{}'.format(red('BEFORE ['),p.before,red(']')))
		errmsg('{}{}{}'.format(red('MATCH ['),p.after,red(']')))

class MMGenExpect(object):

	def __init__(self,name,mmgen_cmd,cmd_args=[],extra_desc='',no_output=False):
		cmd = (('./','')[bool(opt.system)]+mmgen_cmd,'python')[g.platform=='win']
		cmd_args = add_spawn_args + cmd_args
		args = (cmd_args,[mmgen_cmd]+cmd_args)[g.platform=='win']
		desc = (cmd_data[name][1],name)[bool(opt.names)] + (' ' + extra_desc).strip()
		for i in args:
			if type(i) not in (str,unicode):
				m1 = 'Error: missing input files in cmd line?:'
				m2 = '\nName: {}\nCmd: {}\nCmd args: {}'
				die(2,(m1+m2).format(name,cmd,args))
		if use_popen_spawn:
			args = [("'"+a+"'" if ' ' in a else a) for a in args]
		cmd_str = '{} {}'.format(cmd,' '.join(args))
		if use_popen_spawn:
			cmd_str = cmd_str.replace('\\','/')

		if opt.log:
			log_fd.write(cmd_str+'\n')
		if opt.verbose or opt.print_cmdline or opt.exact_output:
			clr1,clr2,eol = ((green,cyan,'\n'),(nocolor,nocolor,' '))[bool(opt.print_cmdline)]
			sys.stderr.write(green('Testing: {}\n'.format(desc)))
			sys.stderr.write(clr1('Executing {}{}'.format(clr2(cmd_str),eol)))
		else:
			m = 'Testing %s: ' % desc
			msg_r((m,yellow(m))[ia])

		if mmgen_cmd == '': return

		if opt.direct_exec or ia:
			msg('')
			from subprocess import call,check_output
			f = (call,check_output)[bool(no_output)]
			ret = f([cmd] + args)
			if f == call and ret != 0:
				m = 'ERROR: process returned a non-zero exit status (%s)'
				die(1,red(m % ret))
		else:
			if opt.traceback:
				cmd,args = tb_cmd,[cmd]+args
			if use_popen_spawn:
				self.p = PopenSpawn(cmd_str)
			else:
				self.p = pexpect.spawn(cmd,args)
			if opt.exact_output: self.p.logfile = sys.stdout

	def license(self):
		if 'MMGEN_NO_LICENSE' in os.environ: return
		p = "'w' for conditions and warranty info, or 'c' to continue: "
		my_expect(self.p,p,'c')

	def label(self,label='Test Label'):
		p = 'Enter a wallet label, or hit ENTER for no label: '
		my_expect(self.p,p,label+'\n')

	def usr_rand_out(self,saved=False):
		m = '%suser-supplied entropy' % (('','saved ')[saved])
		my_expect(self.p,'Generating encryption key from OS random data plus ' + m)

	def usr_rand(self,num_chars):
		if opt.usr_random:
			self.interactive()
			my_send(self.p,'\n')
		else:
			rand_chars = list(getrandstr(num_chars,no_space=True))
			my_expect(self.p,'symbols left: ','x')
			try:
				vmsg_r('SEND ')
				while self.p.expect('left: ',0.1) == 0:
					ch = rand_chars.pop(0)
					msg_r(yellow(ch)+' ' if opt.verbose else '+')
					self.p.send(ch)
			except:
				vmsg('EOT')
			my_expect(self.p,'ENTER to continue: ','\n')

	def passphrase_new(self,desc,passphrase):
		my_expect(self.p,('Enter passphrase for %s: ' % desc), passphrase+'\n')
		my_expect(self.p,'Repeat passphrase: ', passphrase+'\n')

	def passphrase(self,desc,passphrase,pwtype=''):
		if pwtype: pwtype += ' '
		my_expect(self.p,('Enter %spassphrase for %s.*?: ' % (pwtype,desc)),
				passphrase+'\n',regex=True)

	def hash_preset(self,desc,preset=''):
		my_expect(self.p,('Enter hash preset for %s' % desc))
		my_expect(self.p,('or hit ENTER .*?:'), str(preset)+'\n',regex=True)

	def written_to_file(self,desc,overwrite_unlikely=False,query='Overwrite?  ',oo=False):
		s1 = '%s written to file ' % desc
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = my_expect(self.p,([s1,s2],s1)[overwrite_unlikely])
		if ret == 1:
			my_send(self.p,'YES\n')
#			if oo:
			outfile = self.expect_getend("Overwriting file '").rstrip("'")
			return outfile
# 			else:
# 				ret = my_expect(self.p,s1)
		self.expect(NL,nonl=True)
		outfile = self.p.before.strip().strip("'")
		if opt.debug_pexpect: msgred('Outfile [%s]' % outfile)
		vmsg('%s file: %s' % (desc,cyan(outfile.replace("'",''))))
		return outfile

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ",'\n')
		self.expect('Exiting at user request')

	def tx_view(self):
		my_expect(self.p,r'View .*?transaction.*? \(y\)es, \(N\)o, pager \(v\)iew.*?: ','\n',regex=True)

	def expect_getend(self,s,regex=False):
		ret = self.expect(s,regex=regex,nonl=True)
		debug_pexpect_msg(self.p)
#		end = self.readline().strip()
		# readline() of partial lines doesn't work with PopenSpawn, so do this instead:
		self.expect(NL,nonl=True)
		debug_pexpect_msg(self.p)
		end = self.p.before
		vmsg(' ==> %s' % cyan(end))
		return end

	def interactive(self):
		return self.p.interact()

	def logfile(self,arg):
		self.p.logfile = arg

	def expect(self,*args,**kwargs):
		return my_expect(self.p,*args,**kwargs)

	def send(self,*args,**kwargs):
		return my_send(self.p,*args,**kwargs)

# 	def readline(self):
# 		return self.p.readline()
# 	def readlines(self):
# 		return [l.rstrip()+'\n' for l in self.p.readlines()]

	def read(self,n=None):
		return self.p.read(n)

	def close(self):
		if not use_popen_spawn:
			self.p.close()

from mmgen.obj import BTCAmt
from mmgen.bitcoin import verify_addr

def create_fake_unspent_entry(address,sid=None,idx=None,lbl=None,non_mmgen=None):
	if lbl: lbl = ' ' + lbl
	return {
		'account': (non_mmgen or ('%s:%s%s' % (sid,idx,lbl))).decode('utf8'),
		'vout': int(getrandnum(4) % 8),
		'txid': hexlify(os.urandom(32)).decode('utf8'),
		'amount': BTCAmt('%s.%s' % (10+(getrandnum(4) % 40), getrandnum(4) % 100000000)),
		'address': address,
		'spendable': False,
		'scriptPubKey': ('76a914'+verify_addr(address,return_hex=True)+'88ac'),
		'confirmations': getrandnum(4) % 50000
	}

labels = [
	"Automotive",
	"Travel expenses",
	"Healthcare",
	"Freelancing 1",
	"Freelancing 2",
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
label_iter = None
def create_fake_unspent_data(adata,unspent_data_file,tx_data,non_mmgen_input=''):

	out = []
	for s in tx_data:
		sid = tx_data[s]['sid']
		a = adata.addrlist(sid)
		for n,(idx,btcaddr) in enumerate(a.addrpairs(),1):
			while True:
				try: lbl = next(label_iter)
				except: label_iter = iter(labels)
				else: break
			out.append(create_fake_unspent_entry(btcaddr,sid,idx,lbl))
			if n == 1:  # create a duplicate address. This means addrs_per_wallet += 1
				out.append(create_fake_unspent_entry(btcaddr,sid,idx,lbl))

	if non_mmgen_input:
		from mmgen.bitcoin import privnum2addr,hex2wif
		privnum = getrandnum(32)
		btcaddr = privnum2addr(privnum,compressed=True)
		of = os.path.join(cfgs[non_mmgen_input]['tmpdir'],non_mmgen_fn)
		write_data_to_file(of, hex2wif('{:064x}'.format(privnum),
					compressed=True)+'\n','compressed bitcoin key',silent=True)

		out.append(create_fake_unspent_entry(btcaddr,non_mmgen='Non-MMGen address'))

#	msg('\n'.join([repr(o) for o in out])); sys.exit()
	write_data_to_file(unspent_data_file,repr(out),'Unspent outputs',silent=True)


def add_comments_to_addr_file(addrfile,outfile):
	silence()
	msg(green("Adding comments to address file '%s'" % addrfile))
	from mmgen.addr import AddrList
	a = AddrList(addrfile)
	for n,idx in enumerate(a.idxs(),1):
		if n % 2: a.set_comment(idx,'Test address %s' % n)
	a.format(enable_comments=True)
	write_data_to_file(outfile,a.fmt_data,silent=True)
	end_silence()

def make_brainwallet_file(fn):
	# Print random words with random whitespace in between
	from mmgen.mn_tirosh import words
	wl = words.split()
	nwords,ws_list,max_spaces = 10,'    \n',5
	def rand_ws_seq():
		nchars = getrandnum(1) % max_spaces + 1
		return ''.join([ws_list[getrandnum(1)%len(ws_list)] for i in range(nchars)])
	rand_pairs = [wl[getrandnum(4) % len(wl)] + rand_ws_seq() for i in range(nwords)]
	d = ''.join(rand_pairs).rstrip() + '\n'
	if opt.verbose: msg_r('Brainwallet password:\n%s' % cyan(d))
	write_data_to_file(fn,d,'brainwallet password',silent=True)

def do_between():
	if opt.pause:
		if keypress_confirm(green('Continue?'),default_yes=True):
			if opt.verbose or opt.exact_output: sys.stderr.write('\n')
		else:
			errmsg('Exiting at user request')
			sys.exit()
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
	vmsg("Comparing %s '%s' to stored reference" % (desc,chk))
	if chk == refchk:
		ok()
	else:
		if not opt.verbose: errmsg('')
		errmsg(red("""
Fatal error - %s '%s' does not match reference value '%s'.  Aborting test
""".strip() % (desc,chk,refchk)))
		sys.exit(3)

def check_deps(cmds):
	if len(cmds) != 1:
		die(1,'Usage: %s check_deps <command>' % g.prog_name)

	cmd = cmds[0]

	if cmd not in cmd_data:
		die(1,"'%s': unrecognized command" % cmd)

	if not opt.quiet:
		msg("Checking dependencies for '%s'" % (cmd))

	check_needs_rerun(ts,cmd,build=False)

	w = max(len(i) for i in rebuild_list) + 1
	for cmd in rebuild_list:
		c = rebuild_list[cmd]
		m = 'Rebuild' if (c[0] and c[1]) else 'Build' if c[0] else 'OK'
		msg('cmd {:<{w}} {}'.format(cmd+':', m, w=w))
#			mmsg(cmd,c)


def clean(usr_dirs=[]):
	if opt.skip_deps and not ia: return
	all_dirs = MMGenTestSuite().list_tmp_dirs()
	dirs = (usr_dirs or all_dirs)
	for d in sorted(dirs):
		if str(d) in all_dirs:
			cleandir(all_dirs[str(d)])
		else:
			die(1,'%s: invalid directory number' % d)
	cleandir(os.path.join('test','data_dir'))

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

		if ia and (len(cmd_data[cmd]) < 4 or cmd_data[cmd][3] != 1): return

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
				msg(yellow("Resuming at '%s'" % cmd))
				opt.resume = False
				opt.skip_deps = False
			else:
				return

		if opt.profile: start = time.time()
		self.__class__.__dict__[cmd](*([self,cmd] + al))
		if opt.profile:
			msg('\r\033[50C{:.4f}'.format(time.time() - start))

	def generate_file_deps(self,cmd):
		return [(str(n),e) for exts,n in cmd_data[cmd][2] for e in exts]

	def generate_cmd_deps(self,fdeps):
		return [cfgs[str(n)]['dep_generators'][ext] for n,ext in fdeps]

	def helpscreens(self,name,arg='--help'):
		for s in scripts:
			t = MMGenExpect(name,('mmgen-'+s),[arg],
				extra_desc='(mmgen-%s)'%s,no_output=True)
			if not ia:
				t.read(); ok()

	def longhelpscreens(self,name): self.helpscreens(name,arg='--longhelp')

	def walletgen(self,name,del_dw_run='dummy',seed_len=None,gen_dfl_wallet=False):
		if ia:
			m = "\nAnswer '{}' at the the interactive prompt".format(('n','y')[gen_dfl_wallet])
			msg(grnbg(m))
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd']+'\n')
		add_args = ([usr_rand_arg],
			['-q','-r0','-L','Interactive Mode Wallet','-P',get_tmpfile_fn(cfg,pwfile)])[bool(ia)]
		args = ['-d',cfg['tmpdir'],'-p1']
		if seed_len: args += ['-l',str(seed_len)]
		t = MMGenExpect(name,'mmgen-walletgen', args + add_args)
		if ia: return
		t.license()
		t.usr_rand(usr_rand_chars)
		t.passphrase_new('new MMGen wallet',cfg['wpasswd'])
		t.label()
		global have_dfl_wallet
		if not have_dfl_wallet:
			t.expect('move it to the data directory? (Y/n): ',('n','y')[gen_dfl_wallet])
			if gen_dfl_wallet: have_dfl_wallet = True
		t.written_to_file('MMGen wallet')
		ok()

	def walletgen_dfl_wallet(self,name,seed_len=None):
		self.walletgen(name,seed_len=seed_len,gen_dfl_wallet=True)

	def brainwalletgen_ref(self,name):
		sl_arg = '-l%s' % cfg['seed_len']
		hp_arg = '-p%s' % ref_wallet_hash_preset
		label = "test.py ref. wallet (pw '%s', seed len %s)" \
				% (ref_wallet_brainpass,cfg['seed_len'])
		bf = 'ref.mmbrain'
		args = ['-d',cfg['tmpdir'],hp_arg,sl_arg,'-ib','-L',label]
		write_to_tmpfile(cfg,bf,ref_wallet_brainpass)
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd'])
		if ia:
			add_args = ['-r0', '-q', '-P%s' % get_tmpfile_fn(cfg,pwfile),
							get_tmpfile_fn(cfg,bf)]
		else:
			add_args = [usr_rand_arg]
		t = MMGenExpect(name,'mmgen-walletconv', args + add_args)
		if ia: return
		t.license()
		t.expect('Enter brainwallet: ', ref_wallet_brainpass+'\n')
		t.passphrase_new('new MMGen wallet',cfg['wpasswd'])
		t.usr_rand(usr_rand_chars)
		sid = os.path.basename(t.written_to_file('MMGen wallet').split('-')[0])
		refcheck('Seed ID',sid,cfg['seed_id'])

	def refwalletgen(self,name): self.brainwalletgen_ref(name)

	def passchg(self,name,wf,pf):
		# ia: reuse password, since there's no way to change it non-interactively
		silence()
		write_to_tmpfile(cfg,pwfile,get_data_from_file(pf))
		end_silence()
		add_args = ([usr_rand_arg],['-q','-r0','-P',pf])[bool(ia)]
		t = MMGenExpect(name,'mmgen-passchg', add_args +
				['-d',cfg['tmpdir'],'-p','2','-L','Changed label'] + ([],[wf])[bool(wf)])
		if ia: return
		t.license()
		t.passphrase('MMGen wallet',cfgs['1']['wpasswd'],pwtype='old')
		t.expect_getend('Hash preset changed to ')
		t.passphrase('MMGen wallet',cfg['wpasswd'],pwtype='new') # reuse passphrase?
		t.expect('Repeat passphrase: ',cfg['wpasswd']+'\n')
		t.usr_rand(usr_rand_chars)
#		t.expect('Enter a wallet label.*: ','Changed Label\n',regex=True)
		t.expect_getend('Label changed to ')
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
		ok()

	def passchg_dfl_wallet(self,name,pf):
		if ia:
			m = "\nAnswer 'YES'<ENTER> at the the interactive prompt"
			msg(grnbg(m))
		return self.passchg(name=name,wf=None,pf=pf)

	def walletchk(self,name,wf,pf,desc='MMGen wallet',
			add_args=[],sid=None,pw=False,extra_desc=''):
		args = ([],['-P',pf,'-q'])[bool(ia and pf)]
		hp = cfg['hash_preset'] if 'hash_preset' in cfg else '1'
		wf_arg = ([],[wf])[bool(wf)]
		t = MMGenExpect(name,'mmgen-walletchk',
				add_args+args+['-p',hp]+wf_arg,
				extra_desc=extra_desc)
		if ia:
			if sid:
				n = (' should be','')[desc=='MMGen wallet']
				m = grnbg('Seed ID%s:' % n)
				msg(grnbg('%s %s' % (m,cyan(sid))))
			return
		if desc != 'hidden incognito data':
			t.expect("Getting %s from file '" % (desc))
		if pw:
			t.passphrase(desc,cfg['wpasswd'])
			t.expect(
				['Passphrase is OK', 'Passphrase.* are correct'],
				regex=True
				)
		chk = t.expect_getend('Valid %s for Seed ID ' % desc)[:8]
		if sid: cmp_or_die(chk,sid)
		else: ok()

	def walletchk_newpass(self,name,wf,pf):
		return self.walletchk(name,wf,pf,pw=True)

	def walletchk_newpass_dfl_wallet(self,name,pf):
		return self.walletchk_newpass(name,wf=None,pf=pf)

	def delete_dfl_wallet(self,name,pf):
		with open(os.path.join(cfg['tmpdir'],'del_dw_run'),'w') as f: pass
		if opt.no_dw_delete: return True
		for wf in [f for f in os.listdir(g.data_dir) if f[-6:]=='.mmdat']:
			os.unlink(os.path.join(g.data_dir,wf))
		MMGenExpect(name,'')
		global have_dfl_wallet
		have_dfl_wallet = False
		if not ia: ok()

	def addrgen(self,name,wf,pf=None,check_ref=False):
		add_args = ([],['-q'] + ([],['-P',pf])[bool(pf)])[ia]
		t = MMGenExpect(name,'mmgen-addrgen', add_args +
				['-d',cfg['tmpdir']] + ([],[wf])[bool(wf)] + [cfg['addr_idx_list']])
		if ia: return
		t.license()
		t.passphrase('MMGen wallet',cfg['wpasswd'])
		t.expect('Passphrase is OK')
		chk = t.expect_getend(r'Checksum for address data .*?: ',regex=True)
		if check_ref:
			refcheck('address data checksum',chk,cfg['addrfile_chk'])
			return
		t.written_to_file('Addresses',oo=True)
		ok()

	def addrgen_dfl_wallet(self,name,pf=None,check_ref=False):
		return self.addrgen(name,wf=None,pf=pf,check_ref=check_ref)

	def refaddrgen(self,name,wf,pf):
		d = ' (%s-bit seed)' % cfg['seed_len']
		self.addrgen(name,wf,pf=pf,check_ref=True)

	def addrimport(self,name,addrfile):
		add_args = ([],['-q','-t'])[ia]
		outfile = os.path.join(cfg['tmpdir'],'addrfile_w_comments')
		add_comments_to_addr_file(addrfile,outfile)
		t = MMGenExpect(name,'mmgen-addrimport', add_args + [outfile])
		if ia: return
		t.expect_getend(r'Checksum for address data .*\[.*\]: ',regex=True)
		t.expect_getend('Validating addresses...OK. ')
		t.expect("Type uppercase 'YES' to confirm: ",'\n')
		vmsg('This is a simulation, so no addresses were actually imported into the tracking\nwallet')
		ok()

	def txcreate_common(self,name,sources=['1'],non_mmgen_input='',do_label=False,txdo_args=[],add_args=[]):
		if opt.verbose or opt.exact_output:
			sys.stderr.write(green('Generating fake tracking wallet info\n'))
		silence()
		from mmgen.addr import AddrList,AddrData,AddrIdxList
		tx_data,ad = {},AddrData()
		for s in sources:
			afile = get_file_with_ext('addrs',cfgs[s]['tmpdir'])
			ai = AddrList(afile)
			ad.add(ai)
			aix = AddrIdxList(fmt_str=cfgs[s]['addr_idx_list'])
			if len(aix) != addrs_per_wallet:
				errmsg(red('Address index list length != %s: %s' %
							(addrs_per_wallet,repr(aix))))
				sys.exit()
			tx_data[s] = {
				'addrfile': afile,
				'chk': ai.chksum,
				'sid': ai.seed_id,
				'addr_idxs': aix[-2:],
			}

		unspent_data_file = os.path.join(cfg['tmpdir'],'unspent.json')
		create_fake_unspent_data(ad,unspent_data_file,tx_data,non_mmgen_input)
		if opt.verbose or opt.exact_output:
			sys.stderr.write("Fake transaction wallet data written to file '%s'\n" % unspent_data_file)

		# make the command line
		from mmgen.bitcoin import privnum2addr
		btcaddr = privnum2addr(getrandnum(32),compressed=True)

		cmd_args = ['-d',cfg['tmpdir']]
		for num in tx_data:
			s = tx_data[num]
			cmd_args += [
				'%s:%s,%s' % (s['sid'],s['addr_idxs'][0],cfgs[num]['amts'][0]),
			]
			# + one BTC address
			# + one change address and one BTC address
			if num is tx_data.keys()[-1]:
				cmd_args += ['%s:%s' % (s['sid'],s['addr_idxs'][1])]
				cmd_args += ['%s,%s' % (btcaddr,cfgs[num]['amts'][1])]

		for num in tx_data: cmd_args += [tx_data[num]['addrfile']]

		os.environ['MMGEN_BOGUS_WALLET_DATA'] = unspent_data_file
		end_silence()
		if opt.verbose or opt.exact_output: sys.stderr.write('\n')

		if ia:
			add_args += ['-q']
			m = '\nAnswer the interactive prompts as follows:\n' + \
				" 'y', 'y', 'q', '1-9'<ENTER>, ENTER, ENTER, ENTER, ENTER, 'y'"
			msg(grnbg(m))
		bwd_msg = 'MMGEN_BOGUS_WALLET_DATA=%s' % unspent_data_file
		if opt.print_cmdline: msg(bwd_msg)
		if opt.log: log_fd.write(bwd_msg + ' ')
		t = MMGenExpect(name,'mmgen-'+('txcreate','txdo')[bool(txdo_args)],['-f','0.0001'] + add_args + cmd_args + txdo_args)
		if ia: return
		t.license()

		if txdo_args and add_args: # txdo4
			t.hash_preset('key-address data','1')
			t.passphrase('key-address data',cfgs['14']['kapasswd'])
			t.expect('Check key-to-address validity? (y/N): ','y')

		for num in tx_data:
			t.expect_getend('Getting address data from file ')
			chk=t.expect_getend(r'Checksum for address data .*?: ',regex=True)
			verify_checksum_or_exit(tx_data[num]['chk'],chk)

		# not in tracking wallet warning, (1 + num sources) times
		if t.expect(['Continue anyway? (y/N): ',
				'Unable to connect to bitcoind']) == 0:
			t.send('y')
		else:
			errmsg(red('Error: unable to connect to bitcoind.  Exiting'))
			sys.exit(1)

		for num in tx_data:
			t.expect('Continue anyway? (y/N): ','y')
		t.expect(r"'q'=quit view, .*?:.",'M', regex=True)
		t.expect(r"'q'=quit view, .*?:.",'q', regex=True)
		outputs_list = [(addrs_per_wallet+1)*i + 1 for i in range(len(tx_data))]
		if non_mmgen_input: outputs_list.append(len(tx_data)*(addrs_per_wallet+1) + 1)
		t.expect('Enter a range or space-separated list of outputs to spend: ',
				' '.join([str(i) for i in outputs_list])+'\n')
		if non_mmgen_input and not txdo_args: t.expect('Accept? (y/N): ','y')
		t.expect('OK? (Y/n): ','y') # fee OK?
		t.expect('OK? (Y/n): ','y') # change OK?
		if do_label:
			t.expect('Add a comment to transaction? (y/N): ','y')
			t.expect('Comment: ',ref_tx_label.encode('utf8')+'\n')
		else:
			t.expect('Add a comment to transaction? (y/N): ','\n')
		t.tx_view()
		if txdo_args: return t
		t.expect('Save transaction? (y/N): ','y')
		t.written_to_file('Transaction')
		ok()

	def txcreate(self,name,addrfile):
		self.txcreate_common(name,sources=['1'])

	def txdo(self,name,addrfile,wallet):
		t = self.txcreate_common(name,sources=['1'],txdo_args=[wallet])
		self.txsign(name,'','',pf='',save=True,has_label=False,txdo_handle=t)
		self.txsend(name,'',txdo_handle=t)

	def txcreate_dfl_wallet(self,name,addrfile):
		self.txcreate_common(name,sources=['15'])

	def txsign_end(self,t,tnum=None,has_label=False):
		t.expect('Signing transaction')
		cprompt = ('Add a comment to transaction','Edit transaction comment')[has_label]
		t.expect('%s? (y/N): ' % cprompt,'\n')
		t.expect('Save signed transaction.*?\? \(Y/n\): ','y',regex=True)
		add = ' #' + tnum if tnum else ''
		t.written_to_file('Signed transaction' + add, oo=True)

	def txsign(self,name,txfile,wf,pf='',save=True,has_label=False,txdo_handle=None):
		add_args = ([],['-q','-P',pf])[ia]
		if ia:
			m = '\nAnswer the interactive prompts as follows:\n  ENTER, ENTER, ENTER'
			msg(grnbg(m))
		if txdo_handle:
			t = txdo_handle
			if ia: return
		else:
			t = MMGenExpect(name,'mmgen-txsign', add_args+['-d',cfg['tmpdir'],txfile]+([],[wf])[bool(wf)])
			if ia: return
			t.license()
			t.tx_view()
		t.passphrase('MMGen wallet',cfg['wpasswd'])
		if txdo_handle: return
		if save:
			self.txsign_end(t,has_label=has_label)
		else:
			cprompt = ('Add a comment to transaction','Edit transaction comment')[has_label]
			t.expect('%s? (y/N): ' % cprompt,'\n')
			t.close()
		ok()

	def txsign_dfl_wallet(self,name,txfile,pf='',save=True,has_label=False):
		return self.txsign(name,txfile,wf=None,pf=pf,save=save,has_label=has_label)

	def txsend(self,name,sigfile,txdo_handle=None):
		if txdo_handle:
			t = txdo_handle
		else:
			t = MMGenExpect(name,'mmgen-txsend', ['-d',cfg['tmpdir'],sigfile])
			t.license()
			t.tx_view()
			t.expect('Add a comment to transaction? (y/N): ','\n')
		t.expect('broadcast this transaction to the network?')
		m = 'YES, I REALLY WANT TO DO THIS'
		t.expect("'%s' to confirm: " % m,m+'\n')
		t.expect('BOGUS transaction NOT sent')
		t.written_to_file('Transaction ID')
		ok()

	def walletconv_export(self,name,wf,desc,uargs=[],out_fmt='w',pf=None,out_pw=False):
		opts = ['-d',cfg['tmpdir'],'-o',out_fmt] + uargs + \
			([],[wf])[bool(wf)] + ([],['-P',pf])[bool(pf)]
		t = MMGenExpect(name,'mmgen-walletconv',opts)
		if ia: return
		t.license()
		if not pf:
			t.passphrase('MMGen wallet',cfg['wpasswd'])
		if out_pw:
			t.passphrase_new('new '+desc,cfg['wpasswd'])
			t.usr_rand(usr_rand_chars)

		if ' '.join(desc.split()[-2:]) == 'incognito data':
			t.expect('Generating encryption key from OS random data ')
			t.expect('Generating encryption key from OS random data ')
			ic_id = t.expect_getend('New Incog Wallet ID: ')
			t.expect('Generating encryption key from OS random data ')
		if desc == 'hidden incognito data':
			write_to_tmpfile(cfg,incog_id_fn,ic_id)
			ret = t.expect(['Create? (Y/n): ',"'YES' to confirm: "])
			if ret == 0:
				t.send('\n')
				t.expect('Enter file size: ',str(hincog_bytes)+'\n')
			else:
				t.send('YES\n')
		if out_fmt == 'w': t.label()
		return t.written_to_file(capfirst(desc),oo=True)

	def export_seed(self,name,wf,desc='seed data',out_fmt='seed',pf=None):
		f = self.walletconv_export(name,wf,desc=desc,out_fmt=out_fmt,pf=pf)
		if ia: return
		silence()
		msg('%s: %s' % (capfirst(desc),cyan(get_data_from_file(f,desc))))
		end_silence()
		ok()

	def export_hex(self,name,wf,desc='hexadecimal seed data',out_fmt='hex',pf=None):
		self.export_seed(name,wf,desc=desc,out_fmt=out_fmt,pf=pf)

	def export_seed_dfl_wallet(self,name,pf,desc='seed data',out_fmt='seed'):
		self.export_seed(name,wf=None,desc=desc,out_fmt=out_fmt,pf=pf)

	def export_mnemonic(self,name,wf):
		self.export_seed(name,wf,desc='mnemonic data',out_fmt='words')

	def export_incog(self,name,wf,desc='incognito data',out_fmt='i',add_args=[]):
		uargs = ['-p1',usr_rand_arg] + add_args
		self.walletconv_export(name,wf,desc=desc,out_fmt=out_fmt,uargs=uargs,out_pw=True)
		ok()

	def export_incog_hex(self,name,wf):
		self.export_incog(name,wf,desc='hex incognito data',out_fmt='xi')

	# TODO: make outdir and hidden incog compatible (ignore --outdir and warn user?)
	def export_incog_hidden(self,name,wf):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		add_args = ['-J','%s,%s'%(rf,hincog_offset)]
		self.export_incog(
			name,wf,desc='hidden incognito data',out_fmt='hi',add_args=add_args)

	def addrgen_seed(self,name,wf,foo,desc='seed data',in_fmt='seed'):
		stdout = (False,True)[desc=='seed data'] #capture output to screen once
		add_arg = ([],['-S'])[bool(stdout)]
		t = MMGenExpect(name,'mmgen-addrgen', add_arg +
				['-i'+in_fmt,'-d',cfg['tmpdir'],wf,cfg['addr_idx_list']])
		t.license()
		t.expect_getend('Valid %s for Seed ID ' % desc)
		vmsg('Comparing generated checksum with checksum from previous address file')
		chk = t.expect_getend(r'Checksum for address data .*?: ',regex=True)
		if stdout: t.read()
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
#		t.no_overwrite()
		ok()

	def addrgen_hex(self,name,wf,foo,desc='hexadecimal seed data',in_fmt='hex'):
		self.addrgen_seed(name,wf,foo,desc=desc,in_fmt=in_fmt)

	def addrgen_mnemonic(self,name,wf,foo):
		self.addrgen_seed(name,wf,foo,desc='mnemonic data',in_fmt='words')

	def addrgen_incog(self,name,wf=[],foo='',in_fmt='i',desc='incognito data',args=[]):
		t = MMGenExpect(name,'mmgen-addrgen', args+['-i'+in_fmt,'-d',cfg['tmpdir']]+
				([],[wf])[bool(wf)] + [cfg['addr_idx_list']])
		t.license()
		t.expect_getend('Incog Wallet ID: ')
		t.hash_preset(desc,'1')
		t.passphrase('%s \w{8}' % desc, cfg['wpasswd'])
		vmsg('Comparing generated checksum with checksum from address file')
		chk = t.expect_getend(r'Checksum for address data .*?: ',regex=True)
		t.close()
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
#		t.no_overwrite()
		ok()

	def addrgen_incog_hex(self,name,wf,foo):
		self.addrgen_incog(name,wf,'',in_fmt='xi',desc='hex incognito data')

	def addrgen_incog_hidden(self,name,wf,foo):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		self.addrgen_incog(name,[],'',in_fmt='hi',desc='hidden incognito data',
			args=['-H','%s,%s'%(rf,hincog_offset),'-l',str(hincog_seedlen)])

	def keyaddrgen(self,name,wf,pf=None,check_ref=False):
		args = ['-d',cfg['tmpdir'],usr_rand_arg,wf,cfg['addr_idx_list']]
		if ia:
			m = "\nAnswer 'n' at the interactive prompt"
			msg(grnbg(m))
			args = ['-q'] + ([],['-P',pf])[bool(pf)] + args
		t = MMGenExpect(name,'mmgen-keygen', args)
		if ia: return
		t.license()
		t.passphrase('MMGen wallet',cfg['wpasswd'])
		chk = t.expect_getend(r'Checksum for key-address data .*?: ',regex=True)
		if check_ref:
			refcheck('key-address data checksum',chk,cfg['keyaddrfile_chk'])
			return
		t.expect('Encrypt key list? (y/N): ','y')
		t.usr_rand(usr_rand_chars)
		t.hash_preset('new key list','1')
#		t.passphrase_new('new key list','kafile password')
		t.passphrase_new('new key list',cfg['kapasswd'])
		t.written_to_file('Secret keys',oo=True)
		ok()

	def refkeyaddrgen(self,name,wf,pf):
		self.keyaddrgen(name,wf,pf,check_ref=True)

	def txsign_keyaddr(self,name,keyaddr_file,txfile):
		t = MMGenExpect(name,'mmgen-txsign', ['-d',cfg['tmpdir'],'-M',keyaddr_file,txfile])
		t.license()
		t.hash_preset('key-address data','1')
		t.passphrase('key-address data',cfg['kapasswd'])
		t.expect('Check key-to-address validity? (y/N): ','y')
		t.tx_view()
		self.txsign_end(t)
		ok()

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
			t.tx_view()
			t.passphrase('MMGen wallet',cfgs[cnum]['wpasswd'])
			self.txsign_end(t,cnum)
		ok()

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
		t.tx_view()
		for cnum in ('1','3'):
#			t.expect_getend('Getting MMGen wallet data from file ')
			t.passphrase('MMGen wallet',cfgs[cnum]['wpasswd'])
		self.txsign_end(t)
		ok()

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
		ok()

	def addrgen4(self,name,wf):
		self.addrgen(name,wf,pf='')

	def txcreate4(self,name,f1,f2,f3,f4,f5,f6):
		self.txcreate_common(name,sources=['1','2','3','4','14'],non_mmgen_input='4',do_label=1)

	def txdo4(self,name,f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12):
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		add_args = ['-d',cfg['tmpdir'],'-i','brain','-b'+cfg['bw_params'],'-p1','-k',non_mm_fn,'-M',f12]
		t = self.txcreate_common(name,sources=['1','2','3','4','14'],non_mmgen_input='4',do_label=1,txdo_args=[f7,f8,f9,f10],add_args=add_args)
		self.txsign4(name,f7,f8,f9,f10,f11,f12,txdo_handle=t)
		self.txsend(name,'',txdo_handle=t)

	def txsign4(self,name,f1,f2,f3,f4,f5,f6,txdo_handle=None):
		if txdo_handle:
			t = txdo_handle
		else:
			non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
			a = ['-d',cfg['tmpdir'],'-i','brain','-b'+cfg['bw_params'],'-p1','-k',non_mm_fn,'-M',f6,f1,f2,f3,f4,f5]
			t = MMGenExpect(name,'mmgen-txsign',a)
			t.license()
			t.hash_preset('key-address data','1')
			t.passphrase('key-address data',cfgs['14']['kapasswd'])
			t.expect('Check key-to-address validity? (y/N): ','y')
			t.tx_view()

		for cnum,desc in ('1','incognito data'),('3','MMGen wallet'):
			t.passphrase(('%s' % desc),cfgs[cnum]['wpasswd'])

		if txdo_handle: return
		self.txsign_end(t,has_label=True)
		ok()

	def tool_encrypt(self,name,infile=''):
		if infile:
			infn = infile
		else:
			d = os.urandom(1033)
			tmp_fn = cfg['tool_enc_infn']
			write_to_tmpfile(cfg,tmp_fn,d,binary=True)
			infn = get_tmpfile_fn(cfg,tmp_fn)
		if ia:
			pwfn = 'ni_pw'
			write_to_tmpfile(cfg,pwfn,tool_enc_passwd+'\n')
			pre = ['-P', get_tmpfile_fn(cfg,pwfn)]
			app = ['hash_preset=1']
		else:
			pre,app = [],[]
		t = MMGenExpect(name,'mmgen-tool',pre+['-d',cfg['tmpdir'],usr_rand_arg,'encrypt',infn]+app)
		if ia: return
		t.usr_rand(usr_rand_chars)
		t.hash_preset('user data','1')
		t.passphrase_new('user data',tool_enc_passwd)
		t.written_to_file('Encrypted data')
		ok()

# Generate the reference mmenc file
# 	def tool_encrypt_ref(self,name):
# 		infn = get_tmpfile_fn(cfg,cfg['tool_enc_ref_infn'])
# 		write_data_to_file(infn,cfg['tool_enc_reftext'],silent=True)
# 		self.tool_encrypt(name,infn)

	def tool_decrypt(self,name,f1,f2):
		of = name + '.out'
		if ia:
			pwfn = 'ni_pw'
			pre = ['-P', get_tmpfile_fn(cfg,pwfn)]
		else:
			pre = []
		t = MMGenExpect(name,'mmgen-tool',
			pre+['-d',cfg['tmpdir'],'decrypt',f2,'outfile='+of,'hash_preset=1'])
		if not ia:
			t.passphrase('user data',tool_enc_passwd)
			t.written_to_file('Decrypted data')
		d1 = read_from_file(f1,binary=True)
		d2 = read_from_file(get_tmpfile_fn(cfg,of),binary=True)
		cmp_or_die(d1,d2,skip_ok=ia)

	def tool_find_incog_data(self,name,f1,f2):
		i_id = read_from_file(f2).rstrip()
		vmsg('Incog ID: %s' % cyan(i_id))
		t = MMGenExpect(name,'mmgen-tool',
				['-d',cfg['tmpdir'],'find_incog_data',f1,i_id])
		if ia: return
		o = t.expect_getend('Incog data for ID %s found at offset ' % i_id)
		os.unlink(f1)
		cmp_or_die(hincog_offset,int(o))

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
		hi_opt = ['-H','%s,%s' % (ic_f,ref_wallet_incog_offset)]
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
		hi_parms = '%s,%s' % (ic_f,ref_wallet_incog_offset)
		sl_parm = '-l' + str(cfg['seed_len'])
		self.walletconv_out(name,
			'hidden incognito data', 'hi',
			uopts=['-J',hi_parms,sl_parm] + extra_uopts,
			uopts_chk=['-H',hi_parms,sl_parm],
			pw=True
		)

	def ref_wallet_chk(self,name):
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		if ia:
			write_to_tmpfile(cfg,pwfile,cfg['wpasswd'])
			pf = get_tmpfile_fn(cfg,pwfile)
		else:
			pf = None
		self.walletchk(name,wf,pf=pf,pw=True,sid=cfg['seed_id'])

	def ref_ss_chk(self,name,ss=None):
		wf = os.path.join(ref_dir,'%s.%s' % (cfg['seed_id'],ss.ext))
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
		add_args = ['-l%s' % cfg['seed_len'], '-p'+ref_bw_hash_preset]
		self.walletchk(name,wf,pf=None,add_args=add_args,
			desc='brainwallet',sid=cfg['ref_bw_seed_id'])

	def ref_brain_chk_spc3(self,name):
		self.ref_brain_chk(name,bw_file=ref_bw_file_spc)

	def ref_hincog_chk(self,name,desc='hidden incognito data'):
		for wtype,edesc,of_arg in ('hic_wallet','',[]), \
								('hic_wallet_old','(old format)',['-O']):
			ic_arg = ['-H%s,%s' % (
						os.path.join(ref_dir,cfg[wtype]),
						ref_wallet_incog_offset
					)]
			slarg = ['-l%s ' % cfg['seed_len']]
			hparg = ['-p1']
			if ia:
				write_to_tmpfile(cfg,pwfile,cfg['wpasswd'])
				add_args = ['-q','-P%s' % get_tmpfile_fn(cfg,pwfile)]
			else:
				add_args = []
			if ia and wtype == 'hic_wallet_old':
				m = grnbg("Answer 'y' at the interactive prompt if Seed ID is")
				n = cyan(cfg['seed_id'])
				msg('\n%s %s' % (m,n))
			if wtype == 'hic_wallet_old' and opt.profile: msg('')
			t = MMGenExpect(name,'mmgen-walletchk',
				add_args + slarg + hparg + of_arg + ic_arg,
				extra_desc=edesc)
			if ia: continue
			t.passphrase(desc,cfg['wpasswd'])
			if wtype == 'hic_wallet_old':
				t.expect('Is the Seed ID correct? (Y/n): ','\n')
			chk = t.expect_getend('Seed ID: ')
			t.close()
			cmp_or_die(cfg['seed_id'],chk)

	def ref_addrfile_chk(self,name,ftype='addr'):
		wf = os.path.join(ref_dir,cfg['ref_'+ftype+'file'])
		if ia:
			m = "\nAnswer the interactive prompts as follows: '1'<ENTER>, ENTER"
			msg(grnbg(m))
			pfn = 'ref_kafile_passwd'
			write_to_tmpfile(cfg,pfn,ref_kafile_pass)
			aa = ['-P',get_tmpfile_fn(cfg,pfn)]
		else:
			aa = []
		t = MMGenExpect(name,'mmgen-tool',aa+[ftype+'file_chksum',wf])
		if ia:
			k = 'ref_%saddrfile_chksum' % ('','key')[ftype == 'keyaddr']
			m = grnbg('Checksum should be:')
			n = cyan(cfg[k])
			msg(grnbg('%s %s' % (m,n)))
			return
		if ftype == 'keyaddr':
			w = 'key-address data'
			t.hash_preset(w,ref_kafile_hash_preset)
			t.passphrase(w,ref_kafile_pass)
			t.expect('Check key-to-address validity? (y/N): ','y')
		o = t.read().strip().split('\n')[-1]
		cmp_or_die(cfg['ref_'+ftype+'file_chksum'],o)

	def ref_keyaddrfile_chk(self,name):
		self.ref_addrfile_chk(name,ftype='keyaddr')

#	def txcreate8(self,name,addrfile):
#		self.txcreate_common(name,sources=['8'])

	def ref_tx_chk(self,name):
		tf = os.path.join(ref_dir,cfg['ref_tx_file'])
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd'])
		pf = get_tmpfile_fn(cfg,pwfile)
		self.txsign(name,tf,wf,pf,save=False,has_label=True)

	def ref_tool_decrypt(self,name):
		f = os.path.join(ref_dir,ref_enc_fn)
		aa = []
		if ia:
			pfn = 'tool_enc_passwd'
			write_to_tmpfile(cfg,pfn,tool_enc_passwd)
			aa = ['-P',get_tmpfile_fn(cfg,pfn)]
		t = MMGenExpect(name,'mmgen-tool',
				aa + ['-q','decrypt',f,'outfile=-','hash_preset=1'])
		if ia: return
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
		if ia:
			opts += ['-q']
			msg('')
			if pw:
				pfn = 'ni_passwd'
				write_to_tmpfile(cfg,pfn,cfg['wpasswd'])
				opts += ['-P',get_tmpfile_fn(cfg,pfn)]
			if desc == 'brainwallet':
				m = "\nAnswer the interactive prompt as follows: '%s'<ENTER>"
				msg(grnbg(m % ref_wallet_brainpass))
			if '-O' in uopts:
				m = grnbg("Answer 'y' at the interactive prompt if Seed ID is")
				n = cyan(cfg['seed_id'])
				msg('\n%s %s' % (m,n))
		t = MMGenExpect(name,'mmgen-walletconv',opts+uopts+if_arg,extra_desc=d)
		if ia:
			m = grnbg('Seed ID should be:')
			n = cyan(cfg['seed_id'])
			msg(grnbg('%s %s' % (m,n)))
			return
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
		ok()
		# back check of result
		if opt.profile: msg('')
		self.walletchk(name,wf,pf=None,
				desc='mnemonic data',
				sid=cfg['seed_id'],
				extra_desc='(check)'
				)

	def walletconv_out(self,name,desc,out_fmt='w',uopts=[],uopts_chk=[],pw=False):
		opts = ['-d',cfg['tmpdir'],'-p1','-o',out_fmt] + uopts
		if ia:
			pfn = 'ni_passwd'
			write_to_tmpfile(cfg,pfn,cfg['wpasswd'])
			l = 'Non-Interactive Test Wallet'
			aa = ['-q','-L',l,'-r0','-P',get_tmpfile_fn(cfg,pfn)]
			if desc == 'hidden incognito data':
				rd = os.urandom(ref_wallet_incog_offset+128)
				write_to_tmpfile(cfg,hincog_fn,rd)
		else:
			aa = [usr_rand_arg]
		infile = os.path.join(ref_dir,cfg['seed_id']+'.mmwords')
		t = MMGenExpect(name,'mmgen-walletconv',aa+opts+[infile],extra_desc='(convert)')

		add_args = ['-l%s' % cfg['seed_len']]
		if ia:
			pfn = 'ni_passwd'
			write_to_tmpfile(cfg,pfn,cfg['wpasswd'])
			pf = get_tmpfile_fn(cfg,pfn)
			if desc != 'hidden incognito data':
				from mmgen.seed import SeedSource
				ext = SeedSource.fmt_code_to_type(out_fmt).ext
				hps = ('',',1')[bool(pw)]   # TODO real hp
				pre_ext = '[%s%s].' % (cfg['seed_len'],hps)
				wf = get_file_with_ext(pre_ext+ext,cfg['tmpdir'],no_dot=True)
		else:
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
			ok()

		if desc == 'hidden incognito data':
			add_args += uopts_chk
			wf = None
		if opt.profile: msg('')
		self.walletchk(name,wf,pf=pf,
			desc=desc,sid=cfg['seed_id'],pw=pw,
			add_args=add_args,
			extra_desc='(check)')
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
			'refaddrgen',
			'ref_seed_chk',
			'ref_hex_chk',
			'ref_mn_chk',
			'ref_brain_chk',
			'ref_hincog_chk',
			'refkeyaddrgen',
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
	m1 = 'All requested tests finished OK, elapsed time: {:02d}:{:02d}\n'
	m2 = ('','Please re-check all {} control values against the program output.\n'.format(grnbg('HIGHLIGHTED')))[ia]
	sys.stderr.write(green(m1.format(t/60,t%60)))
	sys.stderr.write(m2)

ts = MMGenTestSuite()

try:
	if cmd_args:
		for arg in cmd_args:
			if arg in utils:
				globals()[arg](cmd_args[cmd_args.index(arg)+1:])
				sys.exit()
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
				die(1,'%s: unrecognized command' % arg)
	else:
		clean()
		for cmd in cmd_data:
			if cmd[:5] == 'info_':
				msg(green('%sTesting %s' % (('\n','')[bool(opt.resume)],cmd_data[cmd][0])))
				continue
			ts.do_cmd(cmd)
			if cmd is not cmd_data.keys()[-1]: do_between()
except KeyboardInterrupt:
	die(1,'\nExiting at user request')
	raise
except:
	sys.stderr = stderr_save
	raise

end_msg()
