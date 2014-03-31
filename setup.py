#!/usr/bin/env python
from distutils.core import setup

setup(
		name         = 'mmgen',
		version      = '0.6.9',
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
			'mmgen.tx',
			'mmgen.utils',
			'mmgen.walletgen',

			'mmgen.rpc.__init__',
			'mmgen.rpc.config',
			'mmgen.rpc.connection',
			'mmgen.rpc.data',
			'mmgen.rpc.exceptions',
			'mmgen.rpc.proxy',
			'mmgen.rpc.util',

			'tests.__init__',
			'tests.addr',
			'tests.bitcoin',
			'tests.mn_electrum',
			'tests.mnemonic',
			'tests.mn_tirosh',
			'tests.test',
			'tests.utils',
			'tests.walletgen'
		],
		scripts=[
			'mmgen-addrgen',
			'mmgen-addrimport',
			'mmgen-passchg',
			'mmgen-walletchk',
			'mmgen-walletgen',
			'mmgen-txcreate',
			'mmgen-txsign',
			'mmgen-txsend',
			'mmgen-pywallet'
		]
	)
