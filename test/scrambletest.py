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
test/scrambletest.py: seed scrambling and addrlist data generation tests for all
                      supported coins + passwords
"""

import sys, os, time
from subprocess import run, PIPE
from collections import namedtuple

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from mmgen.main import launch
from mmgen.cfg import Config
from mmgen.util import msg, msg_r, bmsg, die, list_gen
from mmgen.color import gray, green
from test.include.common import set_globals, init_coverage, end_msg

opts_data = {
	'text': {
		'desc': 'Test seed scrambling and addrlist data generation for all supported altcoins',
		'usage':'[options] [command]',
		'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long (global) options
-a, --no-altcoin    Skip altcoin tests
-C, --coverage      Produce code coverage info using trace module
-l, --list-cmds     List and describe the tests and commands in this test suite
-v, --verbose       Produce more verbose output
""",
	'notes': """
Valid commands: 'coin', 'pw'
If no command is given, the whole suite of tests is run.
"""
	}
}

cfg = Config(opts_data=opts_data)

set_globals(cfg)

td = namedtuple('scrambletest_entry', ['seed', 'str', 'id_str', 'lbl', 'addr'])

bitcoin_data = {
#                   SCRAMBLED_SEED[:8] SCRAMBLE_KEY     ID_STR   LBL          FIRST ADDR
'btc':           td('456d7f5f1c4bfe3b','(none)',        '',      '',          '1MU7EdgqYy9JX35L25hR6CmXXcSEBDAwyv'),
'btc_compressed':td('bf98a4af5464a4ef','compressed',    '-C',    'COMPRESSED','1F97Jd89wwmu4ELadesAdGDzg3d8Y6j5iP'),
'btc_segwit':    td('b56962d829ffc678','segwit',        '-S',    'SEGWIT',    '36TvVzU5mxSjJ3D9qKAmYzCV7iUqtTDezF'),
'btc_bech32':    td('d09eea818f9ad17f','bech32',        '-B',    'BECH32',    'bc1q8snv94j6959y3gkqv4gku0cm5mersnpucsvw5z'),
}

altcoin_data = {
'bch':           td('456d7f5f1c4bfe3b','(none)',        '',      '',              '1MU7EdgqYy9JX35L25hR6CmXXcSEBDAwyv'),
'bch_compressed':td('bf98a4af5464a4ef','compressed',    '-C',    'COMPRESSED',    '1F97Jd89wwmu4ELadesAdGDzg3d8Y6j5iP'),
'ltc':           td('b11f16632e63ba92','ltc:legacy',    '-LTC',  'LTC',           'LMxB474SVfxeYdqxNrM1WZDZMnifteSMv1'),
'ltc_compressed':td('7ccf465d466ee7d3','ltc:compressed','-LTC-C','LTC:COMPRESSED','LdkebBKVXSs6NNoPJWGM8KciDnL8LhXXjb'),
'ltc_segwit':    td('9460f5ba15e82768','ltc:segwit',    '-LTC-S','LTC:SEGWIT',    'MQrY3vEbqKMBgegXrSaR93R2HoTDE5bKrY'),
'ltc_bech32':    td('dbdbff2e196e27d3','ltc:bech32',    '-LTC-B','LTC:BECH32',    'ltc1qdvgqsz94ht20lr8fyk5v7n884hu9p7d8k9easu'),
'eth':           td('213ed116869b19f2','eth',           '-ETH',  'ETH',           'e704b6cfd9f0edb2e6cfbd0c913438d37ede7b35'),
'etc':           td('909def37096f5ab8','etc',           '-ETC',  'ETC',           '1a6acbef8c38f52f20d04ecded2992b04d8608d7'),
'dash':          td('1319d347b021f952','dash:legacy',   '-DASH', 'DASH',          'XoK491fppGNZQUUS9uEFkT6L9u8xxVFJNJ'),
'emc':           td('7e1a29853d2db875','emc:legacy',    '-EMC',  'EMC',           'EU4L6x2b5QUb2gRQsBAAuB8TuPEwUxCNZU'),
'zec':           td('0bf9b5b20af7b5a0','zec:legacy',    '-ZEC',  'ZEC',           't1URz8BHxV38v3gsaN6oHQNKC16s35R9WkY'),
'zec_zcash_z':   td('b15570d033df9b1a','zec:zcash_z',   '-ZEC-Z','ZEC:ZCASH_Z',   'zcLMMsnzfFYZWU4avRBnuc83yh4jTtJXbtP32uWrs3ickzu1krMU4ppZCQPTwwfE9hLnRuFDSYF8VFW13aT9eeQK8aov3Ge'),
'xmr':           td('c76af3b088da3364','xmr:monero',    '-XMR-M','XMR:MONERO',    '41tmwZd2CdXEGtWqGY9fH9FVtQM8VxZASYPQ3VJQhFjtGWYzQFuidD21vJYTi2yy3tXRYXTNXBTaYVLav62rwUUpFFyicZU'),
}

passwd_data = {
'dfl_dfl_αω':  td('b78c363f3d6714f6', 'b58:20:αω',  '-αω-b58-20',  'αω b58:20',  'L3JcAZze6LQS2TFodoW9'),
'dfl_H_αω':    td('2cba1ba1a73d5497', 'b58:10:αω',  '-αω-b58-10',  'αω b58:10',  'KgSBfzPBWj'),
'b32_dfl_αω':  td('ad71ff8d0512660d', 'b32:24:αω',  '-αω-b32-24',  'αω b32:24',  'VQFESDGWAQCOCSG6GDLIG5OQ'),
'b32_H_αω':    td('b050a1613dd4d3ad', 'b32:12:αω',  '-αω-b32-12',  'αω b32:12',  'QTI7HTVN3JOE'),
'hex_dfl_αω':  td('8322b26abd931d55', 'hex:64:αω',  '-αω-hex-64',  'αω hex:64',  '6e9f8d5d2ec6c4f2a079b163e37f5dc2a7e6adb221c4de315078ffad971ba260'),
'hex_H_αω':    td('46beb852d38ed5c4', 'hex:32:αω',  '-αω-hex-32',  'αω hex:32',  '86143b36b649728cc8f3677872ed37d3'),
'bip39_dfl_αω':td('95b383d5092a55df', 'bip39:24:αω','-αω-bip39-24','αω bip39:24','treat athlete brand top beauty poverty senior unhappy vacant domain yellow scale fossil aim lonely fatal sun nuclear such ancient stage require stool similar'),
'bip39_18_αω': td('29e5a605ffa36142', 'bip39:18:αω','-αω-bip39-18','αω bip39:18','better legal various ketchup then range festival either tomato cradle say absorb solar earth alter pattern canyon liar'),
'bip39_12_αω': td('efa13cb309d7fc1d', 'bip39:12:αω','-αω-bip39-12','αω bip39:12','lady oppose theme fit position merry reopen acquire tuna dentist young chunk'),
'xmrseed_dfl_αω':td('62f5b72a5ca89cab', 'xmrseed:25:αω','-αω-xmrseed-25','αω xmrseed:25','tequila eden skulls giving jester hospital dreams bakery adjust nanny cactus inwardly films amply nanny soggy vials muppet yellow woken ashtray organs exhale foes eden'),
}

run_env = dict(os.environ)
run_env['MMGEN_DEBUG_ADDRLIST'] = '1'
words_file = 'test/ref/98831F3A.mmwords'
cvrg_opts = '-m trace --count --coverdir={} --file={}'.format(*init_coverage()).split() if cfg.coverage else []

def make_cmd(progname, opts, add_opts, args):
	return ['python3'] + cvrg_opts + [f'cmds/{progname}', '-qS'] + opts + add_opts + [words_file] + args + ['1']

def run_cmd(cmd):
	cp = run(cmd, stdout=PIPE, stderr=PIPE, text=True, env=run_env)
	if cp.returncode != 0:
		die(2, f'\nSpawned program exited with error code {cp.returncode}:\n{cp.stderr}')
	return cp.stdout.splitlines()

def run_test(progname, opts, add_opts, args, test_data, addr_desc, opts_w):
	cmd = make_cmd(progname, opts, add_opts, args)
	if cfg.verbose:
		msg(green(f'Executing: {" ".join(cmd)}'))
	else:
		msg_r('Testing: {} {:{w}} '.format(progname, ' '.join(opts), w=opts_w))

	lines = run_cmd(cmd)
	cmd_out = dict([e[9:].split(': ') for e in lines if e.startswith('sc_debug_')])
	cmd_out['addr'] = lines[-2].split(None, 1)[-1]

	ref_data = test_data._asdict()
	for k in ref_data:
		if cmd_out[k] == ref_data[k]:
			s = k.replace('seed', 'seed[:8]').replace('addr', addr_desc)
			cfg._util.vmsg(f'  {s:9}: {cmd_out[k]}')
		else:
			die(4, f'\nError: sc_{k} value {cmd_out[k]} does not match reference value {ref_data[k]}')
	msg(green('OK') if cfg.verbose else 'OK')

def make_coin_test_data():
	bmsg('Testing address scramble strings and list IDs')
	coin_data = bitcoin_data | ({} if cfg.no_altcoin else altcoin_data)
	for id_str, test_data in coin_data.items():
		if id_str == 'zec_zcash_z' and sys.platform == 'win32':
			msg(gray("Skipping 'zec_zcash_z' test for Windows platform"))
			continue
		coin, mmtype = id_str.split('_', 1) if '_' in id_str else (id_str, None)
		opts = list_gen(
			[f'--coin={coin}'],
			[f'--type={mmtype}', mmtype],
			['--cashaddr=0', coin == 'bch']
		)
		yield ('mmgen-addrgen', opts, [], [], test_data, 'address')

def make_passwd_test_data():
	bmsg('Testing password scramble strings and list IDs')
	for id_str, test_data in passwd_data.items():
		if id_str.startswith('xmrseed') and cfg.no_altcoin:
			continue
		pw_fmt, pw_len, pw_id = id_str.split('_')
		opts = list_gen(
			[f'--passwd-fmt={pw_fmt}', pw_fmt != 'dfl'],
			[f'--passwd-len={pw_len}', pw_len != 'dfl'],
		)
		yield ('mmgen-passgen', opts, ['--accept-defaults'], [pw_id], test_data, 'password')

def main():
	start_time = int(time.time())

	cmds = cfg._args or ('coin', 'pw')
	funcs = {'coin': make_coin_test_data, 'pw': make_passwd_test_data}
	for cmd in cmds:
		data = tuple(funcs[cmd]())
		opts_w = max(len(' '.join(e[1])) for e in data)
		for d in data:
			run_test(*d, opts_w)

	end_msg(int(time.time()) - start_time)

launch(func=main)
