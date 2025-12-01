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
xmrwallet.file.tx: Monero transaction file class for the MMGen Suite
"""

import time
from collections import namedtuple
from pathlib import Path

from ...obj import CoinTxID, Int
from ...color import red, yellow, blue, cyan, pink, orange, purple
from ...util import die, fmt, make_timestr, list_gen
from ...seed import SeedID
from ...protocol import init_proto
from ...addr import CoinAddr
from ...tx.util import get_autosign_obj

from ..include import XMRWalletAddrSpec
from . import MoneroMMGenFile

class MoneroMMGenTX:

	class Base(MoneroMMGenFile):

		data_label = 'MoneroMMGenTX'

		# both base_chksum and full_chksum are used to make the filename stem, so we must not include
		# fields that change when TX is signed and submitted (e.g. ‘sign_time’, ‘submit_time’)
		base_chksum_fields = {
			'op',
			'create_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'amount'}
		full_chksum_fields = {
			'op',
			'create_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'amount',
			'fee',
			'blob'}
		oneline_fs = '{a:7} {b:8} {c:19} {d:13} {e:9} {f:6} {x:2} {g:6} {h:17} {j}'
		oneline_fixed_cols_w = 96 # width of all columns except the last (coin address)
		chksum_nchars = 6
		xmrwallet_tx_data = namedtuple('xmrwallet_tx_data', [
			'op',
			'create_time',
			'sign_time',
			'submit_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'dest_address',
			'txid',
			'amount',
			'priority',
			'fee',
			'blob',
			'metadata',
			'unsigned_txset',
			'signed_txset',
			'complete'])

		def __init__(self):
			self.name = type(self).__name__

		@property
		def src_wallet_idx(self):
			return int(self.data.source.split(':')[0])

		def get_info_oneline(self, *, indent='', addr_w=None):
			d = self.data
			return self.oneline_fs.format(
					a = yellow(d.network),
					b = d.seed_id.hl(),
					c = make_timestr(d.submit_time if d.submit_time is not None else d.create_time),
					d = orange(self.file_id),
					e = purple(d.op.ljust(9)),
					f = red('{}:{}'.format(d.source.wallet, d.source.account).ljust(6)),
					g = red('{}:{}'.format(d.dest.wallet, d.dest.account).ljust(6))
						if d.dest else cyan('ext   '),
					h = d.amount.fmt(4, color=True, prec=12),
					j = d.dest_address.fmt(0, addr_w, color=True) if addr_w else d.dest_address.hl(0),
					x = '->')

		def get_info(self, *, indent='', addr_w=None):
			d = self.data
			pmt_id = d.dest_address.parsed.payment_id
			fs = '\n'.join(list_gen(
				['Info for transaction {a} [Seed ID: {b}. Network: {c}]:'],
				['  TxID:      {d}'],
				['  Created:   {e:19} [{f}]'],
				['  Signed:    {g:19} [{h}]', d.sign_time],
				['  Submitted: {s:19} [{t}]', d.submit_time],
				['  Type:      {i}{S}'],
				['  From:      wallet {j}, account {k}'],
				['  To:        wallet {x}, account {y}, address {z}', d.dest],
				['  Amount:    {m} XMR'],
				['  Priority:  {F}', d.priority],
				['  Fee:       {n} XMR'],
				['  Dest:      {o}'],
				['  Size:      {Z} bytes', d.signed_txset],
				['  Payment ID: {P}', pmt_id]))

			from ...util2 import format_elapsed_hr
			from ..ops import addr_width
			from .. import tx_priorities
			return fmt(fs, strip_char='\t', indent=indent).format(
					a = orange(self.file_id),
					b = d.seed_id.hl(),
					c = yellow(d.network.upper()),
					d = d.txid.hl(),
					e = make_timestr(d.create_time),
					f = format_elapsed_hr(d.create_time),
					g = make_timestr(d.sign_time) if d.sign_time else None,
					h = format_elapsed_hr(d.sign_time) if d.sign_time else None,
					i = blue(d.op),
					j = d.source.wallet.hl(),
					k = red(f'#{d.source.account}'),
					m = d.amount.hl(),
					F = (Int(d.priority).hl() + f' [{tx_priorities[d.priority]}]')
						if d.priority else None,
					n = d.fee.hl(),
					o = d.dest_address.hl(0)
						if self.cfg.full_address else d.dest_address.fmt(0, addr_width, color=True),
					P = pink(pmt_id.hex()) if pmt_id else None,
					s = make_timestr(d.submit_time) if d.submit_time else None,
					S = pink(f" [cold signed{', submitted' if d.complete else ''}]")
						if d.signed_txset else '',
					t = format_elapsed_hr(d.submit_time) if d.submit_time else None,
					x = d.dest.wallet.hl() if d.dest else None,
					y = red(f'#{d.dest.account}') if d.dest else None,
					z = red(f'#{d.dest.account_address}') if d.dest else None,
					Z = Int(len(d.signed_txset) // 2).hl() if d.signed_txset else None)

		@property
		def file_id(self):
			return (self.base_chksum + ('-' + self.full_chksum if self.full_chksum else '')).upper()

		def write(self, *, delete_metadata=False, ask_write=True, ask_overwrite=True):
			dict_data = self.data._asdict()
			if delete_metadata:
				dict_data['metadata'] = None

			fn = '{a}-XMR[{b!s}]{c}.{d}'.format(
				a = self.file_id,
				b = self.data.amount,
				c = '' if self.data.network == 'mainnet' else f'.{self.data.network}',
				d = self.ext)

			if self.cfg.autosign:
				fn = getattr(get_autosign_obj(self.cfg), self.tx_dir) / fn

			from ...fileutil import write_data_to_file
			write_data_to_file(
				cfg                   = self.cfg,
				outfile               = str(fn),
				data                  = self.make_wrapped_data(dict_data),
				desc                  = self.desc,
				ask_write             = ask_write,
				ask_write_default_yes = not ask_write,
				ask_overwrite         = ask_overwrite,
				ignore_opt_outdir     = self.cfg.autosign)

	class New(Base):
		is_new = False
		is_signing = False
		is_submitting = False
		is_complete = False
		signed = False
		tx_dir = 'xmr_tx_dir'

		def __init__(self, *args, **kwargs):

			super().__init__()

			assert not args, 'Non-keyword args not permitted'

			if '_in_tx' in kwargs:
				in_data = kwargs.pop('_in_tx').data._asdict()
				in_data.update(kwargs)
			else:
				in_data = kwargs

			d = namedtuple('monero_tx_in_data_tuple', in_data)(**in_data)
			self.cfg = d.cfg

			proto = init_proto(self.cfg, 'xmr', network=d.network, need_amt=True)

			now = int(time.time())

			self.data = self.xmrwallet_tx_data(
				op             = d.op,
				create_time    = now if self.is_new else getattr(d, 'create_time', None),
				sign_time      = now if self.is_signing else getattr(d, 'sign_time', None),
				submit_time    = now if self.is_submitting else None,
				network        = d.network,
				seed_id        = SeedID(sid=d.seed_id),
				source         = XMRWalletAddrSpec(d.source),
				dest           = None if d.dest is None else XMRWalletAddrSpec(d.dest),
				dest_address   = CoinAddr(proto, d.dest_address),
				txid           = CoinTxID(d.txid),
				amount         = d.amount,
				priority       = self.cfg.priority if self.is_new else d.priority,
				fee            = d.fee,
				blob           = d.blob,
				metadata       = d.metadata,
				unsigned_txset = d.unsigned_txset,
				signed_txset   = getattr(d, 'signed_txset', None),
				complete       = self.is_complete)

	class NewUnsigned(New):
		desc = 'unsigned transaction'
		ext = 'rawtx'
		is_new = True

	class NewColdSigned(New):
		desc = 'signed transaction'
		ext = 'sigtx'
		is_signing = True
		signed = True

	class NewSigned(NewColdSigned):
		is_new = True
		is_complete = True

	class NewSubmitted(New):
		desc = 'submitted transaction'
		ext = 'subtx'
		signed = True
		is_submitting = True
		is_complete = True

	class NewUnsignedCompat(NewUnsigned):
		tx_dir = 'txauto_dir'
		ext = 'arawtx'

	class NewColdSignedCompat(NewColdSigned):
		tx_dir = 'txauto_dir'
		ext = 'asigtx'

	class NewSubmittedCompat(NewSubmitted):
		tx_dir = 'txauto_dir'
		ext = 'asubtx'

	class Completed(Base):
		desc = 'transaction'
		forbidden_fields = ()

		def __init__(self, cfg, fn):

			super().__init__()

			self.cfg = cfg
			self.fn = Path(fn)

			try:
				d_wrap = self.extract_data_from_file(cfg, fn)
			except Exception as e:
				die('MoneroMMGenTXFileParseError',
					f'{type(e).__name__}: {e}\nCould not load transaction file')

			if 'unsigned_txset' in d_wrap['data']: # post-autosign
				self.full_chksum_fields &= set(d_wrap['data']) # allow for added chksum fields in future
			else:
				self.full_chksum_fields = set(d_wrap['data']) - {'metadata'}

			for key in self.xmrwallet_tx_data._fields: # backwards compat: fill in missing fields
				if not key in d_wrap['data']:
					d_wrap['data'][key] = None

			d = self.xmrwallet_tx_data(**d_wrap['data'])

			if self.name not in ('View', 'Completed'):
				assert fn.name.endswith('.' + self.ext), (
					f'TX file {fn} has incorrect extension (not {self.ext!r})')
				assert getattr(d, self.req_field), (
					f'{self.name} TX missing required field {self.req_field!r}')
				assert bool(d.sign_time) == self.signed, '{a} has {b}sign time!'.format(
					a = self.desc,
					b = 'no ' if self.signed else'')
				for f in self.forbidden_fields:
					assert not getattr(d, f), f'{self.name} TX mismatch: contains forbidden field {f!r}'

			proto = init_proto(cfg, 'xmr', network=d.network, need_amt=True)

			self.data = self.xmrwallet_tx_data(
				op             = d.op,
				create_time    = d.create_time,
				sign_time      = d.sign_time,
				submit_time    = d.submit_time,
				network        = d.network,
				seed_id        = SeedID(sid=d.seed_id),
				source         = XMRWalletAddrSpec(d.source),
				dest           = None if d.dest is None else XMRWalletAddrSpec(d.dest),
				dest_address   = CoinAddr(proto, d.dest_address),
				txid           = CoinTxID(d.txid),
				amount         = proto.coin_amt(d.amount),
				priority       = d.priority,
				fee            = proto.coin_amt(d.fee),
				blob           = d.blob,
				metadata       = d.metadata,
				unsigned_txset = d.unsigned_txset,
				signed_txset   = d.signed_txset,
				complete       = d.complete)

			self.check_checksums(d_wrap)

	class Unsigned(Completed):
		desc = 'unsigned transaction'
		ext = 'rawtx'
		signed = False
		req_field = 'unsigned_txset'
		forbidden_fields = ('signed_txset',)

	class Signed(Completed):
		desc = 'signed transaction'
		ext = 'sigtx'
		signed = True
		req_field = 'blob'
		forbidden_fields = ('signed_txset', 'unsigned_txset')

	class ColdSigned(Signed):
		req_field = 'signed_txset'
		forbidden_fields = ()

	class Submitted(ColdSigned):
		desc = 'submitted transaction'
		ext = 'subtx'
		silent_load = True

	class View(Completed):
		silent_load = True

	class UnsignedCompat(Unsigned):
		ext = 'arawtx'

	class ColdSignedCompat(ColdSigned):
		ext = 'asigtx'

	class SubmittedCompat(Submitted):
		ext = 'asubtx'
