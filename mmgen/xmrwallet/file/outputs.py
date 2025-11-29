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
xmrwallet.file.outputs: Monero wallet outputs file class for the MMGen Suite
"""

import re
from collections import namedtuple
from pathlib import Path

from ...util import die, suf
from ...tx.util import get_autosign_obj

from . import MoneroMMGenFile

class MoneroWalletOutputsFile:

	class Base(MoneroMMGenFile):

		desc = 'wallet outputs'
		data_label = 'MoneroMMGenWalletOutputsFile'
		base_chksum_fields = {'seed_id', 'wallet_index', 'outputs_data_hex'}
		full_chksum_fields = {'seed_id', 'wallet_index', 'outputs_data_hex', 'signed_key_images'}
		fn_fs = '{a}-outputs-{b}.{c}'
		ext_offset = 25 # len('-outputs-') + len(chksum) ({b})
		chksum_nchars = 16
		data_tuple = namedtuple('wallet_outputs_data', [
			'seed_id',
			'wallet_index',
			'outputs_data_hex',
			'signed_key_images',
			'sign',
			'imported'])

		def __init__(self, cfg):
			self.name = type(self).__name__
			self.cfg = cfg

		def write(self, *, add_suf='', quiet=False):
			from ...fileutil import write_data_to_file
			write_data_to_file(
				cfg               = self.cfg,
				outfile           = str(self.get_outfile(self.cfg, self.wallet_fn)) + add_suf,
				data              = self.make_wrapped_data(self.data._asdict()),
				desc              = self.desc,
				ask_overwrite     = False,
				quiet             = quiet,
				ignore_opt_outdir = True)

		def get_outfile(self, cfg, wallet_fn):
			return (
				get_autosign_obj(cfg).xmr_outputs_dir if cfg.autosign else
				wallet_fn.parent) / self.fn_fs.format(
					a = wallet_fn.name,
					b = self.base_chksum,
					c = self.ext)

		def get_wallet_fn(self, fn):
			assert fn.name.endswith(f'.{self.ext}'), (
				f'{self.name}: filename does not end with {"."+self.ext!r}')
			return fn.parent / fn.name[:-(len(self.ext)+self.ext_offset+1)]

		def get_info(self, *, indent=''):
			if self.data.signed_key_images is not None:
				data = self.data.signed_key_images or []
				return f'{indent}{self.wallet_fn.name}: {len(data)} signed key image{suf(data)}'
			else:
				return f'{indent}{self.wallet_fn.name}: no key images'

	class New(Base):
		ext = 'raw'

		def __init__(self, parent, wallet_fn, data, *, wallet_idx=None, sign=False):
			super().__init__(parent.cfg)
			self.wallet_fn = wallet_fn
			init_data = dict.fromkeys(self.data_tuple._fields)
			init_data.update({
				'seed_id':      parent.kal.al_id.sid,
				'wallet_index': wallet_idx or parent.get_idx_from_fn(wallet_fn)})
			if sign:
				init_data['sign'] = sign
			init_data.update({k: v for k, v in data.items() if k in init_data})
			self.data = self.data_tuple(**init_data)

	class Completed(New):

		def __init__(self, parent, *, fn=None, wallet_fn=None):
			def check_equal(desc, a, b):
				assert a == b, f'{desc} mismatch: {a} (from file) != {b} (from filename)'
			fn = fn or self.get_outfile(parent.cfg, wallet_fn)
			wallet_fn = wallet_fn or self.get_wallet_fn(fn)
			d_wrap = self.extract_data_from_file(parent.cfg, fn)
			data = d_wrap['data']
			check_equal('Seed ID', data['seed_id'], parent.kal.al_id.sid)
			wallet_idx = parent.get_idx_from_fn(wallet_fn)
			check_equal('Wallet index', data['wallet_index'], wallet_idx)
			super().__init__(
				parent     = parent,
				wallet_fn  = wallet_fn,
				data       = data,
				wallet_idx = wallet_idx)
			self.check_checksums(d_wrap)

		@classmethod
		def find_fn_from_wallet_fn(cls, cfg, wallet_fn, *, ret_on_no_match=False):
			path = get_autosign_obj(cfg).xmr_outputs_dir or Path()
			pat = cls.fn_fs.format(
				a = wallet_fn.name,
				b = f'[0-9a-f]{{{cls.chksum_nchars}}}\\',
				c = cls.ext)
			matches = [f for f in path.iterdir() if re.match(pat, f.name)]
			if not matches and ret_on_no_match:
				return None
			if not matches or len(matches) > 1:
				die(2, "{a} matching pattern {b!r} found in '{c}'!".format(
					a = 'No files' if not matches else 'More than one file',
					b = pat,
					c = path))
			return matches[0]

	class Unsigned(Completed):
		pass

	class SignedNew(New):
		desc = 'signed key images'
		ext = 'sig'

	class Signed(Completed, SignedNew):
		pass

class MoneroWalletDumpFile:

	class Base:
		desc = 'Monero wallet dump'
		data_label = 'MoneroMMGenWalletDumpFile'
		base_chksum_fields = {'seed_id', 'wallet_index', 'wallet_metadata'}
		full_chksum_fields = None
		ext = 'dump'
		ext_offset = 0
		data_tuple = namedtuple('wallet_dump_data', [
			'seed_id',
			'wallet_index',
			'wallet_metadata'])
		def get_outfile(self, cfg, wallet_fn):
			return wallet_fn.parent / f'{wallet_fn.name}.{self.ext}'

	class New(Base, MoneroWalletOutputsFile.New):
		pass

	class Completed(Base, MoneroWalletOutputsFile.Completed):
		pass
