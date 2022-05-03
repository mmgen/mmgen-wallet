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
tx.new: new transaction class
"""

from ..globalvars import *
from ..opts import opt
from .base import Base
from ..color import pink
from ..obj import get_obj
from ..util import msg,qmsg,fmt,die,suf,remove_dups,get_extension,keypress_confirm,do_license_msg,line_input
from ..addr import is_mmgen_id,CoinAddr,is_coin_addr

def mmaddr2coinaddr(mmaddr,ad_w,ad_f,proto):

	def wmsg(k):
		messages = {
			'addr_in_addrfile_only': f"""
				Warning: output address {mmaddr} is not in the tracking wallet, which
				means its balance will not be tracked.  You're strongly advised to import
				the address into your tracking wallet before broadcasting this transaction.
			""",
			'addr_not_found': f"""
				No data for {g.proj_name} address {mmaddr} could be found in either the
				tracking wallet or the supplied address file.  Please import this address
				into your tracking wallet, or supply an address file on the command line.
			""",
			'addr_not_found_no_addrfile': f"""
				No data for {g.proj_name} address {mmaddr} could be found in the tracking
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
					e.label = f

	def check_dup_addrs(self,io_str):
		assert io_str in ('inputs','outputs')
		addrs = [e.addr for e in getattr(self,io_str)]
		if len(addrs) != len(set(addrs)):
			die(2,f'{addrs}: duplicate address in transaction {io_str}')

	# given tx size and absolute fee or fee spec, return absolute fee
	# relative fee is N+<first letter of unit name>
	def feespec2abs(self,tx_fee,tx_size):
		fee = get_obj(self.proto.coin_amt,num=tx_fee,silent=True)
		if fee:
			return fee
		else:
			import re
			units = {u[0]:u for u in self.proto.coin_amt.units}
			pat = re.compile(r'([1-9][0-9]*)({})'.format('|'.join(units)))
			if pat.match(tx_fee):
				amt,unit = pat.match(tx_fee).groups()
				return self.fee_rel2abs(tx_size,units,int(amt),unit)
		return False

	def get_usr_fee_interactive(self,tx_fee=None,desc='Starting'):
		abs_fee = None
		while True:
			if tx_fee:
				abs_fee = self.convert_and_check_fee(tx_fee,desc)
			if abs_fee:
				prompt = '{} TX fee{}: {}{} {} ({} {})\n'.format(
						desc,
						(f' (after {opt.tx_fee_adj:.2f}X adjustment)'
							if opt.tx_fee_adj != 1 and desc.startswith('Network-estimated')
								else ''),
						('','≈')[self.fee_is_approximate],
						abs_fee.hl(),
						self.coin,
						pink(str(self.fee_abs2rel(abs_fee))),
						self.rel_fee_disp)
				if opt.yes or keypress_confirm(prompt+'OK?',default_yes=True):
					if opt.yes:
						msg(prompt)
					return abs_fee
			tx_fee = line_input(self.usr_fee_prompt)
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

		if opt.tx_fee:
			desc = 'User-selected'
			start_fee = opt.tx_fee
		else:
			desc = 'Network-estimated ({}, {} conf{})'.format(
				opt.fee_estimate_mode.upper(),
				pink(str(opt.tx_confs)),
				suf(opt.tx_confs) )
			fee_per_kb,fe_type = await self.get_rel_fee_from_network()

			if fee_per_kb < 0:
				if not have_estimate_fail:
					msg(self.fee_fail_fs.format(c=opt.tx_confs,t=fe_type))
					have_estimate_fail.append(True)
				start_fee = None
			else:
				start_fee = self.fee_est2abs(fee_per_kb,fe_type)

		return self.get_usr_fee_interactive(start_fee,desc=desc)

	def add_output(self,coinaddr,amt,is_chg=None):
		self.outputs.append(self.Output(self.proto,addr=coinaddr,amt=amt,is_chg=is_chg))

	def process_cmd_arg(self,arg,ad_f,ad_w):

		def add_output_chk(addr,amt,err_desc):
			if not amt and self.get_chg_output_idx() != None:
				die(2,'ERROR: More than one change address listed on command line')
			if is_mmgen_id(self.proto,addr) or is_coin_addr(self.proto,addr):
				coin_addr = ( mmaddr2coinaddr(addr,ad_w,ad_f,self.proto) if is_mmgen_id(self.proto,addr)
								else CoinAddr(self.proto,addr) )
				self.add_output(coin_addr,self.proto.coin_amt(amt or '0'),is_chg=not amt)
			else:
				die(2,f'{addr}: invalid {err_desc} {{!r}}'.format(f'{addr},{amt}' if amt else addr))

		if ',' in arg:
			addr,amt = arg.split(',',1)
			add_output_chk(addr,amt,'coin argument in command-line argument')
		else:
			add_output_chk(arg,None,'command-line argument')

	def process_cmd_args(self,cmd_args,ad_f,ad_w):

		for a in cmd_args:
			self.process_cmd_arg(a,ad_f,ad_w)

		if self.get_chg_output_idx() == None:
			die(2,(
				fmt( self.msg_no_change_output.format(self.dcoin) ).strip()
					if len(self.outputs) == 1 else
				'ERROR: No change output specified' ))

		if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
			die(2,f'{g.proj_name} Segwit address requested on the command line, '
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
		for a in addrfiles:
			check_infile(a)
			ad_f.add(AddrList(self.proto,a))

		ad_w = await TwAddrData(self.proto,wallet=self.tw)

		self.process_cmd_args(cmd_args,ad_f,ad_w)

		self.add_mmaddrs_to_outputs(ad_w,ad_f)
		self.check_dup_addrs('outputs')

	# inputs methods
	def select_unspent(self,unspent):
		prompt = 'Enter a range or space-separated list of outputs to spend: '
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
			sel_nums = us_f(self.twuo.unspent)

			msg(f'Selected output{suf(sel_nums)}: {{}}'.format(' '.join(str(n) for n in sel_nums)))
			sel_unspent = self.twuo.MMGenTwOutputList([self.twuo.unspent[i-1] for i in sel_nums])

			inputs_sum = sum(s.amt for s in sel_unspent)
			if not await self.precheck_sufficient_funds(inputs_sum,sel_unspent,outputs_sum):
				continue

			self.copy_inputs_from_tw(sel_unspent)  # makes self.inputs

			self.usr_fee = await self.get_fee_from_user()

			funds_left = await self.get_funds_left(self.usr_fee,outputs_sum)

			if funds_left >= 0:
				p = self.final_inputs_ok_msg(funds_left)
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

		twuo_addrs = await self.get_cmdline_input_addrs()

		self.twuo = await TwUnspentOutputs(self.proto,minconf=opt.minconf,addrs=twuo_addrs)
		await self.twuo.get_unspent_data()

		if not do_info:
			await self.get_outputs_from_cmdline(cmd_args)

		do_license_msg()

		if not opt.inputs:
			await self.twuo.view_and_sort(self)

		self.twuo.display_total()

		if do_info:
			del self.twuo.wallet
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

		del new.twuo.wallet
		return new
