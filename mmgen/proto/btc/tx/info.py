#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.btc.tx.info: Bitcoin transaction info class
"""

from ....tx.info import TxInfo
from ....util import fmt,die
from ....color import red,green,pink
from ....addr import MMGenID

class TxInfo(TxInfo):
	sort_orders = ('addr','raw')
	txinfo_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} RBF={r} Sig={s} Locktime={l}\n'
	txinfo_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} RBF={r} Sig={s} Locktime={l}\n'
	txinfo_ftr_fs = fmt("""
		Input amount: {i} {d}
		Spend amount: {s} {d}
		Change:       {C} {d}
		Fee:          {a} {c}{r}
	""")

	def format_rel_fee(self,terse):
		tx = self.tx
		return ' ({} {}, {} of spend amount)'.format(
			pink(str(tx.fee_abs2rel(tx.fee))),
			tx.rel_fee_disp,
			pink('{:0.6f}%'.format( tx.fee / tx.send_amt * 100 ))
		)

	def format_abs_fee(self,color,iwidth):
		return self.tx.proto.coin_amt(self.tx.fee).fmt(color=color,iwidth=iwidth)

	def format_verbose_footer(self):
		tx = self.tx
		tsize = len(tx.serialized) // 2 if tx.serialized else 'unknown'
		out = f'Transaction size: Vsize {tx.estimate_size()} (estimated), Total {tsize}'
		if tx.name in ('Signed','OnlineSigned'):
			wsize = tx.deserialized.witness_size
			out += f', Base {tsize-wsize}, Witness {wsize}'
		return out + '\n'

	def format_body(self,blockcount,nonmm_str,max_mmwid,enl,terse,sort):
		tx = self.tx

		if sort not in self.sort_orders:
			die(1,'{!r}: invalid transaction view sort order. Valid options: {}'.format(
				sort,
				','.join(self.sort_orders) ))

		def format_io(desc):
			io = getattr(tx,desc)
			is_input = desc == 'inputs'
			yield desc.capitalize() + ':\n' + enl
			confs_per_day = 60*60*24 // tx.proto.avg_bdi
			io_sorted = {
				'addr': lambda: sorted(
					io, # prepend '+' (sorts before '0') to ensure non-MMGen addrs are displayed first
					key = lambda o: (o.mmid.sort_key if o.mmid else f'+{o.addr}') + f'{o.amt:040.20f}' ),
				'raw':  lambda: io
			}[sort]
			if terse:
				iwidth = max(len(str(int(e.amt))) for e in io)
			for n,e in enumerate(io_sorted()):
				if is_input and blockcount:
					confs = e.confs + blockcount - tx.blockcount
					days = int(confs // confs_per_day)
				if e.mmid:
					mmid_fmt = e.mmid.fmt(
						width=max_mmwid,
						encl='()',
						color=True,
						append_chars=('',' (chg)')[bool(not is_input and e.is_chg and terse)],
						append_color='green')
				else:
					mmid_fmt = MMGenID.fmtc( nonmm_str, width=max_mmwid, color=True )
				if terse:
					yield '{:3} {} {} {} {}\n'.format(
						n+1,
						e.addr.fmt(color=True,width=addr_w),
						mmid_fmt,
						e.amt.fmt(iwidth=iwidth,color=True),
						tx.dcoin )
				else:
					def gen():
						if is_input:
							yield (n+1, 'tx,vout:', f'{e.txid.hl()},{red(str(e.vout))}')
							yield ('',  'address:', f'{e.addr.hl()} {mmid_fmt}')
						else:
							yield (n+1, 'address:', f'{e.addr.hl()} {mmid_fmt}')
						if e.comment:
							yield ('',  'comment:', e.comment.hl())
						yield     ('',  'amount:',  f'{e.amt.hl()} {tx.dcoin}')
						if is_input and blockcount:
							yield ('',  'confirmations:', f'{confs} (around {days} days)')
						if not is_input and e.is_chg:
							yield ('',  'change:',  green('True'))
					yield '\n'.join('{:>3} {:<8} {}'.format(*d) for d in gen()) + '\n\n'

		addr_w = max(len(e.addr) for f in (tx.inputs,tx.outputs) for e in f)

		return (
			'Displaying inputs and outputs in {} sort order'.format({'raw':'raw','addr':'address'}[sort])
			+ ('\n\n','\n')[terse]
			+ ''.join(format_io('inputs'))
			+ ''.join(format_io('outputs')) )

	def strfmt_locktime(self,locktime=None,terse=False):
		# Locktime itself is an unsigned 4-byte integer which can be parsed two ways:
		#
		# If less than 500 million, locktime is parsed as a block height. The transaction can be
		# added to any block which has this height or higher.
		# MMGen note: s/this height or higher/a higher block height/
		#
		# If greater than or equal to 500 million, locktime is parsed using the Unix epoch time
		# format (the number of seconds elapsed since 1970-01-01T00:00 UTC). The transaction can be
		# added to any block whose block time is greater than the locktime.
		num = locktime or self.tx.locktime
		if num == None:
			return '(None)'
		elif num >= 5 * 10**6:
			import time
			return ' '.join(time.strftime('%c',time.gmtime(num)).split()[1:])
		elif num > 0:
			return '{}{}'.format(('block height ','')[terse],num)
		else:
			die(2,f'{num!r}: invalid nLockTime value!')
