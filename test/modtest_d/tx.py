#!/usr/bin/env python3

"""
test.modtest_d.tx: TX unit tests for the MMGen suite
"""

import os

from mmgen.tx import CompletedTX, UnsignedTX
from mmgen.tx.file import MMGenTxFile
from mmgen.cfg import Config

from ..include.common import cfg, qmsg, vmsg, gr_uc

async def do_txfile_test(desc, fns, cfg=cfg, check=False):
	qmsg(f'\n  Testing CompletedTX initializer ({desc})')
	for fn in fns:
		qmsg(f'     parsing: {os.path.basename(fn)}')
		fpath = os.path.join('test', 'ref', fn)
		tx = await CompletedTX(cfg=cfg, filename=fpath, quiet_open=True)

		vmsg('\n' + tx.info.format())

		f = MMGenTxFile(tx)
		fn_gen = f.make_filename()

		if cfg.debug_utf8:
			fn_gen = fn_gen.replace('-α', '')

		assert fn_gen == os.path.basename(fn), f'{fn_gen} != {fn}'

		if check:
			import json
			from mmgen.tx.file import json_dumps
			from mmgen.util import make_chksum_6
			text = f.format()
			with open(fpath) as fh:
				text_chk = fh.read()
			data_chk = json.loads(text_chk)
			outputs = data_chk['MMGenTransaction']['outputs']
			for n, o in enumerate(outputs):
				outputs[n] = {k:v for k,v in o.items() if not (type(v) is bool and v is False)}
			data_chk['chksum'] = make_chksum_6(json_dumps(data_chk['MMGenTransaction']))
			text_chk_fixed = json_dumps(data_chk)
			assert text == text_chk_fixed, f'\nformatted text:\n{text}\n  !=\noriginal file:\n{text_chk_fixed}'

	qmsg('  OK')
	return True

class unit_tests:

	altcoin_deps = ('txfile_alt', 'txfile_alt_legacy')

	async def txfile(self, name, ut, desc='displaying transaction files (BTC)'):
		return await do_txfile_test(
			'Bitcoin',
			(
				'tx/7A8157[6.65227,34].rawtx',
				'tx/B498CE[5.55788,38].rawtx',
				'tx/BB3FD2[7.57134314,123].sigtx',
				'tx/0A869F[1.23456,32].regtest.asubtx',
			),
			check = True
		)

	async def txfile_alt(self, name, ut, desc='displaying transaction files (LTC, BCH, ETH)'):
		return await do_txfile_test(
			'altcoins',
			(
				'tx/C09D73-LTC[981.73747,2000].testnet.rawtx',
				'tx/91060A-BCH[1.23456].regtest.arawtx',
				'tx/D850C6-MM1[43.21,50000].subtx', # token tx
			),
			# token resolved by tracking wallet under data_dir:
			cfg = Config({'data_dir': 'test/ref/data_dir'}),
			check = True
		)

	async def txfile_legacy(self, name, ut, desc='displaying transaction files (legacy format, BTC)'):
		return await do_txfile_test(
			'Bitcoin - legacy file format',
			(
				'0B8D5A[15.31789,14,tl=1320969600].rawtx',
				'542169[5.68152,34].sigtx',
				'0C7115[15.86255,14,tl=1320969600].testnet.rawtx',
				'25EFA3[2.34].testnet.rawtx',
			)
		)

	async def txfile_alt_legacy(self, name, ut, desc='displaying transaction files (legacy format, LTC, BCH, ETH)'):
		return await do_txfile_test(
			'altcoins - legacy file format',
			(
				'460D4D-BCH[10.19764,tl=1320969600].rawtx',
				'ethereum/5881D2-MM1[1.23456,50000].rawtx',
				'ethereum/6BDB25-MM1[1.23456,50000].testnet.rawtx',
				'ethereum/88FEFD-ETH[23.45495,40000].rawtx',
				'litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx',
				'litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx',
			)
		)

	def errors(self, name, ut, desc='reading transaction files (error handling)'):
		async def bad1():
			await CompletedTX(cfg, filename='foo')
		def bad2():
			UnsignedTX(cfg, filename='foo')
		bad_data = (
			('forbidden positional args', 'TypeError', 'positional arguments', bad1),
			('forbidden positional args', 'TypeError', 'positional arguments', bad2),
		)
		ut.process_bad_data(bad_data)
		return True

	def op_return_data(self, name, ut, desc='OpReturnData class'):
		max_len = cfg._proto.max_op_return_data_len
		from mmgen.proto.btc.tx.op_return_data import OpReturnData
		vecs = [
			'data:=:ETH.ETH:0x86d526d6624AbC0178cF7296cD538Ecc080A95F1:0/1/0',
			'hexdata:3d3a4554482e4554483a30783836643532366436363234416243303137'
				'38634637323936634435333845636330383041393546313a302f312f30',
			'hexdata:00010203040506',
			'hexdata:' + 'ee' * max_len,
			'data:' + 'z' * max_len,
			'data:a',
			'data:a\n',
			'data:a\tb',
			'data:' + gr_uc[:24],
		]

		assert OpReturnData(cfg._proto, vecs[0]) == OpReturnData(cfg._proto, vecs[1])

		for vec in vecs:
			d = OpReturnData(cfg._proto, vec)
			assert d == OpReturnData(cfg._proto, repr(d)) # repr() must return a valid initializer
			assert isinstance(d, bytes)
			assert isinstance(str(d), str)
			vmsg('-' * 80)
			vmsg(vec)
			vmsg(repr(d))
			vmsg(d.hl())
			vmsg(d.hl(add_label=True))
			vmsg(f'length: {len(str(d))}')

		bad_data = [
			'data:',
			'hexdata:',
			'data:' + 'x' * (max_len + 1),
			'hexdata:' + ('deadbeef' * (max_len // 4)) + 'ee',
			'hex:0abc',
			'da:xyz',
			'hexdata:xyz',
			'hexdata:abcde',
			b'data:abc',
			'hexdata:' + 'dd' * (max_len + 1),
		]

		def bad(n):
			return lambda: OpReturnData(cfg._proto, bad_data[n])

		vmsg('-' * 80)
		vmsg('Testing error handling:')

		ut.process_bad_data((
			('bad1',    'AssertionError', 'not in range', bad(0)),
			('bad2',    'AssertionError', 'not in range', bad(1)),
			('bad3',    'AssertionError', 'not in range', bad(2)),
			('bad4',    'AssertionError', 'not in range', bad(3)),
			('bad5',    'ValueError',     'must start',   bad(4)),
			('bad6',    'ValueError',     'must start',   bad(5)),
			('bad7',    'AssertionError', 'not in hex',   bad(6)),
			('bad8',    'AssertionError', 'even',         bad(7)),
			('bad9',    'AssertionError', 'a string',     bad(8)),
			('bad10',   'AssertionError', 'not in range', bad(9)),
		), pfx='')

		return True
