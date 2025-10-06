#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
wallet.incog_base: incognito wallet base class
"""

from ..seed import Seed
from ..util import msg, make_chksum_8, die
from .enc import wallet

class wallet(wallet):

	_msg = {
		'check_incog_id': """
  Check the generated Incog ID above against your records.  If it doesn't
  match, then your incognito data is incorrect or corrupted.
	""",
		'record_incog_id': """
  Make a record of the Incog ID but keep it secret.  You will use it to
  identify your incog wallet data in the future.
	""",
		'decrypt_params': " {} hash preset"}

	def _make_iv_chksum(self, s):
		from hashlib import sha256
		return sha256(s).hexdigest()[:8].upper()

	def _get_incog_data_len(self, seed_len):
		return (
			self.crypto.aesctr_iv_len
			+ self.crypto.salt_len
			+ (0 if self.cfg.old_incog_fmt else self.crypto.hincog_chk_len)
			+ seed_len//8)

	def _incog_data_size_chk(self):
		# valid sizes: 56, 64, 72
		dlen = len(self.fmt_data)
		seed_len = self.cfg.seed_len or Seed.dfl_len
		valid_dlen = self._get_incog_data_len(seed_len)
		if dlen == valid_dlen:
			return True
		else:
			if self.cfg.old_incog_fmt:
				msg('WARNING: old-style incognito format requested.  Are you sure this is correct?')
			msg(f'Invalid incognito data size ({dlen} bytes) for this seed length ({seed_len} bits)')
			msg(f'Valid data size for this seed length: {valid_dlen} bytes')
			for sl in Seed.lens:
				if dlen == self._get_incog_data_len(sl):
					die(1, f'Valid seed length for this data size: {sl} bits')
			msg(f'This data size ({dlen} bytes) is invalid for all available seed lengths')
			return False

	def _encrypt (self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		if self.cfg.old_incog_fmt:
			die(1, 'Writing old-format incognito wallets is unsupported')
		d = self.ssdata
		crypto = self.crypto

		d.iv = crypto.get_random(crypto.aesctr_iv_len)
		d.iv_id = self._make_iv_chksum(d.iv)
		msg(f'New Incog Wallet ID: {d.iv_id}')
		self.cfg._util.qmsg('Make a record of this value')
		self.cfg._util.vmsg('\n  ' + self.msg['record_incog_id'].strip()+'\n')

		d.salt = crypto.get_random(crypto.salt_len)
		seed_key = crypto.make_key(
			passwd      = d.passwd,
			salt        = d.salt,
			hash_preset = d.hash_preset,
			desc        = 'incog wallet key')

		from hashlib import sha256
		chk = sha256(self.seed.data).digest()[:8]
		d.enc_seed = crypto.encrypt_seed(
			data = chk + self.seed.data,
			key  = seed_key)

		# IV is used BOTH to initialize counter and to salt password!
		d.wrapper_key = crypto.make_key(
			passwd      = d.passwd,
			salt        = d.iv,
			hash_preset = d.hash_preset,
			desc        = 'incog wrapper key')

		d.key_id = make_chksum_8(d.wrapper_key)
		self.cfg._util.vmsg(f'Key ID: {d.key_id}')

		d.target_data_len = self._get_incog_data_len(self.seed.bitlen)

	def _format(self):
		d = self.ssdata
		self.fmt_data = d.iv + self.crypto.encrypt_data(
			data = d.salt + d.enc_seed,
			key  = d.wrapper_key,
			iv   = d.iv,
			desc = self.desc)

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return '{}-{}-{}[{},{}].{}'.format(
			s.fn_stem,
			d.key_id,
			d.iv_id,
			s.bitlen,
			d.hash_preset,
			self.ext)

	def _deformat(self):

		if not self._incog_data_size_chk():
			return False

		d = self.ssdata
		d.iv             = self.fmt_data[0:self.crypto.aesctr_iv_len]
		d.incog_id       = self._make_iv_chksum(d.iv)
		d.enc_incog_data = self.fmt_data[self.crypto.aesctr_iv_len:]
		msg(f'Incog Wallet ID: {d.incog_id}')
		self.cfg._util.qmsg('Check this value against your records')
		self.cfg._util.vmsg('\n  ' + self.msg['check_incog_id'].strip()+'\n')

		return True

	def _verify_seed_newfmt(self, data):
		chk, seed = data[:8], data[8:]
		from hashlib import sha256
		if sha256(seed).digest()[:8] == chk:
			self.cfg._util.qmsg('Passphrase{} are correct'.format(self.msg['decrypt_params'].format('and')))
			return seed
		else:
			msg('Incorrect passphrase{}'.format(self.msg['decrypt_params'].format('or')))
			return False

	def _verify_seed_oldfmt(self, seed):
		prompt = f'Seed ID: {make_chksum_8(seed)}.  Is the Seed ID correct?'
		from ..ui import keypress_confirm
		if keypress_confirm(self.cfg, prompt, default_yes=True):
			return seed
		else:
			return False

	def _decrypt(self):
		d = self.ssdata
		self._get_hash_preset(add_desc=d.incog_id)
		d.passwd = self._get_passphrase(add_desc=d.incog_id)
		crypto = self.crypto

		# IV is used BOTH to initialize counter and to salt password!
		wrapper_key = crypto.make_key(
			passwd      = d.passwd,
			salt        = d.iv,
			hash_preset = d.hash_preset,
			desc        = 'wrapper key')

		dd = crypto.decrypt_data(
			enc_data = d.enc_incog_data,
			key      = wrapper_key,
			iv       = d.iv,
			desc     = 'incog data')

		d.salt     = dd[0:crypto.salt_len]
		d.enc_seed = dd[crypto.salt_len:]

		seed_key = crypto.make_key(
			passwd      = d.passwd,
			salt        = d.salt,
			hash_preset = d.hash_preset,
			desc        = 'main key')

		self.cfg._util.qmsg(f'Key ID: {make_chksum_8(seed_key)}')

		verify_seed_func = getattr(self, '_verify_seed_'+ ('oldfmt' if self.cfg.old_incog_fmt else 'newfmt'))

		seed = verify_seed_func(
			crypto.decrypt_seed(
				enc_seed = d.enc_seed,
				key      = seed_key,
				seed_id  = '',
				key_id   = ''))

		if seed:
			self.seed = Seed(self.cfg, seed_bin=seed)
			msg(f'Seed ID: {self.seed.sid}')
			return True
		else:
			return False
