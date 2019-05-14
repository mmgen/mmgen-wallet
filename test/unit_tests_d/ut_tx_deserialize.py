#!/usr/bin/env python3
"""
test/unit_tests_d/ut_tx_deserialize: TX deserialization unit test for the MMGen suite
"""

import os
from mmgen.common import *

class tx_deserialize(object):

	def _get_core_repo_root(self):
		self.core_repo_root = os.getenv('CORE_REPO_ROOT')
		if not self.core_repo_root:
			die(1,'The environmental variable CORE_REPO_ROOT must be set before running this test')

	def run_test(self,name):

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
