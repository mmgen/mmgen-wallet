#!/usr/bin/env python3

"""
test.daemontest_d.tx: TX daemon tests for the MMGen suite
"""

import json

from mmgen.color import purple, cyan
from mmgen.util import Msg, Msg_r
from mmgen.devtools import Pmsg
from mmgen.protocol import init_proto
from mmgen.tx import CompletedTX
from mmgen.proto.btc.tx.base import DeserializeTX
from mmgen.rpc import rpc_init
from mmgen.daemon import CoinDaemon
from mmgen.tx import NewTX

from ..include.common import cfg, start_test_daemons, stop_test_daemons, qmsg

def print_info(name, extra_desc):
	if cfg.names:
		Msg_r('{} {} {}'.format(
			purple('Testing'),
			cyan(f'{name} ({extra_desc})'),
			'' if cfg.quiet else '\n'))
	else:
		Msg_r(f'Testing {extra_desc}')
		if not cfg.quiet:
			Msg('')

async def test_tx(tx_proto, tx_hex, desc, n):

	def has_nonstandard_outputs(outputs):
		for o in outputs:
			t = o['scriptPubKey']['type']
			if t in ('nonstandard', 'pubkey'):
				return True
		return False

	rpc = await rpc_init(cfg, proto=tx_proto, ignore_wallet=True)
	d = await rpc.call('decoderawtransaction', tx_hex)

	if has_nonstandard_outputs(d['vout']):
		return False

	dt = DeserializeTX(tx_proto, tx_hex)

	if cfg.verbose:
		Msg('\n\n=============================== Bitcoin Core: ==================================')
	Msg_r('.' if cfg.quiet else f'{n:>3}) {desc}\n')
	if cfg.verbose:
		Pmsg(d)
		Msg('\n------------------------------ MMGen deserialized: -----------------------------')
		Pmsg(dt._asdict())

	# metadata
	assert dt.txid == d['txid'], 'TXID does not match'
	assert dt.locktime == d['locktime'], 'Locktime does not match'
	assert dt.version == d['version'], 'Version does not match'

	# inputs
	a, b = d['vin'], dt.txins
	for i in range(len(a)):
		assert a[i]['txid'] == b[i]['txid'], f'TxID of input {i} does not match'
		assert a[i]['vout'] == b[i]['vout'], f'vout of input {i} does not match'
		assert a[i]['sequence'] == int(b[i]['nSeq'], 16), (
			f'nSeq of input {i} does not match')
		if 'txinwitness' in a[i]:
			assert a[i]['txinwitness'] == b[i]['witness'], (
				f'witness of input {i} does not match')

	# outputs
	a, b = d['vout'], dt.txouts
	for i in range(len(a)):
		if 'addresses' in a[i]['scriptPubKey']:
			A = a[i]['scriptPubKey']['addresses'][0]
			B = b[i]['addr']
			fs = 'address of output {} does not match\nA: {}\nB: {}'
			assert A == B, fs.format(i, A, B)

		A = tx_proto.coin_amt(a[i]['value'])
		B = b[i]['amt']
		fs = 'value of output {} does not match\nA: {}\nB: {}'
		assert A == B, fs.format(i, A, B)

		A = a[i]['scriptPubKey']['hex']
		B = b[i]['scriptPubKey']
		fs = 'scriptPubKey of output {} does not match\nA: {}\nB: {}'
		assert A == B, fs.format(i, A, B)

async def do_mmgen_ref(daemons, fns, name, desc):
	# NB: remove_datadir is required here for some reason (seems to be Bitcoin Core version-dependent)
	start_test_daemons(*daemons, remove_datadir=True)
	print_info(name, desc)
	for n, fn in enumerate(fns):
		tx = await CompletedTX(cfg=cfg, filename=fn, quiet_open=True)
		await test_tx(
			tx_proto = tx.proto,
			tx_hex   = tx.serialized,
			desc     = fn,
			n        = n + 1)
	stop_test_daemons(*daemons, remove_datadir=True)
	Msg('OK')
	return True

class unit_tests:

	altcoin_deps = ('mmgen_ref_alt',)

	async def newtx(self, name, ut):
		qmsg('  Testing NewTX initializer')
		d = CoinDaemon(cfg, network_id='btc', test_suite=True)
		d.start()

		proto = init_proto(cfg, 'btc', need_amt=True)
		NewTX(cfg=cfg, proto=proto, target='tx')

		d.stop()
		d.remove_datadir()
		qmsg('  OK')
		return True

	async def core_vectors(self, name, ut):

		start_test_daemons('btc')

		with open('test/ref/tx_valid.json') as fp:
			core_data = json.loads(fp.read())

		print_info(name, 'Bitcoin Core test vectors')

		n = 1
		desc = '(no description)'
		for e in core_data:
			if isinstance(e[0], list):
				await test_tx(
					tx_proto = init_proto(cfg, 'btc', need_amt=True),
					tx_hex   = e[1],
					desc     = desc,
					n        = n)
				n += 1
			else:
				desc = e[0]

		Msg('OK')
		stop_test_daemons('btc', remove_datadir=True)
		return True

	async def mmgen_ref(self, name, ut):
		return await do_mmgen_ref(
			('btc', 'btc_tn'),
			(
				'test/ref/tx/B498CE[5.55788,38].rawtx',
				'test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx',
				'test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx',
				'test/ref/542169[5.68152,34].sigtx',
			),
			name,
			'MMGen reference transactions [Bitcoin]')

	async def mmgen_ref_alt(self, name, ut):
		return await do_mmgen_ref(
			('ltc', 'ltc_tn', 'bch'),
			(
				'test/ref/litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx',
				'test/ref/litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx',
				'test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx'
			),
			name,
			'MMGen reference transactions [Altcoin]')
