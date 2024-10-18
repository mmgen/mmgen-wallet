#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
wallet.mmgen: MMGen native wallet class
"""

import os

from ..seed import Seed
from ..util import msg, make_timestamp, make_chksum_6, split_into_cols, is_chksum_6
from ..obj import MMGenWalletLabel, get_obj
from ..baseconv import baseconv

from .enc import wallet

class wallet(wallet):

	desc = 'MMGen wallet'

	def __init__(self, *args, **kwargs):
		if self.cfg.label:
			self.label = MMGenWalletLabel(self.cfg.label)
		else:
			self.label = None
		super().__init__(*args, **kwargs)

	# logic identical to _get_hash_preset_from_user()
	def _get_label_from_user(self, old_lbl=''):
		prompt = 'Enter a wallet label, or hit ENTER {}: '.format(
			'to reuse the label {}'.format(old_lbl.hl2(encl='‘’')) if old_lbl else
			'for no label')
		from ..ui import line_input
		while True:
			ret = line_input(self.cfg, prompt)
			if ret:
				lbl = get_obj(MMGenWalletLabel, s=ret)
				if lbl:
					return lbl
				else:
					msg('Invalid label.  Trying again...')
			else:
				return old_lbl or MMGenWalletLabel('No Label')

	# logic identical to _get_hash_preset()
	def _get_label(self):
		if hasattr(self, 'ss_in') and hasattr(self.ss_in.ssdata, 'label'):
			old_lbl = self.ss_in.ssdata.label
			if self.cfg.keep_label:
				lbl = old_lbl
				self.cfg._util.qmsg('Reusing label {} at user request'.format(lbl.hl2(encl='‘’')))
			elif self.label:
				lbl = self.label
				self.cfg._util.qmsg('Using user-configured label {}'.format(lbl.hl2(encl='‘’')))
			else: # Prompt, using old value as default
				lbl = self._get_label_from_user(old_lbl)
			if (not self.cfg.keep_label) and self.op == 'pwchg_new':
				self.cfg._util.qmsg('Label {}'.format('unchanged' if lbl == old_lbl else f'changed to {lbl!r}'))
		elif self.label:
			lbl = self.label
			self.cfg._util.qmsg('Using user-configured label {}'.format(lbl.hl2(encl='‘’')))
		else:
			lbl = self._get_label_from_user()
		self.ssdata.label = lbl

	def _encrypt(self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		self._get_label()
		d = self.ssdata
		d.pw_status = ('NE', 'E')[len(d.passwd)==0]
		d.timestamp = make_timestamp()

	def _format(self):
		d = self.ssdata
		s = self.seed
		bc = baseconv('b58')
		slt_fmt  = bc.frombytes(d.salt, pad='seed', tostr=True)
		es_fmt = bc.frombytes(d.enc_seed, pad='seed', tostr=True)
		lines = (
			d.label,
			'{} {} {} {} {}'.format(s.sid.lower(), d.key_id.lower(), s.bitlen, d.pw_status, d.timestamp),
			'{}: {} {} {}'.format(d.hash_preset, *self.crypto.get_hash_params(d.hash_preset)),
			'{} {}'.format(make_chksum_6(slt_fmt), split_into_cols(4, slt_fmt)),
			'{} {}'.format(make_chksum_6(es_fmt),  split_into_cols(4, es_fmt))
		)
		chksum = make_chksum_6(' '.join(lines).encode())
		self.fmt_data = '\n'.join((chksum,)+lines) + '\n'

	def _deformat(self):

		def check_master_chksum(lines, desc):

			if len(lines) != 6:
				msg(f'Invalid number of lines ({len(lines)}) in {desc} data')
				return False

			if not is_chksum_6(lines[0]):
				msg(f'Incorrect master checksum ({lines[0]}) in {desc} data')
				return False

			chk = make_chksum_6(' '.join(lines[1:]))
			if not self.cfg._util.compare_chksums(lines[0], 'master', chk, 'computed',
						hdr='For wallet master checksum', verbose=True):
				return False

			return True

		lines = self.fmt_data.splitlines()
		if not check_master_chksum(lines, self.desc):
			return False

		d = self.ssdata
		d.label = MMGenWalletLabel(lines[1])

		d1, d2, d3, d4, d5 = lines[2].split()
		d.seed_id = d1.upper()
		d.key_id  = d2.upper()
		self.check_usr_seed_len(int(d3))
		d.pw_status, d.timestamp = d4, d5

		hpdata = lines[3].split()

		d.hash_preset = hp = hpdata[0][:-1]  # a string!
		self.cfg._util.qmsg(f'Hash preset of wallet: {hp!r}')
		if self.cfg.hash_preset and self.cfg.hash_preset != hp:
			self.cfg._util.qmsg(f'Warning: ignoring user-requested hash preset {self.cfg.hash_preset!r}')

		hash_params = tuple(map(int, hpdata[1:]))

		if hash_params != self.crypto.get_hash_params(d.hash_preset):
			msg(f'Hash parameters {" ".join(hash_params)!r} don’t match hash preset {d.hash_preset!r}')
			return False

		lmin, _, lmax = sorted(baseconv('b58').seedlen_map_rev) # 22, 33, 44
		for i, key in (4, 'salt'), (5, 'enc_seed'):
			l = lines[i].split(' ')
			chk = l.pop(0)
			b58_val = ''.join(l)

			if len(b58_val) < lmin or len(b58_val) > lmax:
				msg(f'Invalid format for {key} in {self.desc}: {l}')
				return False

			if not self.cfg._util.compare_chksums(
					chk,
					key,
					make_chksum_6(b58_val),
					'computed checksum',
					verbose = True):
				return False

			val = baseconv('b58').tobytes(b58_val, pad='seed')
			if val is False:
				msg(f'Invalid base 58 number: {b58_val}')
				return False

			setattr(d, key, val)

		return True

	def _decrypt(self):
		d = self.ssdata
		# Needed for multiple transactions with {}-txsign
		d.passwd = self._get_passphrase(
			add_desc = os.path.basename(self.infile.name) if self.cfg.quiet else '')
		key = self.crypto.make_key(d.passwd, d.salt, d.hash_preset)
		ret = self.crypto.decrypt_seed(d.enc_seed, key, d.seed_id, d.key_id)
		if ret:
			self.seed = Seed(self.cfg, ret)
			return True
		else:
			return False

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return '{}-{}[{},{}].{}'.format(
			s.fn_stem,
			d.key_id,
			s.bitlen,
			d.hash_preset,
			self.ext)
