#!/usr/bin/env python
from distutils.core import setup

setup(
		name         = 'mmgen',
		version      = '0.6',
		author       = 'Philemon',
		author_email = 'mmgen-py@yandex.com',
		url          = 'http://www.python.org/sigs/distutils-sig/',
		py_modules = [
			'mmgen.addr',
			'mmgen.bitcoin',
			'mmgen.config',
			'mmgen.license',
			'mmgen.__init__',
			'mmgen.mn_electrum',
			'mmgen.mnemonic',
			'mmgen.mn_tirosh',
			'mmgen.Opts',
			'mmgen.utils',
			'mmgen.walletgen'
		],
		data_files=[('/usr/local/bin', [
			'mmgen-addrgen',
			'mmgen-keygen',
			'mmgen-passchg',
			'mmgen-walletchk',
			'mmgen-walletgen'
		])]
	)
