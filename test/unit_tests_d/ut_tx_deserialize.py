#!/usr/bin/env python3
"""
test/unit_tests_d/ut_tx_deserialize: TX deserialization unit test for the MMGen suite
"""

import os,json

from mmgen.common import *
from ..include.common import *
from mmgen.protocol import init_proto
from mmgen.tx import UnsignedTX
from mmgen.base_proto.bitcoin.tx.base import DeserializeTX
from mmgen.rpc import rpc_init
from mmgen.daemon import CoinDaemon

class unit_test(object):

	def _get_core_repo_root(self):
		self.core_repo_root = os.getenv('CORE_REPO_ROOT')
		if not self.core_repo_root:
			die(1,'The environmental variable CORE_REPO_ROOT must be set before running this test')

	def run_test(self,name,ut):

		async def test_tx(tx_proto,tx_hex,desc,n):

			def has_nonstandard_outputs(outputs):
				for o in outputs:
					t = o['scriptPubKey']['type']
					if t in ('nonstandard','pubkey','nulldata'):
						return True
				return False

			rpc = await rpc_init(proto=tx_proto)
			d = await rpc.call('decoderawtransaction',tx_hex)

			if has_nonstandard_outputs(d['vout']): return False

			dt = DeserializeTX(tx_proto,tx_hex)

			if opt.verbose:
				Msg('\n====================================================')
			Msg_r('.' if opt.quiet else f'{n:>3}) {desc}\n')
			if opt.verbose:
				Pmsg(d)
				Msg('----------------------------------------------------')
				Pmsg(dt)

			# metadata
			assert dt.txid == d['txid'],'TXID does not match'
			assert dt.locktime == d['locktime'],'Locktime does not match'
			assert dt.version == d['version'],'Version does not match'

			# inputs
			a,b = d['vin'],dt.txins
			for i in range(len(a)):
				assert a[i]['txid'] == b[i]['txid'],f'TxID of input {i} does not match'
				assert a[i]['vout'] == b[i]['vout'],f'vout of input {i} does not match'
				assert a[i]['sequence'] == int(b[i]['nSeq'],16),(
					f'nSeq of input {i} does not match')
				if 'txinwitness' in a[i]:
					assert a[i]['txinwitness'] == b[i]['witness'],(
						f'witness of input {i} does not match')

			# outputs
			a,b = d['vout'],dt.txouts
			for i in range(len(a)):
				if 'addresses' in a[i]['scriptPubKey']:
					A = a[i]['scriptPubKey']['addresses'][0]
					B = b[i]['address']
					fs = 'address of output {} does not match\nA: {}\nB: {}'
					assert A == B, fs.format(i,A,B)

				A = a[i]['value']
				B = b[i]['amount']
				fs = 'value of output {} does not match\nA: {}\nB: {}'
				assert A == B, fs.format(i,A,B)

				A = a[i]['scriptPubKey']['hex']
				B = b[i]['scriptPubKey']
				fs = 'scriptPubKey of output {} does not match\nA: {}\nB: {}'
				assert A == B, fs.format(i,A,B)

			return True

		def print_info(fn,extra_desc):
			if opt.names:
				Msg_r('{} {} ({}){}'.format(
					purple('Testing'),
					cyan(name),
					extra_desc,
					'' if opt.quiet else '\n'))
			else:
				Msg_r(f'Testing {extra_desc} transactions from {fn!r}')
				if not opt.quiet:
					Msg('')

		async def test_core_vectors():
			self._get_core_repo_root()
			fn_b = 'src/test/data/tx_valid.json'
			fn = os.path.join(self.core_repo_root,fn_b)
			with open(fn) as fp:
				data = json.loads(fp.read())
			print_info(fn_b,'Core test vector')
			n = 1
			for e in data:
				if type(e[0]) == list:
					await test_tx(
						tx_proto = init_proto('btc',need_amt=True),
						tx_hex   = e[1],
						desc     = desc,
						n        = n )
					n += 1
				else:
					desc = e[0]
			Msg('OK')

		async def test_mmgen_txs():
			fns = ( ('btc',False,'test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'),
					('btc',True,'test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx'),
				#	('bch',False,'test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx')
				)
			print_info('test/ref/*rawtx','MMGen reference')
			for n,(coin,testnet,fn) in enumerate(fns):
				tx = UnsignedTX(filename=fn)
				await test_tx(
					tx_proto = tx.proto,
					tx_hex   = tx.serialized,
					desc     = fn,
					n        = n+1 )
			Msg('OK')

		start_test_daemons('btc',remove_datadir=True)
		start_test_daemons('btc_tn')
		run_session(test_core_vectors())
		run_session(test_mmgen_txs())
		stop_test_daemons('btc','btc_tn')

		return True
