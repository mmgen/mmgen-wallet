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
proto.btc.tw.txhistory: Bitcoin base protocol tracking wallet transaction history class
"""

from collections import namedtuple

from ....tw.txhistory import TwTxHistory
from ....tw.shared import get_tw_label, TwMMGenID
from ....addr import CoinAddr
from ....util import msg, msg_r
from ....color import nocolor, red, pink, gray
from ....obj import TwComment, CoinTxID, Int

from .rpc import BitcoinTwRPC
from .view import BitcoinTwView

class BitcoinTwTransaction:

	no_address_str = '[DATA]'

	def __init__(self, *, parent, proto, rpc,
			idx,          # unique numeric identifier of this transaction in listing
			unspent_info, # addrs in wallet with balances: {'mmid': {'addr', 'comment', 'amt'}}
			mm_map,       # all addrs in wallet: ['addr', ['twmmid', 'comment']]
			tx,           # the decoded transaction data
			wallet_vouts, # list of ints - wallet-related vouts
			prevouts,     # list of (txid,vout) pairs
			prevout_txs   # decoded transaction data for prevouts
		):

		self.parent       = parent
		self.proto        = proto
		self.rpc          = rpc
		self.idx          = idx
		self.unspent_info = unspent_info
		self.tx           = tx

		def gen_prevouts_data():
			_d = namedtuple('prevout_data', ['txid', 'data'])
			for tx in prevout_txs:
				for e in prevouts:
					if e.txid == tx['txid']:
						yield _d(e.txid, tx['vout'][e.vout])

		def gen_wallet_vouts_data():
			_d = namedtuple('wallet_vout_data', ['txid', 'data'])
			txid = self.tx['txid']
			vouts = self.tx['decoded']['vout']
			for n in wallet_vouts:
				yield _d(txid, vouts[n])

		def gen_vouts_info(data):
			_d = namedtuple('vout_info', ['txid', 'coin_addr', 'twlabel', 'data'])
			def gen():
				for d in data:
					addr = (
						d.data['scriptPubKey'].get('address') or
						d.data['scriptPubKey'].get('addresses',[self.no_address_str])[0])
					yield _d(
						txid = d.txid,
						coin_addr = addr,
						twlabel = mm_map[addr] if (addr in mm_map and mm_map[addr].twmmid) else None,
						data = d.data)
			return sorted(
				gen(),
				# if address is not MMGen, ignore address and sort by TxID + vout only
				key = lambda d: (
					(d.twlabel.twmmid.sort_key if d.twlabel and d.twlabel.twmmid.type == 'mmgen' else '')
					+ '_'
					+ d.txid
					+ '{:08d}'.format(d.data['n'])
				))

		def gen_all_addrs(src):
			for e in self.vouts_info[src]:
				if e.twlabel:
					mmid = e.twlabel.twmmid
					yield (
						(mmid if mmid.type == 'mmgen' else mmid.split(':', 1)[1]) +
						('*' if mmid in self.unspent_info else '')
					)
				else:
					yield e.coin_addr

		def total(data):
			return sum(coin_amt(d.data['value']) for d in data)

		def get_best_comment():
			"""
			find the most relevant comment for tabular (squeezed) display
			"""
			def vouts_labels(src):
				return [d.twlabel.comment for d in self.vouts_info[src] if d.twlabel and d.twlabel.comment]
			ret = vouts_labels('outputs') or vouts_labels('inputs')
			return ret[0] if ret else TwComment('')

		coin_amt = self.proto.coin_amt
		# 'outputs' refers to wallet-related outputs only
		self.vouts_info = {
			'inputs':  gen_vouts_info(gen_prevouts_data()),
			'outputs': gen_vouts_info(gen_wallet_vouts_data())}
		self.max_addrlen = {
			'inputs':  max(len(addr) for addr in gen_all_addrs('inputs')),
			'outputs': max(len(addr) for addr in gen_all_addrs('outputs'))}
		self.inputs_total = total(self.vouts_info['inputs'])
		self.outputs_total = sum(coin_amt(i['value']) for i in self.tx['decoded']['vout'])
		self.wallet_outputs_total = total(self.vouts_info['outputs'])
		self.fee = self.inputs_total - self.outputs_total
		self.nOutputs = len(self.tx['decoded']['vout'])
		self.confirmations = self.tx['confirmations']
		self.comment = get_best_comment()
		self.vsize = self.tx['decoded'].get('vsize') or self.tx['decoded']['size']
		self.txid = CoinTxID(self.tx['txid'])
		# Though 'blocktime' is flagged as an “optional” field, it’s always present for transactions
		# that are in the blockchain.  However, Bitcoin Core wallet saves a record of broadcast but
		# unconfirmed transactions, e.g. replaced transactions, and the 'blocktime' field is missing
		# for these, so use 'time' as a fallback.
		self.time = self.tx.get('blocktime') or self.tx['time']
		self.time_received = self.tx.get('timereceived')

	def blockheight_disp(self, *, color):
		return (
			# old/altcoin daemons return no 'blockheight' field, so use confirmations instead
			Int(self.rpc.blockcount + 1 - self.confirmations).hl(color=color)
			if self.confirmations > 0 else None)

	def age_disp(self, age_fmt, *, width, color):
		match age_fmt:
			case 'confs':
				ret_str = str(self.confirmations).ljust(width)
				return gray(ret_str) if self.confirmations < 0 and color else ret_str
			case 'block':
				ret = (self.rpc.blockcount - (abs(self.confirmations) - 1)) * (-1 if self.confirmations < 0 else 1)
				ret_str = str(ret).ljust(width)
				return gray(ret_str) if ret < 0 and color else ret_str
			case _:
				return self.parent.date_formatter[age_fmt](self.rpc, self.tx.get('blocktime', 0))

	def txdate_disp(self, age_fmt):
		return self.parent.date_formatter[age_fmt](self.rpc, self.time)

	def txid_disp(self, *, color, width=None):
		return self.txid.hl(color=color) if width is None else self.txid.truncate(width, color=color)

	def vouts_list_disp(self, src, color, indent, addr_view_pref):

		fs1, fs2 = {
			'inputs':  ('{i},{n} {a} {A}', '{i},{n} {a} {A} {l}'),
			'outputs': (    '{n} {a} {A}',     '{n} {a} {A} {l}')
		}[src]

		def gen_output():
			for e in self.vouts_info[src]:
				mmid = e.twlabel.twmmid if e.twlabel else None
				if not mmid:
					yield fs1.format(
						i = CoinTxID(e.txid).hl(color=color),
						n = (nocolor, red)[color](str(e.data['n']).ljust(3)),
						a = CoinAddr(self.proto, e.coin_addr).fmt(
							addr_view_pref, self.max_addrlen[src], color=color)
								if e.coin_addr != self.no_address_str else
							CoinAddr.fmtc(e.coin_addr, self.max_addrlen[src], color=color),
						A = self.proto.coin_amt(e.data['value']).fmt(color=color)
					).rstrip()
				else:
					bal_star, co = ('*', 'melon') if mmid in self.unspent_info else ('', 'brown')
					addr_out = mmid if mmid.type == 'mmgen' else mmid.split(':', 1)[1]
					yield fs2.format(
						i = CoinTxID(e.txid).hl(color=color),
						n = (nocolor, red)[color](str(e.data['n']).ljust(3)),
						a = TwMMGenID.hl2(
							TwMMGenID,
							s = '{:{w}}'.format(addr_out + bal_star, w=self.max_addrlen[src]),
							color = color,
							color_override = co),
						A = self.proto.coin_amt(e.data['value']).fmt(color=color),
						l = e.twlabel.comment.hl(color=color)
					).rstrip()

		return f'\n{indent}'.join(gen_output()).strip()

	def vouts_disp(self, src, width, color, addr_view_pref):

		def gen_output():

			nonlocal space_left

			for e in self.vouts_info[src]:
				mmid = e.twlabel.twmmid if e.twlabel else None
				bal_star, addr_w, co = ('*', 16, 'melon') if mmid in self.unspent_info else ('', 15, 'brown')
				if not mmid:
					if width and space_left < addr_w:
						break
					yield (
						CoinAddr(self.proto, e.coin_addr).fmt(addr_view_pref, addr_w, color=color)
							if e.coin_addr != self.no_address_str else
						CoinAddr.fmtc(e.coin_addr, addr_w, color=color))
					space_left -= addr_w
				elif mmid.type == 'mmgen':
					mmid_disp = mmid + bal_star
					if width and space_left < len(mmid_disp):
						break
					yield TwMMGenID.hl2(TwMMGenID, s=mmid_disp, color=color, color_override=co)
					space_left -= len(mmid_disp)
				else:
					if width and space_left < addr_w:
						break
					yield TwMMGenID.hl2(
						TwMMGenID,
						s = CoinAddr.fmtc(mmid.split(':', 1)[1] + bal_star, addr_w),
						color = color,
						color_override = co)
					space_left -= addr_w
				space_left -= 1

		space_left = width or 0

		return ' '.join(gen_output()) + ' ' * (space_left + 1 if width else 0)

	def amt_disp(self, show_total_amt):
		return (
			self.outputs_total if show_total_amt else
			self.wallet_outputs_total)

	def fee_disp(self, color):
		atomic_unit = self.proto.coin_amt.units[0]
		return '{} {}'.format(
			self.fee.hl(color=color),
			(nocolor, pink)[color]('({:,} {}s/byte)'.format(
				self.fee.to_unit(atomic_unit) // self.vsize,
				atomic_unit)))

class BitcoinTwTxHistory(BitcoinTwView, TwTxHistory, BitcoinTwRPC):

	has_age = True
	hdr_lbl = 'transaction history'
	desc = 'transaction history'
	item_desc = 'transaction'
	item_desc_pl = 'transactions'
	prompt_fs_in = [
		'Sort options: [t]xid, [a]mt, total a[m]t, [A]ge, block[n]um, [r]everse',
		'Column options: toggle [D]ays/date/confs/block, tx[i]d, [T]otal amt',
		'View/Print: pager [v]iew, full pager [V]iew, [p]rint, full [P]rint{s}',
		'Filters/Actions: show [u]nconfirmed, [q]uit menu, r[e]draw:']
	prompt_fs_repl = {
		'BCH': (1, 'Column options: toggle [D]ate/confs, cas[h]addr, tx[i]d, [T]otal amt')}
	key_mappings = {
		'A':'s_age',
		'n':'s_blockheight',
		'a':'s_amt',
		'm':'s_total_amt',
		't':'s_txid',
		'r':'s_reverse',
		'D':'d_days',
		'e':'d_redraw',
		'u':'d_show_unconfirmed',
		'i':'d_show_txid',
		'T':'d_show_total_amt',
		'v':'a_view',
		'V':'a_view_detail',
		'p':'a_print_squeezed',
		'P':'a_print_detail'}

	async def get_rpc_data(self):
		blockhash = (
			await self.rpc.call('getblockhash', self.sinceblock)
				if self.sinceblock else '')
		return (await self.rpc.icall(
			'listsinceblock',
			blockhash = blockhash,
			include_removed = False))['transactions']

	async def gen_data(self, rpc_data, lbl_id):

		def gen_parsed_data():
			for o in rpc_data:
				if lbl_id in o:
					lbl = get_tw_label(self.proto, o[lbl_id])
					yield o | {
						'twmmid': lbl.mmid,
						'comment': lbl.comment or ''}
				else:
					assert o['category'] == 'send', f"{o['address']}: {o['category']} != 'send'"
					yield o | {
						'twmmid': None,
						'comment': None}

		data = list(gen_parsed_data())

		if self.cfg.debug_tw:
			import json
			from ....rpc.util import json_encoder
			def do_json_dump(*data):
				nw = f'{self.proto.coin.lower()}-{self.proto.network}'
				for d, fn_stem in data:
					with open(f'/tmp/{fn_stem}-{nw}.json', 'w') as fh:
						fh.write(json.dumps(d, cls=json_encoder))

		_mmp = namedtuple('mmap_datum', ['twmmid', 'comment'])

		mm_map = {
			i['address']: (
				_mmp(TwMMGenID(self.proto, i['twmmid']), TwComment(i['comment']))
					if i['twmmid'] else _mmp(None, None)
			)
			for i in data if 'address' in i}

		if self.sinceblock: # mapping data may be incomplete for inputs, so update from 'listlabels'
			mm_map.update(
				{e.coinaddr: _mmp(e.label.mmid, e.label.comment) if e.label else _mmp(None, None)
					for e in await self.get_label_addr_pairs()}
			)

		msg_r('Getting wallet transactions...')
		_wallet_txs = await self.rpc.gathered_icall(
			'gettransaction',
			[(i, True, True) for i in {d['txid'] for d in data}])
		msg('done')

		if not 'decoded' in _wallet_txs[0]:
			_decoded_txs = iter(
				await self.rpc.gathered_call(
					'decoderawtransaction',
					[(d['hex'],) for d in _wallet_txs]))
			for tx in _wallet_txs:
				tx['decoded'] = next(_decoded_txs)

		if self.cfg.debug_tw:
			do_json_dump((_wallet_txs, 'wallet-txs'),)

		_wip = namedtuple('prevout', ['txid', 'vout'])
		txdata = [{
			'tx': tx,
			'wallet_vouts': sorted({i.vout for i in
				[_wip(CoinTxID(d['txid']), d['vout']) for d in data]
					if i.txid == tx['txid']}),
			'prevouts': [_wip(CoinTxID(vin['txid']), vin['vout']) for vin in tx['decoded']['vin']]}
				for tx in _wallet_txs]

		_prevout_txids = {i.txid for d in txdata for i in d['prevouts']}

		msg_r('Getting input transactions...')
		_prevout_txs = await self.rpc.gathered_call('getrawtransaction', [(i, True) for i in _prevout_txids])
		msg('done')

		_prevout_txs_dict = dict(zip(_prevout_txids, _prevout_txs))

		for d in txdata:
			d['prevout_txs'] = [_prevout_txs_dict[txid] for txid in {i.txid for i in d['prevouts']}]

		if self.cfg.debug_tw:
			do_json_dump(
				(rpc_data,     'txhist-rpc'),
				(data,         'txhist'),
				(mm_map,       'mmap'),
				(_prevout_txs, 'prevout-txs'),
				(txdata,       'txdata'),
			)

		unspent_info = await self.get_unspent_by_mmid()

		return (
			BitcoinTwTransaction(
				parent       = self,
				proto        = self.proto,
				rpc          = self.rpc,
				idx          = idx,
				unspent_info = unspent_info,
				mm_map       = mm_map,
				**d) for idx, d in enumerate(txdata))
