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
test/unit_tests.py:  Unit tests for the MMGen suite
"""

import sys,os,time

repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path[0] = repo_root
os.environ['MMGEN_TEST_SUITE'] = '1'

# Import these _after_ prepending repo_root to sys.path
from mmgen.common import *

opts_data = {
	'text': {
		'desc': "Unit tests for the MMGen suite",
		'usage':'[options] [tests]',
		'options': """
-h, --help       Print this help message
-l, --list       List available tests
-n, --names      Print command names instead of descriptions
-q, --quiet      Produce quieter output
-v, --verbose    Produce more verbose output
""",
	'notes': """
If no test is specified, all available tests are run
	"""
	}
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]
cmd_args = opts.init(opts_data)

class UnitTests(object):

	def _get_core_repo_root(self):
		self.core_repo_root = os.getenv('CORE_REPO_ROOT')
		if not self.core_repo_root:
			die(1,'The environmental variable CORE_REPO_ROOT must be set before running this test')

	def tx_deserialize(self,name):

		def test_tx(txhex,desc,n):

			def has_nonstandard_outputs(outputs):
				for o in outputs:
					t = o['scriptPubKey']['type']
					if t in ('nonstandard','pubkey','nulldata'):
						return True
				return False

			d = g.rpch.decoderawtransaction(txhex)

			if has_nonstandard_outputs(d['vout']): return False

			dt = DeserializedTX(txhex)

			if opt.verbose:
				Msg('\n====================================================')
			Msg_r('.' if opt.quiet else '{:>3}) {}\n'.format(n,desc))
			if opt.verbose:
				Pmsg(d)
				Msg('----------------------------------------------------')
				Pmsg(dt)

			# metadata
			assert dt['txid'] == d['txid'],'TXID does not match'
			assert dt['lock_time'] == d['locktime'],'Locktime does not match'
			assert dt['version'] == d['version'],'Version does not match'

			# inputs
			a,b = d['vin'],dt['txins']
			for i in range(len(a)):
				assert a[i]['txid'] == b[i]['txid'],'TxID of input {} does not match'.format(i)
				assert a[i]['vout'] == b[i]['vout'],'vout of input {} does not match'.format(i)
				assert a[i]['sequence'] == int(b[i]['nSeq'],16),(
					'nSeq of input {} does not match'.format(i))
				if 'txinwitness' in a[i]:
					assert a[i]['txinwitness'] == b[i]['witness'],(
						'witness of input {} does not match'.format(i))

			# outputs
			a,b = d['vout'],dt['txouts']
			for i in range(len(a)):
				assert a[i]['scriptPubKey']['addresses'][0] == b[i]['address'],(
					'address of ouput {} does not match'.format(i))
				assert a[i]['value'] == b[i]['amount'],'value of ouput {} does not match'.format(i)
				assert a[i]['scriptPubKey']['hex'] == b[i]['scriptPubKey'],(
					'scriptPubKey of ouput {} does not match'.format(i))

			return True

		def print_info(fn,extra_desc):
			if opt.names:
				Msg_r('{} {} ({}){}'.format(
					purple('Testing'),
					cyan(name),
					extra_desc,
					'' if opt.quiet else '\n'))
			else:
				Msg_r('Testing transactions from {!r}'.format(fn))
				if not opt.quiet: Msg('')

		def test_core_vectors():
			self._get_core_repo_root()
			fn = os.path.join(self.core_repo_root,'src/test/data/tx_valid.json')
			data = json.loads(open(fn).read())
			print_info(fn,'Core test vectors')
			n = 1
			for e in data:
				if type(e[0]) == list:
					test_tx(e[1],desc,n)
					n += 1
				else:
					desc = e[0]
			Msg('OK')

		def test_mmgen_txs():
			fns = ( ('btc',False,'test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'),
					('btc',True,'test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx'),
					('bch',False,'test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx') )
			from mmgen.protocol import init_coin
			from mmgen.tx import MMGenTX
			print_info('test/ref/*rawtx','MMGen reference transactions')
			for n,(coin,tn,fn) in enumerate(fns):
				init_coin(coin,tn)
				rpc_init(reinit=True)
				test_tx(MMGenTX(fn).hex,fn,n+1)
			init_coin('btc',False)
			rpc_init(reinit=True)
			Msg('OK')

		from mmgen.tx import DeserializedTX
		import json

		test_mmgen_txs()
		test_core_vectors()

		return True

def exit_msg():
	t = int(time.time()) - start_time
	gmsg('All requested tests finished OK, elapsed time: {:02}:{:02}'.format(t//60,t%60))

def run_unit_test(test):
	gmsg('Running unit test {}'.format(test))
	t = UnitTests()
	return getattr(t,test)(test)

all_tests = filter(lambda s: s[0] != '_',dir(UnitTests))
start_time = int(time.time())

if opt.list:
	Die(0,' '.join(all_tests))

try:
	for test in cmd_args:
		if test not in all_tests:
			die(1,"'{}': test not recognized".format(test))
	for test in (cmd_args or all_tests):
		if not run_unit_test(test):
			rdie(2,'Test failed')
	exit_msg()
except KeyboardInterrupt:
	die(1,green('\nExiting at user request'))
