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
tx.new: new transaction class
"""

from ..globalvars import *
from ..opts import opt
from .base import Base
from ..globalvars import gc
from ..color import pink,yellow
from ..obj import get_obj,MMGenList
from ..util import msg,qmsg,fmt,die,suf,remove_dups,get_extension
from ..addr import (
	is_mmgen_id,
	MMGenAddrType,
	CoinAddr,
	is_mmgen_addrtype,
	is_coin_addr,
	is_addrlist_id
)

def mmaddr2coinaddr(mmaddr,ad_w,ad_f,proto):

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
		return '\n' + fmt(messages[k],indent='  ')

	# assume mmaddr has already been checked
	coin_addr = ad_w.mmaddr2coinaddr(mmaddr)

	if not coin_addr:
		if ad_f:
			coin_addr = ad_f.mmaddr2coinaddr(mmaddr)
			if coin_addr:
				msg(wmsg('addr_in_addrfile_only'))
				from ..ui import keypress_confirm
				if not (opt.yes or keypress_confirm('Continue anyway?')):
					sys.exit(1)
			else:
				die(2,wmsg('addr_not_found'))
		else:
			die(2,wmsg('addr_not_found_no_addrfile'))

	return CoinAddr(proto,coin_addr)

class New(Base):

	fee_is_approximate = False
	msg_low_coin = 'Selected outputs insufficient to fund this transaction ({} {} needed)'
	msg_wallet_low_coin = 'Wallet has insufficient funds for this transaction ({} {} needed)'
	msg_no_change_output = """
		ERROR: No change address specified.  If you wish to create a transaction with
		only one output, specify a single output address with no {} amount
	"""
	chg_autoselected = False

	def update_output_amt(self,idx,amt):
		o = self.outputs[idx]._asdict()
		o['amt'] = amt
		self.outputs[idx] = self.Output(self.proto,**o)

	def add_mmaddrs_to_outputs(self,ad_w,ad_f):
		a = [e.addr for e in self.outputs]
		d = ad_w.make_reverse_dict(a)
		if ad_f:
			d.update(ad_f.make_reverse_dict(a))
		for e in self.outputs:
			if e.addr and e.addr in d:
				e.mmid,f = d[e.addr]
				if f:
					e.comment = f

	def check_dup_addrs(self,io_str):
		assert io_str in ('inputs','outputs')
		addrs = [e.addr for e in getattr(self,io_str)]
		if len(addrs) != len(set(addrs)):
			die(2,f'{addrs}: duplicate address in transaction {io_str}')

	# given tx size and absolute fee or fee spec, return absolute fee
	# relative fee is N+<first letter of unit name>
	def feespec2abs(self,fee_arg,tx_size):
		fee = get_obj(self.proto.coin_amt,num=fee_arg,silent=True)
		if fee:
			return fee
		else:
			import re
			units = {u[0]:u for u in self.proto.coin_amt.units}
			pat = re.compile(r'([1-9][0-9]*)({})'.format('|'.join(units)))
			if pat.match(fee_arg):
				amt,unit = pat.match(fee_arg).groups()
				return self.fee_rel2abs(tx_size,units,int(amt),unit)
		return False

	def get_usr_fee_interactive(self,fee=None,desc='Starting'):
		abs_fee = None
		from ..ui import line_input
		while True:
			if fee:
				abs_fee = self.convert_and_check_fee(fee,desc)
			if abs_fee:
				prompt = '{} TX fee{}: {}{} {} ({} {})\n'.format(
						desc,
						(f' (after {opt.fee_adjust:.2f}X adjustment)'
							if opt.fee_adjust != 1 and desc.startswith('Network-estimated')
								else ''),
						('','≈')[self.fee_is_approximate],
						abs_fee.hl(),
						self.coin,
						pink(str(self.fee_abs2rel(abs_fee))),
						self.rel_fee_disp)
				from ..ui import keypress_confirm
				if opt.yes or keypress_confirm(prompt+'OK?',default_yes=True):
					if opt.yes:
						msg(prompt)
					return abs_fee
			fee = line_input(self.usr_fee_prompt)
			desc = 'User-selected'

	# we don't know fee yet, so perform preliminary check with fee == 0
	async def precheck_sufficient_funds(self,inputs_sum,sel_unspent,outputs_sum):
		if self.twuo.total < outputs_sum:
			msg(self.msg_wallet_low_coin.format(outputs_sum-inputs_sum,self.dcoin))
			return False
		if inputs_sum < outputs_sum:
			msg(self.msg_low_coin.format(outputs_sum-inputs_sum,self.dcoin))
			return False
		return True

	async def get_fee_from_user(self,have_estimate_fail=[]):

		if opt.fee:
			desc = 'User-selected'
			start_fee = opt.fee
		else:
			desc = 'Network-estimated ({}, {} conf{})'.format(
				opt.fee_estimate_mode.upper(),
				pink(str(opt.fee_estimate_confs)),
				suf(opt.fee_estimate_confs) )
			fee_per_kb,fe_type = await self.get_rel_fee_from_network()

			if fee_per_kb < 0:
				if not have_estimate_fail:
					msg(self.fee_fail_fs.format(c=opt.fee_estimate_confs,t=fe_type))
					have_estimate_fail.append(True)
				start_fee = None
			else:
				start_fee = self.fee_est2abs(fee_per_kb,fe_type)

		return self.get_usr_fee_interactive(start_fee,desc=desc)

	def add_output(self,coinaddr,amt,is_chg=None):
		self.outputs.append(self.Output(self.proto,addr=coinaddr,amt=amt,is_chg=is_chg))

	async def process_cmd_arg(self,arg_in,ad_f,ad_w):

		arg,amt = arg_in.split(',',1) if ',' in arg_in else (arg_in,None)

		if is_mmgen_id(self.proto,arg):
			coin_addr = mmaddr2coinaddr(arg,ad_w,ad_f,self.proto)
		elif is_coin_addr(self.proto,arg):
			coin_addr = CoinAddr(self.proto,arg)
		elif is_mmgen_addrtype(self.proto,arg) or is_addrlist_id(self.proto,arg):
			if self.proto.base_proto_coin != 'BTC':
				die(2,f'Change addresses not supported for {self.proto.name} protocol')

			from ..tw.addresses import TwAddresses
			al = await TwAddresses(self.proto,get_data=True)

			if is_mmgen_addrtype(self.proto,arg):
				arg = MMGenAddrType(self.proto,arg)
				res = al.get_change_address_by_addrtype(arg)
				desc = 'of address type'
			else:
				res = al.get_change_address(arg)
				desc = 'from address list'

			if res:
				coin_addr = res.addr
				self.chg_autoselected = True
			else:
				die(2,'Tracking wallet contains no {t}addresses {d} {a!r}'.format(
					t = ('unused ','')[res is None],
					d = desc,
					a = arg ))
		else:
			die(2,f'{arg_in}: invalid command-line argument')

		if not (amt or self.chg_idx is None):
			die(2,'ERROR: More than one change address {} on command line'.format(
				'requested' if self.chg_autoselected else 'listed'))

		self.add_output(coin_addr,self.proto.coin_amt(amt or '0'),is_chg=not amt)

	async def process_cmd_args(self,cmd_args,ad_f,ad_w):

		for a in cmd_args:
			await self.process_cmd_arg(a,ad_f,ad_w)

		if self.chg_idx is None:
			die(2,(
				fmt( self.msg_no_change_output.format(self.dcoin) ).strip()
					if len(self.outputs) == 1 else
				'ERROR: No change output specified' ))

		if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
			die(2,f'{gc.proj_name} Segwit address requested on the command line, '
					+ 'but Segwit is not active on this chain')

		if not self.outputs:
			die(2,'At least one output must be specified on the command line')

	async def get_outputs_from_cmdline(self,cmd_args):
		from ..addrdata import AddrData,TwAddrData
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
			ad_f.add(AddrList( self.proto, addrfile ))

		ad_w = await TwAddrData(self.proto,twctl=self.twctl)

		await self.process_cmd_args(cmd_args,ad_f,ad_w)

		self.add_mmaddrs_to_outputs(ad_w,ad_f)
		self.check_dup_addrs('outputs')

		if self.chg_output is not None:
			if self.chg_autoselected:
				self.confirm_autoselected_addr(self.chg_output)
			elif len(self.outputs) > 1:
				await self.warn_chg_addr_used(self.chg_output)

	def confirm_autoselected_addr(self,chg):
		from ..ui import keypress_confirm
		if not keypress_confirm(
				'Using {a} as {b} address. OK?'.format(
					a = chg.mmid.hl(),
					b = 'single output' if len(self.outputs) == 1 else 'change' ),
				default_yes = True ):
			die(1,'Exiting at user request')

	async def warn_chg_addr_used(self,chg):
		from ..tw.addresses import TwAddresses
		if (await TwAddresses(self.proto,get_data=True)).is_used(chg.addr):
			from ..ui import keypress_confirm
			if not keypress_confirm(
					'{a} {b} {c}\n{d}'.format(
						a = yellow(f'Requested change address'),
						b = (chg.mmid or chg.addr).hl(),
						c = yellow('is already used!'),
						d = yellow('Address reuse harms your privacy and security. Continue anyway? (y/N): ')
					),
					complete_prompt = True,
					default_yes = False ):
				die(1,'Exiting at user request')

	# inputs methods
	def select_unspent(self,unspent):
		prompt = 'Enter a range or space-separated list of outputs to spend: '
		from ..ui import line_input
		while True:
			reply = line_input(prompt).strip()
			if reply:
				from ..addrlist import AddrIdxList
				selected = get_obj(AddrIdxList, fmt_str=','.join(reply.split()) )
				if selected:
					if selected[-1] <= len(unspent):
						return selected
					msg(f'Unspent output number must be <= {len(unspent)}')

	def select_unspent_cmdline(self,unspent):

		def idx2num(idx):
			uo = unspent[idx]
			mmid_disp = f' ({uo.twmmid})' if uo.twmmid.type == 'mmgen' else ''
			msg(f'Adding input: {idx + 1} {uo.addr}{mmid_disp}')
			return idx + 1

		def get_uo_nums():
			for addr in opt.inputs.split(','):
				if is_mmgen_id(self.proto,addr):
					attr = 'twmmid'
				elif is_coin_addr(self.proto,addr):
					attr = 'addr'
				else:
					die(1,f'{addr!r}: not an MMGen ID or {self.coin} address')

				found = False
				for idx in range(len(unspent)):
					if getattr(unspent[idx],attr) == addr:
						yield idx2num(idx)
						found = True

				if not found:
					die(1,f'{addr!r}: address not found in tracking wallet')

		return set(get_uo_nums()) # silently discard duplicates

	def copy_inputs_from_tw(self,tw_unspent_data):
		def gen_inputs():
			for d in tw_unspent_data:
				i = self.Input(
					self.proto,
					**{attr:getattr(d,attr) for attr in d.__dict__ if attr in self.Input.tw_copy_attrs} )
				if d.twmmid.type == 'mmgen':
					i.mmid = d.twmmid # twmmid -> mmid
				yield i
		self.inputs = type(self.inputs)(self,list(gen_inputs()))

	def warn_insufficient_funds(self,funds_left):
		msg(self.msg_low_coin.format(self.proto.coin_amt(-funds_left).hl(),self.coin))

	async def get_funds_left(self,fee,outputs_sum):
		return self.sum_inputs() - outputs_sum - fee

	async def get_inputs_from_user(self,outputs_sum):

		while True:
			us_f = self.select_unspent_cmdline if opt.inputs else self.select_unspent
			sel_nums = us_f(self.twuo.data)

			msg(f'Selected output{suf(sel_nums)}: {{}}'.format(' '.join(str(n) for n in sel_nums)))
			sel_unspent = MMGenList(self.twuo.data[i-1] for i in sel_nums)

			inputs_sum = sum(s.amt for s in sel_unspent)
			if not await self.precheck_sufficient_funds(inputs_sum,sel_unspent,outputs_sum):
				continue

			self.copy_inputs_from_tw(sel_unspent)  # makes self.inputs

			self.usr_fee = await self.get_fee_from_user()

			funds_left = await self.get_funds_left(self.usr_fee,outputs_sum)

			if funds_left >= 0:
				p = self.final_inputs_ok_msg(funds_left)
				from ..ui import keypress_confirm
				if opt.yes or keypress_confirm(p+'. OK?',default_yes=True):
					if opt.yes:
						msg(p)
					return funds_left
			else:
				self.warn_insufficient_funds(funds_left)

	async def create(self,cmd_args,locktime=None,do_info=False,caller='txcreate'):

		assert isinstance( locktime, (int,type(None)) ), 'locktime must be of type int'

		from ..tw.unspent import TwUnspentOutputs

		if opt.comment_file:
			self.add_comment(opt.comment_file)

		twuo_addrs = await self.get_input_addrs_from_cmdline()

		self.twuo = await TwUnspentOutputs(self.proto,minconf=opt.minconf,addrs=twuo_addrs)
		await self.twuo.get_data()

		if not do_info:
			await self.get_outputs_from_cmdline(cmd_args)

		from ..ui import do_license_msg
		do_license_msg()

		if not opt.inputs:
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

		if not opt.yes:
			self.add_comment()  # edits an existing comment

		await self.create_serialized(locktime=locktime) # creates self.txid too

		self.add_timestamp()
		self.add_blockcount()
		self.chain = self.proto.chain_name
		self.check_fee()

		qmsg('Transaction successfully created')

		from . import UnsignedTX
		new = UnsignedTX(data=self.__dict__)

		if not opt.yes:
			new.info.view_with_prompt('View transaction details?')

		del new.twuo.twctl
		return new
