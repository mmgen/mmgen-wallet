#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
wallet.enc: encrypted wallet base class
"""

from ..globalvars import g
from ..opts import opt
from ..util import msg,qmsg,make_chksum_8
from .base import wallet

class wallet(wallet):

	def __init__(self,*args,**kwargs):
		from mmgen.crypto import Crypto
		self.crypto = Crypto()
		return super().__init__(*args,**kwargs)

	def _decrypt_retry(self):
		while True:
			if self._decrypt():
				break
			if self.passwd_file:
				die(2,'Passphrase from password file, so exiting')
			msg('Trying again...')

	def _get_hash_preset_from_user(self,old_preset,add_desc=''):
		prompt = 'Enter {}hash preset for {}{}{},\nor hit ENTER to {} value ({!r}): '.format(
			('old ' if self.op=='pwchg_old' else 'new ' if self.op=='pwchg_new' else ''),
			('','new ')[self.op=='new'],
			self.desc,
			('',' '+add_desc)[bool(add_desc)],
			('accept the default','reuse the old')[self.op=='pwchg_new'],
			old_preset )
		return self.crypto.get_hash_preset_from_user( old_preset=old_preset, prompt=prompt )

	def _get_hash_preset(self,add_desc=''):
		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'hash_preset'):
			old_hp = self.ss_in.ssdata.hash_preset
			if opt.keep_hash_preset:
				hp = old_hp
				qmsg(f'Reusing hash preset {hp!r} at user request')
			elif opt.hash_preset:
				hp = opt.hash_preset
				qmsg(f'Using hash preset {hp!r} requested on command line')
			else: # Prompt, using old value as default
				hp = self._get_hash_preset_from_user(old_hp,add_desc)
			if (not opt.keep_hash_preset) and self.op == 'pwchg_new':
				qmsg('Hash preset {}'.format( 'unchanged' if hp == old_hp else f'changed to {hp!r}' ))
		elif opt.hash_preset:
			hp = opt.hash_preset
			qmsg(f'Using hash preset {hp!r} requested on command line')
		else:
			hp = self._get_hash_preset_from_user(
				old_preset = g.dfl_hash_preset,
				add_desc   = add_desc )
		self.ssdata.hash_preset = hp

	def _get_new_passphrase(self):
		return self.crypto.get_new_passphrase(
			data_desc = ('new ' if self.op in ('new','conv') else '') + self.desc,
			hash_preset = self.ssdata.hash_preset,
			passwd_file = self.passwd_file,
			pw_desc = ('new ' if self.op=='pwchg_new' else '') + 'passphrase' )

	def _get_passphrase(self,add_desc=''):
		return self.crypto.get_passphrase(
			data_desc = self.desc + (f' {add_desc}' if add_desc else ''),
			passwd_file = self.passwd_file,
			pw_desc = ('old ' if self.op == 'pwchg_old' else '') + 'passphrase' )

	def _get_first_pw_and_hp_and_encrypt_seed(self):
		d = self.ssdata
		self._get_hash_preset()

		if hasattr(self,'ss_in') and hasattr(self.ss_in.ssdata,'passwd'):
			old_pw = self.ss_in.ssdata.passwd
			if opt.keep_passphrase:
				d.passwd = old_pw
				qmsg('Reusing passphrase at user request')
			else:
				d.passwd = self._get_new_passphrase()
				if self.op == 'pwchg_new':
					qmsg('Passphrase {}'.format( 'unchanged' if d.passwd == old_pw else 'changed' ))
		else:
			d.passwd = self._get_new_passphrase()

		from hashlib import sha256
		d.salt     = sha256( self.crypto.get_random(128) ).digest()[:self.crypto.salt_len]
		key        = self.crypto.make_key( d.passwd, d.salt, d.hash_preset )
		d.key_id   = make_chksum_8(key)
		d.enc_seed = self.crypto.encrypt_seed( self.seed.data, key )
