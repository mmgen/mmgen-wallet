#!/usr/bin/env python
from distutils.core import setup

setup(
		name         = 'mmgen',
		version      = '0.7.7',
		author       = 'Philemon',
		author_email = 'mmgen-py@yandex.com',
		url          = 'https://github.com/mmgen/mmgen',
		py_modules = [
			'__init__',

			'mmgen.__init__',
			'mmgen.addr',
			'mmgen.bitcoin',
			'mmgen.config',
			'mmgen.license',
			'mmgen.mn_electrum',
			'mmgen.mnemonic',
			'mmgen.mn_tirosh',
			'mmgen.Opts',
			'mmgen.term',
			'mmgen.tool',
			'mmgen.tx',
			'mmgen.util',
			'mmgen.walletgen',

			'mmgen.rpc.__init__',
			'mmgen.rpc.config',
			'mmgen.rpc.connection',
			'mmgen.rpc.data',
			'mmgen.rpc.exceptions',
			'mmgen.rpc.proxy',
			'mmgen.rpc.util',

			'mmgen.tests.__init__',
			'mmgen.tests.addr',
			'mmgen.tests.bitcoin',
			'mmgen.tests.mn_electrum',
			'mmgen.tests.mnemonic',
			'mmgen.tests.mn_tirosh',
			'mmgen.tests.test',
			'mmgen.tests.util',
			'mmgen.tests.walletgen'
		],
		scripts=[
			'mmgen-addrgen',
			'mmgen-keygen',
			'mmgen-addrimport',
			'mmgen-passchg',
			'mmgen-walletchk',
			'mmgen-walletgen',
			'mmgen-txcreate',
			'mmgen-txsign',
			'mmgen-txsend',
			'mmgen-pywallet',
			'mmgen-tool',
		]
	)
