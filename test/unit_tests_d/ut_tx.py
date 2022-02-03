#!/usr/bin/env python3
"""
test.unit_tests_d.ut_tx: TX unit test for the MMGen suite
"""

import re
from mmgen.common import *
from mmgen.tx import NewTX,UnsignedTX
from mmgen.txfile import MMGenTxFile
from mmgen.rpc import rpc_init
from mmgen.daemon import CoinDaemon
from mmgen.protocol import init_proto

class unit_tests:

	def tx(self,name,ut):
		qmsg('  Testing transaction objects')
		d = CoinDaemon('btc',test_suite=True)
		d.start()

		async def do():
			proto = init_proto('btc',need_amt=True)
			tx = await NewTX(proto=proto)
			tx.rpc = await rpc_init(proto=proto)

		run_session(do())

		d.stop()
		qmsg('  OK')
		return True

	def txfile(self,name,ut):
		qmsg('  Testing TX file operations')

		fns = ( # TODO: add altcoin TX files
			'0B8D5A[15.31789,14,tl=1320969600].rawtx',
			'0C7115[15.86255,14,tl=1320969600].testnet.rawtx',
			'460D4D-BCH[10.19764,tl=1320969600].rawtx',
			'25EFA3[2.34].testnet.rawtx',
		)
		for fn in fns:
			vmsg(f'    parsing: {fn}')
			fpath = os.path.join('test','ref',fn)
			tx = UnsignedTX(filename=fpath,quiet_open=True)
			f = MMGenTxFile(tx)

			fn_gen = f.make_filename()
			if g.debug_utf8:
				fn_gen = fn_gen.replace('-α','')
			assert fn_gen == fn, f'{fn_gen} != {fn}'

			text = f.format()
			# New in version 3.3: Support for the unicode legacy literal (u'value') was
			# reintroduced to simplify the maintenance of dual Python 2.x and 3.x codebases.
			# See PEP 414 for more information.
			with open(fpath) as fp:
				# remove Python2 'u' string prefixes from ref files
				chk = re.subn( r"\bu(['\"])", r'\1', fp.read() )[0]
			diff = get_ndiff(chk,text)
			#print('\n'.join(diff))
			nLines = len([i for i in diff if i.startswith('-')])
			assert nLines in (0,1), f'{nLines} lines differ: only checksum line may differ'
			#break # FIXME - test BCH, testnet

		qmsg('  OK')
		return True
