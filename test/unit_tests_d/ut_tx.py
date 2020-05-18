#!/usr/bin/env python3
"""
test.unit_tests_d.ut_tx: TX unit test for the MMGen suite
"""

import re
from mmgen.common import *
from mmgen.tx import MMGenTX
from mmgen.txfile import MMGenTxFile

class unit_tests:

	def txfile(self,name,ut):

		qmsg('  Testing TX file operations')

		fns = ( # TODO: add altcoin TX files
			'0B8D5A[15.31789,14,tl=1320969600].rawtx',
			'0C7115[15.86255,14,tl=1320969600].testnet.rawtx',
			'460D4D-BCH[10.19764,tl=1320969600].rawtx',
			'25EFA3[2.34].testnet.rawtx',
		)
		for fn in fns:
			fpath = os.path.join('test','ref',fn)
			tx = MMGenTX(filename=fpath,quiet_open=True)
			f = MMGenTxFile(tx)

			fn_gen = f.make_filename()
			vmsg(f'    parsed: {fn_gen}')
			assert fn_gen == fn, f'{fn_gen} != {fn}'

			text = f.format()
			# New in version 3.3: Support for the unicode legacy literal (u'value') was
			# reintroduced to simplify the maintenance of dual Python 2.x and 3.x codebases.
			# See PEP 414 for more information.
			chk = re.subn(r"\bu'",r"'",open(fpath).read())[0] # remove Python2 'u' string prefixes from ref files
			nLines = len([i for i in get_ndiff(chk,text) if i.startswith('-')])
			assert nLines == 1, f'{nLines} lines differ: only checksum line should differ'
			break # FIXME - test BCH, testnet

		qmsg('  OK')
		return True
