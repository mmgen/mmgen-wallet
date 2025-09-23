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
proto.btc.tx.info: Bitcoin transaction info class
"""

from ....tx.info import TxInfo
from ....util import fmt, die
from ....color import red, green, blue, pink
from ....addr import MMGenID

class TxInfo(TxInfo):

	sort_orders = ('addr', 'raw')
	txinfo_hdr_fs = '{hdr}\n  ID={i} ({a} {c}) RBF={r} Sig={s} Locktime={l}\n'
	txinfo_hdr_fs_short = 'TX {i} ({a} {c}) RBF={r} Sig={s} Locktime={l}\n'
	txinfo_ftr_fs = fmt("""
		Input amount: {i} {d}
		Spend amount: {s} {d}
		Change:       {C} {d}
		Fee:          {a} {c}{r}
	""")

	def format_rel_fee(self):
		tx = self.tx
		return ' ({} {}, {} of spend amount)'.format(
			pink(tx.fee_abs2rel(tx.fee)),
			tx.rel_fee_disp,
			pink('{:0.6f}%'.format(tx.fee / tx.send_amt * 100))
		)

	def format_abs_fee(self, iwidth, /, *, color=None):
		return self.tx.fee.fmt(iwidth, color=color)

	def format_verbose_footer(self):
		tx = self.tx
		tsize = len(tx.serialized) // 2 if tx.serialized else 'unknown'
		out = f'Transaction size: Vsize {tx.estimate_size()} (estimated), Total {tsize}'
		if tx.name in ('Signed', 'OnlineSigned'):
			wsize = tx.deserialized.witness_size
			out += f', Base {tsize-wsize}, Witness {wsize}'
		return out + '\n'

	def format_body(self, blockcount, nonmm_str, max_mmwid, enl, *, terse, sort):

		if sort not in self.sort_orders:
			die(1, '{!r}: invalid transaction view sort order. Valid options: {}'.format(
				sort,
				','.join(self.sort_orders)))

		def get_mmid_fmt(e, is_input):
			if e.mmid:
				return e.mmid.fmt2(
					max_mmwid,
					encl = '()',
					color = True,
					append_chars = ('', ' (chg)')[bool(not is_input and e.is_chg and terse)],
					append_color = 'green')
			else:
				return MMGenID.fmtc(
					'[vault address]' if not is_input and e.is_vault else nonmm_str,
					max_mmwid,
					color = True)

		def format_io(desc):
			io = getattr(tx, desc)
			is_input = desc == 'inputs'
			yield desc.capitalize() + ':\n' + enl
			confs_per_day = 60*60*24 // tx.proto.avg_bdi

			io_sorted = {
				'addr': lambda: sorted(
					io, # prepend '+' (sorts before '0') to ensure non-MMGen addrs are displayed first
					key = lambda o: (o.mmid.sort_key if o.mmid else f'+{o.addr}') + f'{o.amt:040.20f}'),
				'raw':  lambda: io
			}[sort]

			def data_disp(data):
				return f'OP_RETURN data ({len(data)} bytes)'

			if terse:
				iwidth = max(len(str(int(e.amt))) for e in io)
				addr_w = max((len(e.addr.views[vp1]) if e.addr else len(data_disp(e.data))) for f in (tx.inputs, tx.outputs) for e in f)
				for n, e in enumerate(io_sorted()):
					yield '{:3} {} {} {} {}\n'.format(
						n+1,
						e.addr.fmt(vp1, addr_w, color=True) if e.addr else blue(data_disp(e.data).ljust(addr_w)),
						get_mmid_fmt(e, is_input) if e.addr else ''.ljust(max_mmwid),
						e.amt.fmt(iwidth, color=True),
						tx.dcoin)
					if have_bch and e.addr:
						yield '{:3} [{}]\n'.format('', e.addr.hl(vp2, color=False))
			else:
				col1_w = len(str(len(io))) + 1
				for n, e in enumerate(io_sorted()):
					mmid_fmt = get_mmid_fmt(e, is_input)
					if is_input and blockcount:
						confs = e.confs + blockcount - tx.blockcount
						days = int(confs // confs_per_day)
					def gen():
						if is_input:
							yield (n+1, 'tx,vout:', f'{e.txid.hl()},{red(str(e.vout))}')
							yield ('',  'address:', f'{e.addr.hl(vp1)} {mmid_fmt}')
							if have_bch:
								yield ('', '', f'[{e.addr.hl(vp2, color=False)}]')
						else:
							yield (
								n + 1,
								'address:',
								(f'{e.addr.hl(vp1)} {mmid_fmt}' if e.addr else e.data.hl(add_label=True)))
							if have_bch and e.addr:
								yield ('', '', f'[{e.addr.hl(vp2, color=False)}]')
						if e.comment:
							yield ('',  'comment:', e.comment.hl())
						yield     ('',  'amount:',  f'{e.amt.hl()} {tx.dcoin}')
						if is_input and blockcount:
							yield ('',  'confirmations:', f'{confs} (around {days} days)')
						if not is_input and e.is_chg:
							yield ('',  'change:',  green('True'))
					yield '\n'.join('{:>{w}} {:<8} {}'.format(*d, w=col1_w) for d in gen()) + '\n\n'

		tx = self.tx

		if self.cfg._proto.coin == 'BCH':
			have_bch = True
			vp1 = 1 if not self.cfg.cashaddr else not self.cfg._proto.cashaddr
			vp2 = (vp1 + 1) % 2
		else:
			have_bch = False
			vp1 = 0

		return (
			'Inputs/Outputs sort order: {}'.format({
				'raw':  pink('UNSORTED'),
				'addr': pink('ADDRESS')
			}[sort])
			+ ('\n\n', '\n')[terse]
			+ ''.join(format_io('inputs'))
			+ ''.join(format_io('outputs')))

	def strfmt_locktime(self, locktime=None, *, terse=False):
		# Locktime itself is an unsigned 4-byte integer which can be parsed two ways:
		#
		# If less than 500 million, locktime is parsed as a block height. The transaction can be
		# added to any block which has this height or higher.
		# MMGen note: s/this height or higher/a higher block height/
		#
		# If greater than or equal to 500 million, locktime is parsed using the Unix epoch time
		# format (the number of seconds elapsed since 1970-01-01T00:00 UTC). The transaction can be
		# added to any block whose block time is greater than the locktime.
		match locktime or self.tx.locktime:
			case None:
				return '(None)'
			case num if num.bit_length() > 32:
				die(2, f'{num!r}: invalid nLockTime value (integer size greater than 4 bytes)!')
			case num if num >= 500_000_000:
				import time
				return ' '.join(time.strftime('%c', time.gmtime(num)).split()[1:])
			case num if num > 0:
				return '{}{}'.format(('block height ', '')[terse], num)
			case num:
				die(2, f'{num!r}: invalid nLockTime value!')
