#!/usr/bin/env python3

import sys, os
pn = os.path.abspath(os.path.dirname(sys.argv[0]))
os.chdir(os.path.dirname(os.path.dirname(pn)))
sys.path[0] = os.curdir

from mmgen.cfg import Config, gc
from mmgen.util import msg

opts_data = {
	'text': {
		'desc':    '',
		'usage':   'crypto | seed',
		'options': """
-h, --help            Print this help message
-P, --passwd-file=f   a
-p, --hash-preset=p   b
-r, --usr-randchars=n c
-L, --label=l         d
-m, --keep-label      e
		"""
	}
}

cfg = Config(opts_data=opts_data, init_opts={'color': True})

def crypto():
	desc = 'test data'

	from mmgen.crypto import Crypto
	crypto = Crypto(cfg)

	pw = crypto.get_new_passphrase(data_desc=desc, hash_preset=gc.dfl_hash_preset, passwd_file=None)
	msg(f'==> got new passphrase: [{pw}]\n')

	pw = crypto.get_passphrase(data_desc=desc, passwd_file=None)
	msg(f'==> got passphrase: [{pw}]\n')

	hp = crypto.get_hash_preset_from_user(data_desc=desc)
	msg(f'==> got hash preset: [{hp}]')

	hp = crypto.get_hash_preset_from_user(data_desc=desc)
	msg(f'==> got hash preset: [{hp}]')

def seed():

	from mmgen.wallet import Wallet

	for n in range(1, 3):
		msg(f'------- NEW WALLET {n} -------\n')
		w1 = Wallet(cfg)
		msg(f'\n==> got pw, preset, lbl: [{w1.ssdata.passwd}][{w1.ssdata.hash_preset}][{w1.ssdata.label}]\n')

	for n in range(1, 3):
		msg(f'------- PASSCHG {n} -------\n')
		w2 = Wallet(cfg, ss=w1, passchg=True)
		msg(f'\n==> got pw, preset, lbl: [{w2.ssdata.passwd}][{w2.ssdata.hash_preset}][{w2.ssdata.label}]\n')

	msg('------- WALLET FROM FILE -------\n')
	w3 = Wallet(cfg, fn='test/ref/FE3C6545-D782B529[128,1].mmdat') # passphrase: 'reference password'
	msg(f'\n==> got pw, preset, lbl: [{w3.ssdata.passwd}][{w3.ssdata.hash_preset}][{w3.ssdata.label}]\n')

globals()[cfg._args[0]]()
