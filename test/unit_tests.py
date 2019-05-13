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
-f, --fast       Speed up execution by reducing rounds on some tests
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

	def subseed(self,name):
		from mmgen.seed import Seed
		from mmgen.obj import SubSeedIdxRange

		def basic_ops():
			msg_r('Testing basic ops...')
			for a,b,c,d,e,f,h in (
					(8,'4710FBF0','0C1B0615','803B165C','2669AC64',256,'10L'),
					(6,'9D07ABBD','EBA9C33F','20787E6A','192E2AA2',192,'10L'),
					(4,'43670520','04A4CCB3','B5F21D7B','C1934CFF',128,'10L'),
				):

				seed_bin = bytes.fromhex('deadbeef' * a)
				seed = Seed(seed_bin)
				assert seed.sid == b, seed.sid

				subseed = seed.subseed('2s')
				assert subseed.sid == c, subseed.sid

				subseed = seed.subseed('3')
				assert subseed.sid == d, subseed.sid

				subseed = seed.subseed_by_seed_id(e)
				assert subseed.length == f, subseed.length
				assert subseed.sid == e, subseed.sid
				assert subseed.idx == 10, subseed.idx
				assert subseed.ss_idx == h, subseed.ss_idx

				seed2 = Seed(seed_bin)
				s2s = seed2.subseeds['short']
				s2l = seed2.subseeds['long']

				seed2.gen_subseeds(1)
				assert len(s2s) == 1, len(s2s)

				seed2.gen_subseeds(1) # do nothing
				seed2.gen_subseeds(2) # append one item

				seed2.gen_subseeds(5)
				assert len(s2s) == 5, len(s2s)

				seed2.gen_subseeds(3) # do nothing
				assert len(s2l) == 5, len(s2l)

				seed2.gen_subseeds(10)
				assert len(s2s) == 10, len(s2s)

				assert seed.pformat() == seed2.pformat()

				s = seed.fmt_subseeds()
				s_lines = s.strip().split('\n')
				assert len(s_lines) == g.subseeds + 4, s

				a = seed.subseed('2L').sid
				b = [e for e in s_lines if ' 2L:' in e][0].strip().split()[1]
				assert a == b, b

				c = seed.subseed('2').sid
				assert c == a, c

				a = seed.subseed('5S').sid
				b = [e for e in s_lines if ' 5S:' in e][0].strip().split()[3]
				assert a == b, b

				s = seed.fmt_subseeds(g.subseeds+1,g.subseeds+2)
				s_lines = s.strip().split('\n')
				assert len(s_lines) == 6, s

				ss_idx = str(g.subseeds+2) + 'S'
				a = seed.subseed(ss_idx).sid
				b = [e for e in s_lines if ' {}:'.format(ss_idx) in e][0].strip().split()[3]
				assert a == b, b

				s = seed.fmt_subseeds(1,2)
				s_lines = s.strip().split('\n')
				assert len(s_lines) == 6, s

			msg('OK')

		def defaults_and_limits():
			msg_r('Testing defaults and limits...')

			seed_bin = bytes.fromhex('deadbeef' * 8)
			seed = Seed(seed_bin)
			seed.gen_subseeds()
			ss = seed.subseeds
			assert len(ss['short']) == g.subseeds, ss['short']
			assert len(ss['long']) == g.subseeds, ss['long']

			seed = Seed(seed_bin)
			seed.subseed_by_seed_id('EEEEEEEE')
			ss = seed.subseeds
			assert len(ss['short']) == g.subseeds, ss['short']
			assert len(ss['long']) == g.subseeds, ss['long']

			seed = Seed(seed_bin)
			subseed = seed.subseed_by_seed_id('803B165C')
			assert subseed.sid == '803B165C', subseed.sid
			assert subseed.idx == 3, subseed.idx

			seed = Seed(seed_bin)
			subseed = seed.subseed_by_seed_id('803B165C',last_idx=1)
			assert subseed == None, subseed

			r = SubSeedIdxRange('1-5')
			r2 = SubSeedIdxRange(1,5)
			assert r2 == r, r2
			assert r == (r.first,r.last), r
			assert r.first == 1, r.first
			assert r.last == 5, r.last
			assert r.items == [1,2,3,4,5], r.items
			assert list(r.iterate()) == r.items, list(r.iterate())

			r = SubSeedIdxRange('22')
			r2 = SubSeedIdxRange(22,22)
			assert r2 == r, r2
			assert r == (r.first,r.last), r
			assert r.first == 22, r.first
			assert r.last == 22, r.last
			assert r.items == [22], r
			assert list(r.iterate()) == r.items, list(r.iterate())

			r = SubSeedIdxRange('3-3')
			assert r.items == [3], r.items

			r = SubSeedIdxRange('{}-{}'.format(g.subseeds-1,g.subseeds))
			assert r.items == [g.subseeds-1,g.subseeds], r.items

			for n,e in enumerate(SubSeedIdxRange('1-5').iterate(),1):
				assert n == e, e

			assert n == 5, n

			msg('OK')

		def collisions():
			ss_count,ltr,last_sid,collisions_chk = (
				(SubSeedIdxRange.max_idx,'S','2788F26B',470),
				(49509,'L','8D1FE500',2)
			)[bool(opt.fast)]

			last_idx = str(ss_count) + ltr

			msg_r('Testing Seed ID collisions ({} subseed pairs)...'.format(ss_count))

			seed_bin = bytes.fromhex('12abcdef' * 8)
			seed = Seed(seed_bin)

			seed.gen_subseeds(ss_count)
			ss = seed.subseeds

			assert seed.subseed(last_idx).sid == last_sid, seed.subseed(last_idx).sid

			for sid in ss['long']:
				# msg(sid)
				assert sid not in ss['short']

			collisions = 0
			for k in ('short','long'):
				for sid in ss[k]:
					collisions += ss[k][sid][1]

			assert collisions == collisions_chk, collisions
			msg_r('({} collisions) '.format(collisions))
			msg('OK')

		basic_ops()
		defaults_and_limits()
		collisions()

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
