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
test/scrambletest.py: seed scrambling and addrlist data generation tests for all supported altcoins
"""

import sys,os,subprocess
repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path.__setitem__(0,repo_root)
os.environ['MMGEN_TEST_SUITE'] = '1'

# Import this _after_ local path's been added to sys.path
from mmgen.common import *
from test.common import *

opts_data = {
	'text': {
		'desc': 'Test seed scrambling and addrlist data generation for all supported altcoins',
		'usage':'[options] [command]',
		'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-C, --coverage      Produce code coverage info using trace module
-l, --list-cmds     List and describe the tests and commands in this test suite
-s, --system        Test scripts and modules installed on system rather than
                    those in the repo root
-v, --verbose       Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
	}
}

cmd_args = opts.init(opts_data)

os.environ['MMGEN_DEBUG_ADDRLIST'] = '1'
if not opt.system:
	os.environ['PYTHONPATH'] = repo_root

# TODO: add vectors for 'mmgen-passgen'
from collections import namedtuple
td = namedtuple('scrambletest_entry',['seed','str','id_str','lbl','addr'])

coin_data = {
#                   SCRAMBLED_SEED[:8] SCRAMBLE_KEY     ID_STR   LBL              FIRST ADDR
'btc':           td('456d7f5f1c4bfe3b','(none)',        '',      '',              '1MU7EdgqYy9JX35L25hR6CmXXcSEBDAwyv'),
'btc_compressed':td('bf98a4af5464a4ef','compressed',    '-C',    'COMPRESSED',    '1F97Jd89wwmu4ELadesAdGDzg3d8Y6j5iP'),
'btc_segwit':    td('b56962d829ffc678','segwit',        '-S',    'SEGWIT',        '36TvVzU5mxSjJ3D9qKAmYzCV7iUqtTDezF'),
'btc_bech32':    td('d09eea818f9ad17f','bech32',        '-B',    'BECH32',        'bc1q8snv94j6959y3gkqv4gku0cm5mersnpucsvw5z'),
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

cvr_opts = ' -m trace --count --coverdir={} --file={}'.format(*init_coverage()) if opt.coverage else ''
cmd_base = 'python3{} cmds/mmgen-{{}}gen -qS'.format(cvr_opts)

def get_cmd_output(cmd):
	p = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	o = p.stdout.read().decode()
	err = p.stderr.read().decode()
	exit_val = p.wait()
	if exit_val != 0:
		ydie(2,'\nSpawned program exited with error code {}:\n{}'.format(exit_val,err))
	return o.splitlines()

def do_test(cmd,tdata,msg_str,addr_desc):
	vmsg(green('Executing: {}'.format(cmd)))
	msg_r('Testing: ' + msg_str)

	lines = get_cmd_output(cmd)
	cmd_out = dict([e[9:].split(': ') for e in lines if e.startswith('sc_debug_')])
	cmd_out['addr'] = lines[-2].split(None,1)[-1]

	ref_data = tdata._asdict()
	vmsg('')
	for k in ref_data:
		if cmd_out[k] == ref_data[k]:
			s = k.replace('seed','seed[:8]').replace('addr',addr_desc)
			vmsg('  {:9}: {}'.format(s,cmd_out[k]))
		else:
			rdie(1,'\nError: sc_{} value {} does not match reference value {}'.format(k,cmd_out[k],ref_data[k]))
	msg('OK')

def do_coin_tests():
	bmsg('Testing address scramble strings and list IDs')
	for tname,tdata in coin_data.items():
		if tname == 'zec_zcash_z' and g.platform == 'win':
			msg("Skipping 'zec_zcash_z' test for Windows platform")
			continue
		coin,mmtype = tname.split('_',1) if '_' in tname else (tname,None)
		type_arg = ' --type='+mmtype if mmtype else ''
		cmd = cmd_base.format('addr') + ' --coin={}{} test/ref/98831F3A.mmwords 1'.format(coin,type_arg)
		do_test(cmd,tdata,'--coin {:4} {:22}'.format(coin.upper(),type_arg),'address')

start_time = int(time.time())

do_coin_tests()

t = int(time.time()) - start_time
m = 'All requested tests finished OK, elapsed time: {:02}:{:02}'
gmsg(m.format(t//60,t%60))
