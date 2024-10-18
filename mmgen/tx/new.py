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
tx.new: new transaction class
"""

from collections import namedtuple

from .base import Base
from ..cfg import gc
from ..color import pink, yellow
from ..obj import get_obj, MMGenList
from ..util import msg, fmt, die, suf, remove_dups, get_extension
from ..addr import (
	is_mmgen_id,
	MMGenAddrType,
	MMGenID,
	CoinAddr,
	is_mmgen_addrtype,
	is_coin_addr,
	is_addrlist_id
)

def mmaddr2coinaddr(cfg, mmaddr, ad_w, ad_f, proto):

	def wmsg(k):
		messages = {
			'addr_in_addrfile_only': f"""
				Warning: output address {mmaddr} is not in the tracking wallet, which
				means its balance will not be tracked.  You're strongly advised to import
				the address into your tracking wallet before broadcasting this transaction.
			""",
			'addr_not_found': f"""
				No data for {gc.proj_name} address {mmaddr} could be found in either the
				tracking wallet or the supplied address file.  Please import this address
				into your tracking wallet, or supply an address file on the command line.
			""",
			'addr_not_found_no_addrfile': f"""
				No data for {gc.proj_name} address {mmaddr} could be found in the tracking
				wallet.  Please import this address into your tracking wallet or supply an
				address file for it on the command line.
			"""
		}
		return '\n' + fmt(messages[k], indent='  ')

	# assume mmaddr has already been checked
	coin_addr = ad_w.mmaddr2coinaddr(mmaddr)

	if not coin_addr:
		if ad_f:
			coin_addr = ad_f.mmaddr2coinaddr(mmaddr)
			if coin_addr:
				msg(wmsg('addr_in_addrfile_only'))
				from ..ui import keypress_confirm
				if not (cfg.yes or keypress_confirm(cfg, 'Continue anyway?')):
					import sys
					sys.exit(1)
			else:
				die(2, wmsg('addr_not_found'))
		else:
			die(2, wmsg('addr_not_found_no_addrfile'))

	return CoinAddr(proto, coin_addr)

class New(Base):

	fee_is_approximate = False
	msg_wallet_low_coin = 'Wallet has insufficient funds for this transaction ({} {} needed)'
	msg_no_change_output = """
		ERROR: No change address specified.  If you wish to create a transaction with
		only one output, specify a single output address with no {} amount
	"""
	msg_insufficient_funds = 'Selected outputs insufficient to fund this transaction ({} {} needed)'
	chg_autoselected = False
	_funds_available = namedtuple('funds_available', ['is_positive', 'amt'])

	def warn_insufficient_funds(self, amt, coin):
		msg(self.msg_insufficient_funds.format(amt.hl(), coin))

	def update_output_amt(self, idx, amt):
		o = self.outputs[idx]._asdict()
		o['amt'] = amt
		self.outputs[idx] = self.Output(self.proto, **o)

	def add_mmaddrs_to_outputs(self, ad_w, ad_f):
		a = [e.addr for e in self.outputs]
		d = ad_w.make_reverse_dict(a)
		if ad_f:
			d.update(ad_f.make_reverse_dict(a))
		for e in self.outputs:
			if e.addr and e.addr in d:
				e.mmid, f = d[e.addr]
				if f:
					e.comment = f

	def check_dup_addrs(self, io_str):
		assert io_str in ('inputs', 'outputs')
		addrs = [e.addr for e in getattr(self, io_str)]
		if len(addrs) != len(set(addrs)):
			die(2, f'{addrs}: duplicate address in transaction {io_str}')

	# given tx size and absolute fee or fee spec, return absolute fee
	# relative fee is N+<first letter of unit name>
	def feespec2abs(self, fee_arg, tx_size):

		if type(fee_arg) is self.proto.coin_amt:
			return fee_arg

		if fee := get_obj(self.proto.coin_amt, num=fee_arg, silent=True):
			return fee

		import re
		units = {u[0]:u for u in self.proto.coin_amt.units}
		pat = re.compile(r'([1-9][0-9]*)({})'.format('|'.join(units)))
		if pat.match(fee_arg):
			amt, unit = pat.match(fee_arg).groups()
			return self.fee_rel2abs(tx_size, units, int(amt), unit)

		return False

	def get_usr_fee_interactive(self, fee=None, desc='Starting'):
		abs_fee = None
		from ..ui import line_input
		while True:
			if fee:
				abs_fee = self.convert_and_check_fee(fee, desc)
			if abs_fee:
				prompt = '{a} TX fee{b}: {c}{d} {e} ({f} {g})\n'.format(
					a = desc,
					b = (f' (after {self.cfg.fee_adjust:.2f}X adjustment)'
							if self.cfg.fee_adjust != 1 and desc.startswith('Network-estimated')
								else ''),
					c = ('', '≈')[self.fee_is_approximate],
					d = abs_fee.hl(),
					e = self.coin,
					f = pink(self.fee_abs2rel(abs_fee)),
					g = self.rel_fee_disp)
				from ..ui import keypress_confirm
				if self.cfg.yes or keypress_confirm(self.cfg, prompt+'OK?', default_yes=True):
					if self.cfg.yes:
						msg(prompt)
					return abs_fee
			fee = line_input(self.cfg, self.usr_fee_prompt)
			desc = 'User-selected'

	# we don't know fee yet, so perform preliminary check with fee == 0
	async def precheck_sufficient_funds(self, inputs_sum, sel_unspent, outputs_sum):
		if self.twuo.total < outputs_sum:
			msg(self.msg_wallet_low_coin.format(outputs_sum-inputs_sum, self.dcoin))
			return False
		if inputs_sum < outputs_sum:
			self.warn_insufficient_funds(outputs_sum - inputs_sum, self.dcoin)
			return False
		return True

	def add_output(self, coinaddr, amt, is_chg=None):
		self.outputs.append(self.Output(self.proto, addr=coinaddr, amt=amt, is_chg=is_chg))

	def parse_cmd_arg(self, arg_in, ad_f, ad_w):

		_pa = namedtuple('parsed_txcreate_cmdline_arg', ['arg', 'mmid', 'coin_addr', 'amt'])

		arg, amt = arg_in.split(',', 1) if ',' in arg_in else (arg_in, None)

		if mmid := get_obj(MMGenID, proto=self.proto, id_str=arg, silent=True):
			coin_addr = mmaddr2coinaddr(self.cfg, arg, ad_w, ad_f, self.proto)
		elif is_coin_addr(self.proto, arg):
			coin_addr = CoinAddr(self.proto, arg)
		elif is_mmgen_addrtype(self.proto, arg) or is_addrlist_id(self.proto, arg):
			if self.proto.base_proto_coin != 'BTC':
				die(2, f'Change addresses not supported for {self.proto.name} protocol')
			self.chg_autoselected = True
			coin_addr = None
		else:
			die(2, f'{arg_in}: invalid command-line argument')

		return _pa(arg, mmid, coin_addr, amt)

	async def process_cmd_args(self, cmd_args, ad_f, ad_w):

		async def get_autochg_addr(arg, parsed_args):
			from ..tw.addresses import TwAddresses
			al = await TwAddresses(self.cfg, self.proto, get_data=True)
			exclude = [a.mmid for a in parsed_args if a.mmid]

			if is_mmgen_addrtype(self.proto, arg):
				res = al.get_change_address_by_addrtype(MMGenAddrType(self.proto, arg), exclude=exclude)
				desc = 'of address type'
			else:
				res = al.get_change_address(arg, exclude=exclude)
				desc = 'from address list'

			if res:
				return res

			die(2, 'Tracking wallet contains no {t}addresses {d} {a!r}'.format(
				t = '' if res is None else 'unused ',
				d = desc,
				a = arg))

		parsed_args = [self.parse_cmd_arg(a, ad_f, ad_w) for a in cmd_args]

		chg_args = [a for a in parsed_args if not (a.amt and a.coin_addr)]

		if len(chg_args) > 1:
			desc = 'requested' if self.chg_autoselected else 'listed'
			die(2, f'ERROR: More than one change address {desc} on command line')

		for a in parsed_args:
			self.add_output(
				coinaddr = a.coin_addr or (await get_autochg_addr(a.arg, parsed_args)).addr,
				amt      = self.proto.coin_amt(a.amt or '0'),
				is_chg   = not a.amt)

		if self.chg_idx is None:
			die(2,
				fmt(self.msg_no_change_output.format(self.dcoin)).strip()
					if len(self.outputs) == 1 else
				'ERROR: No change output specified')

		if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
			die(2,
				f'{gc.proj_name} Segwit address requested on the command line, '
				'but Segwit is not active on this chain')

		if not self.outputs:
			die(2, 'At least one output must be specified on the command line')

	async def get_outputs_from_cmdline(self, cmd_args):
		from ..addrdata import AddrData, TwAddrData
		from ..addrlist import AddrList
		from ..addrfile import AddrFile
		addrfiles = remove_dups(
			tuple(a for a in cmd_args if get_extension(a) == AddrFile.ext),
			desc = 'command line',
			edesc = 'argument',
		)
		cmd_args  = remove_dups(
			tuple(a for a in cmd_args if a not in addrfiles),
			desc = 'command line',
			edesc = 'argument',
		)

		ad_f = AddrData(self.proto)
		from ..fileutil import check_infile
		for addrfile in addrfiles:
			check_infile(addrfile)
			ad_f.add(AddrList(self.cfg, self.proto, addrfile))

		ad_w = await TwAddrData(self.cfg, self.proto, twctl=self.twctl)

		await self.process_cmd_args(cmd_args, ad_f, ad_w)

		self.add_mmaddrs_to_outputs(ad_w, ad_f)
		self.check_dup_addrs('outputs')

		if self.chg_output is not None:
			if self.chg_autoselected:
				self.confirm_autoselected_addr(self.chg_output)
			elif len(self.outputs) > 1:
				await self.warn_chg_addr_used(self.chg_output)

	def confirm_autoselected_addr(self, chg):
		from ..ui import keypress_confirm
		if not keypress_confirm(
				self.cfg,
				'Using {a} as {b} address. OK?'.format(
					a = chg.mmid.hl(),
					b = 'single output' if len(self.outputs) == 1 else 'change'),
				default_yes = True):
			die(1, 'Exiting at user request')

	async def warn_chg_addr_used(self, chg):
		from ..tw.addresses import TwAddresses
		if (await TwAddresses(self.cfg, self.proto, get_data=True)).is_used(chg.addr):
			from ..ui import keypress_confirm
			if not keypress_confirm(
					self.cfg,
					'{a} {b} {c}\n{d}'.format(
						a = yellow('Requested change address'),
						b = chg.mmid.hl() if chg.mmid else chg.addr.hl(chg.addr.view_pref),
						c = yellow('is already used!'),
						d = yellow('Address reuse harms your privacy and security. Continue anyway? (y/N): ')
					),
					complete_prompt = True,
					default_yes = False):
				die(1, 'Exiting at user request')

	# inputs methods
	def select_unspent(self, unspent):
		prompt = 'Enter a range or space-separated list of outputs to spend: '
		from ..ui import line_input
		while True:
			reply = line_input(self.cfg, prompt).strip()
			if reply:
				from ..addrlist import AddrIdxList
				selected = get_obj(AddrIdxList, fmt_str=','.join(reply.split()))
				if selected:
					if selected[-1] <= len(unspent):
						return selected
					msg(f'Unspent output number must be <= {len(unspent)}')

	def select_unspent_cmdline(self, unspent):

		def idx2num(idx):
			uo = unspent[idx]
			mmid_disp = f' ({uo.twmmid})' if uo.twmmid.type == 'mmgen' else ''
			msg(f'Adding input: {idx + 1} {uo.addr}{mmid_disp}')
			return idx + 1

		def get_uo_nums():
			for addr in self.cfg.inputs.split(','):
				if is_mmgen_id(self.proto, addr):
					attr = 'twmmid'
				elif is_coin_addr(self.proto, addr):
					attr = 'addr'
				else:
					die(1, f'{addr!r}: not an MMGen ID or {self.coin} address')

				found = False
				for idx, us in enumerate(unspent):
					if getattr(us, attr) == addr:
						yield idx2num(idx)
						found = True

				if not found:
					die(1, f'{addr!r}: address not found in tracking wallet')

		return set(get_uo_nums()) # silently discard duplicates

	def copy_inputs_from_tw(self, tw_unspent_data):
		def gen_inputs():
			for d in tw_unspent_data:
				i = self.Input(
					self.proto,
					**{attr:getattr(d, attr) for attr in d.__dict__ if attr in self.Input.tw_copy_attrs})
				if d.twmmid.type == 'mmgen':
					i.mmid = d.twmmid # twmmid -> mmid
				yield i
		self.inputs = type(self.inputs)(self, list(gen_inputs()))

	async def get_funds_available(self, fee, outputs_sum):
		in_ = self.sum_inputs()
		out = outputs_sum + fee
		return self._funds_available(in_ >= out, in_ - out if in_ >= out else out - in_)

	async def get_inputs_from_user(self, outputs_sum):

		while True:
			us_f = self.select_unspent_cmdline if self.cfg.inputs else self.select_unspent
			sel_nums = us_f(self.twuo.data)

			msg(f'Selected output{suf(sel_nums)}: {{}}'.format(' '.join(str(n) for n in sel_nums)))
			sel_unspent = MMGenList(self.twuo.data[i-1] for i in sel_nums)

			inputs_sum = sum(s.amt for s in sel_unspent)
			if not await self.precheck_sufficient_funds(inputs_sum, sel_unspent, outputs_sum):
				continue

			self.copy_inputs_from_tw(sel_unspent)  # makes self.inputs

			if self.cfg.fee:
				self.usr_fee = self.get_usr_fee_interactive(self.cfg.fee, 'User-selected')
			else:
				fee_per_kb, fe_type = await self.get_rel_fee_from_network()
				self.usr_fee = self.get_usr_fee_interactive(
					None if fee_per_kb is None else self.fee_est2abs(fee_per_kb, fe_type),
					self.network_estimated_fee_label)

			funds = await self.get_funds_available(self.usr_fee, outputs_sum)

			if funds.is_positive:
				p = self.final_inputs_ok_msg(funds.amt)
				from ..ui import keypress_confirm
				if self.cfg.yes or keypress_confirm(self.cfg, p+'. OK?', default_yes=True):
					if self.cfg.yes:
						msg(p)
					return funds.amt
			else:
				self.warn_insufficient_funds(funds.amt, self.coin)

	async def create(self, cmd_args, locktime=None, do_info=False, caller='txcreate'):

		assert isinstance(locktime, (int, type(None))), 'locktime must be of type int'

		from ..tw.unspent import TwUnspentOutputs

		if self.cfg.comment_file:
			self.add_comment(self.cfg.comment_file)

		twuo_addrs = await self.get_input_addrs_from_cmdline()

		self.twuo = await TwUnspentOutputs(self.cfg, self.proto, minconf=self.cfg.minconf, addrs=twuo_addrs)
		await self.twuo.get_data()

		if not do_info:
			await self.get_outputs_from_cmdline(cmd_args)

		from ..ui import do_license_msg
		do_license_msg(self.cfg)

		if not self.cfg.inputs:
			await self.twuo.view_filter_and_sort()

		self.twuo.display_total()

		if do_info:
			del self.twuo.twctl
			import sys
			sys.exit(0)

		outputs_sum = self.sum_outputs()

		msg('Total amount to spend: {}'.format(
			f'{outputs_sum.hl()} {self.dcoin}' if outputs_sum else 'Unknown'
		))

		funds_left = await self.get_inputs_from_user(outputs_sum)

		self.check_non_mmgen_inputs(caller)

		self.update_change_output(funds_left)

		if not self.cfg.yes:
			self.add_comment()  # edits an existing comment

		await self.create_serialized(locktime=locktime) # creates self.txid too

		self.add_timestamp()
		self.add_blockcount()
		self.chain = self.proto.chain_name
		self.check_fee()

		self.cfg._util.qmsg('Transaction successfully created')

		from . import UnsignedTX
		new = UnsignedTX(cfg=self.cfg, data=self.__dict__, automount=self.cfg.autosign)

		if not self.cfg.yes:
			new.info.view_with_prompt('View transaction details?')

		del new.twuo.twctl
		return new
