#!/usr/bin/env python3
"""
test/unit_tests_d/ut_tx_deserialize: TX deserialization unit tests for the MMGen suite
"""

import os,json

from mmgen.common import *
from ..include.common import *
from mmgen.protocol import init_proto
from mmgen.tx import CompletedTX
from mmgen.base_proto.bitcoin.tx.base import DeserializeTX
from mmgen.rpc import rpc_init
from mmgen.daemon import CoinDaemon

def print_info(name,extra_desc):
	if opt.names:
		Msg_r('{} {} {}'.format(
			purple('Testing'),
			cyan(f'{name} ({extra_desc})'),
			'' if opt.quiet else '\n'))
	else:
		Msg_r(f'Testing {extra_desc} transactions')
		if not opt.quiet:
			Msg('')

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
		Msg('\n\n================================ Core vector: ==================================')
	Msg_r('.' if opt.quiet else f'{n:>3}) {desc}\n')
	if opt.verbose:
		Pmsg(d)
		Msg('\n------------------------------ MMGen deserialized: -----------------------------')
		Pmsg(dt._asdict())

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

async def do_mmgen_ref(daemons,fns,name,desc):
	start_test_daemons(*daemons)
	print_info(name,desc)
	for n,fn in enumerate(fns):
		tx = await CompletedTX(filename=fn,quiet_open=True)
		await test_tx(
			tx_proto = tx.proto,
			tx_hex   = tx.serialized,
			desc     = fn,
			n        = n+1 )
	stop_test_daemons(*daemons)
	Msg('OK')
	return True

class unit_tests:

	altcoin_deps = ('mmgen_ref_alt',)

	async def core_vectors(self,name,ut):

		core_repo_root = os.getenv('CORE_REPO_ROOT')
		if not core_repo_root:
			die(1,'The environmental variable CORE_REPO_ROOT must be set before running this test')

		start_test_daemons('btc')

		fn_b = 'src/test/data/tx_valid.json'
		fn = os.path.join(core_repo_root,fn_b)
		with open(fn) as fp:
			core_data = json.loads(fp.read())
		print_info(name,'Bitcoin Core test vectors')
		n = 1
		for e in core_data:
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
		stop_test_daemons('btc')
		return True

	async def mmgen_ref(self,name,ut):
		return await do_mmgen_ref(
			('btc','btc_tn'),
			(
				'test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx',
				'test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx',
				'test/ref/542169[5.68152,34].sigtx',
			),
			name,
			'MMGen reference transactions [Bitcoin]' )

	async def mmgen_ref_alt(self,name,ut):
		return await do_mmgen_ref(
			('ltc','ltc_tn','bch'),
			(
				'test/ref/litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx',
				'test/ref/litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx',
				'test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx'
			),
			name,
			'MMGen reference transactions [Altcoin]' )
