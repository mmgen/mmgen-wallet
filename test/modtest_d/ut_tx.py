#!/usr/bin/env python3

"""
test.modtest_d.ut_tx: TX unit tests for the MMGen suite
"""

import os, re

from mmgen.devtools import get_diff, get_ndiff
from mmgen.tx import CompletedTX, UnsignedTX
from mmgen.tx.file import MMGenTxFile
from mmgen.protocol import init_proto
from mmgen.cfg import Config

from ..include.common import cfg, qmsg, vmsg

async def do_txfile_test(desc, fns, cfg=cfg, check=False):
	qmsg(f'  Testing CompletedTX initializer ({desc})')
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
			text = f.format()
			with open(fpath) as fh:
				text_chk = fh.read()
			assert text == text_chk, f'\nformatted text:\n{text}\n  !=\noriginal file:\n{text_chk}'

	qmsg('  OK')
	return True

class unit_tests:

	altcoin_deps = ('txfile_alt', 'txfile_alt_legacy')

	async def txfile(self, name, ut):
		return await do_txfile_test(
			'Bitcoin',
			(
				'tx/7A8157[6.65227,34].rawtx',
				'tx/BB3FD2[7.57134314,123].sigtx',
				'tx/0A869F[1.23456,32].regtest.asubtx',
			),
			check = True
		)

	async def txfile_alt(self, name, ut):
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

	async def txfile_legacy(self, name, ut):
		return await do_txfile_test(
			'Bitcoin - legacy file format',
			(
				'0B8D5A[15.31789,14,tl=1320969600].rawtx',
				'542169[5.68152,34].sigtx',
				'0C7115[15.86255,14,tl=1320969600].testnet.rawtx',
				'25EFA3[2.34].testnet.rawtx',
			)
		)

	async def txfile_alt_legacy(self, name, ut):
		return await do_txfile_test(
			'altcoins - legacy file format',
			(
				'460D4D-BCH[10.19764,tl=1320969600].rawtx',
				'ethereum/5881D2-MM1[1.23456,50000].rawtx',
				'ethereum/6BDB25-MM1[1.23456,50000].testnet.rawtx',
				'ethereum/88FEFD-ETH[23.45495,40000].rawtx',
				'ethereum/B472BD-ETH[23.45495,40000].testnet.rawtx',
				'ethereum/B472BD-ETH[23.45495,40000].testnet.sigtx',
				'litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx',
				'litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx',
			)
		)

	def errors(self, name, ut):
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
