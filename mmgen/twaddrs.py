#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
twaddrs: Tracking wallet listaddresses class for the MMGen suite
"""

from .color import green
from .util import msg,die,base_proto_subclass
from .base_obj import AsyncInit
from .obj import MMGenList,MMGenDict,TwComment
from .addr import CoinAddr,MMGenID
from .rpc import rpc_init
from .tw import TwCommon,get_tw_label

class TwAddrList(MMGenDict,TwCommon,metaclass=AsyncInit):
	has_age = True

	def __new__(cls,proto,*args,**kwargs):
		return MMGenDict.__new__(base_proto_subclass(cls,proto,'twaddrs'),*args,**kwargs)

	async def __init__(self,proto,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		def check_dup_mmid(acct_labels):
			mmid_prev,err = None,False
			for mmid in sorted(a.mmid for a in acct_labels if a):
				if mmid == mmid_prev:
					err = True
					msg(f'Duplicate MMGen ID ({mmid}) discovered in tracking wallet!\n')
				mmid_prev = mmid
			if err:
				die(4,'Tracking wallet is corrupted!')

		def check_addr_array_lens(acct_pairs):
			err = False
			for label,addrs in acct_pairs:
				if not label: continue
				if len(addrs) != 1:
					err = True
					if len(addrs) == 0:
						msg(f'Label {label!r}: has no associated address!')
					else:
						msg(f'{addrs!r}: more than one {proto.coin} address in account!')
			if err:
				die(4,'Tracking wallet is corrupted!')

		self.rpc   = await rpc_init(proto)
		self.total = proto.coin_amt('0')
		self.proto = proto

		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			if not lbl_id in d: continue  # skip coinbase outputs with missing account
			if d['confirmations'] < minconf: continue
			label = get_tw_label(proto,d[lbl_id])
			if label:
				lm = label.mmid
				if usr_addr_list and (lm not in usr_addr_list):
					continue
				if lm in self:
					if self[lm]['addr'] != d['address']:
						die(2,'duplicate {} address ({}) for this MMGen address! ({})'.format(
							proto.coin,
							d['address'],
							self[lm]['addr'] ))
				else:
					lm.confs = d['confirmations']
					lm.txid = d['txid']
					lm.date = None
					self[lm] = {
						'amt': proto.coin_amt('0'),
						'lbl': label,
						'addr': CoinAddr(proto,d['address']) }
				amt = proto.coin_amt(d['amount'])
				self[lm]['amt'] += amt
				self.total += amt

		# We use listaccounts only for empty addresses, as it shows false positive balances
		if showempty or all_labels:
			# for compatibility with old mmids, must use raw RPC rather than native data for matching
			# args: minconf,watchonly, MUST use keys() so we get list, not dict
			if 'label_api' in self.rpc.caps:
				acct_list = await self.rpc.call('listlabels')
				aa = await self.rpc.batch_call('getaddressesbylabel',[(k,) for k in acct_list])
				acct_addrs = [list(a.keys()) for a in aa]
			else:
				acct_list = list((await self.rpc.call('listaccounts',0,True)).keys()) # raw list, no 'L'
				acct_addrs = await self.rpc.batch_call('getaddressesbyaccount',[(a,) for a in acct_list]) # use raw list here
			acct_labels = MMGenList([get_tw_label(proto,a) for a in acct_list])
			check_dup_mmid(acct_labels)
			assert len(acct_list) == len(acct_addrs),(
				'listaccounts() and getaddressesbyaccount() not equal in length')
			addr_pairs = list(zip(acct_labels,acct_addrs))
			check_addr_array_lens(addr_pairs)
			for label,addr_arr in addr_pairs:
				if not label: continue
				if all_labels and not showempty and not label.comment: continue
				if usr_addr_list and (label.mmid not in usr_addr_list): continue
				if label.mmid not in self:
					self[label.mmid] = { 'amt':proto.coin_amt('0'), 'lbl':label, 'addr':'' }
					if showbtcaddrs:
						self[label.mmid]['addr'] = CoinAddr(proto,addr_arr[0])

	def raw_list(self):
		return [((k if k.type == 'mmgen' else 'Non-MMGen'),self[k]['addr'],self[k]['amt']) for k in self]

	def coinaddr_list(self):
		return [self[k]['addr'] for k in self]

	async def format(self,showbtcaddrs,sort,show_age,age_fmt):
		if not self.has_age:
			show_age = False
		if age_fmt not in self.age_fmts:
			die( 'BadAgeFormat', f'{age_fmt!r}: invalid age format (must be one of {self.age_fmts!r})' )
		fs = '{mid}' + ('',' {addr}')[showbtcaddrs] + ' {cmt} {amt}' + ('',' {age}')[show_age]
		mmaddrs = [k for k in self.keys() if k.type == 'mmgen']
		max_mmid_len = max(len(k) for k in mmaddrs) + 2 if mmaddrs else 10
		max_cmt_width = max(max(v['lbl'].comment.screen_width for v in self.values()),7)
		addr_width = max(len(self[mmid]['addr']) for mmid in self)

		max_fp_len = max([len(a.split('.')[1]) for a in [str(v['amt']) for v in self.values()] if '.' in a] or [1])

		def sort_algo(j):
			if sort and 'age' in sort:
				return '{}_{:>012}_{}'.format(
					j.obj.rsplit(':',1)[0],
					# Hack, but OK for the foreseeable future:
					(1000000000-(j.confs or 0) if hasattr(j,'confs') else 0),
					j.sort_key)
			else:
				return j.sort_key

		mmids = sorted(self,key=sort_algo,reverse=bool(sort and 'reverse' in sort))
		if show_age:
			await self.set_dates(
				self.rpc,
				[o for o in mmids if hasattr(o,'confs')] )

		def gen_output():

			if self.proto.chain_name != 'mainnet':
				yield 'Chain: '+green(self.proto.chain_name.upper())

			yield fs.format(
					mid=MMGenID.fmtc('MMGenID',width=max_mmid_len),
					addr=(CoinAddr.fmtc('ADDRESS',width=addr_width) if showbtcaddrs else None),
					cmt=TwComment.fmtc('COMMENT',width=max_cmt_width+1),
					amt='BALANCE'.ljust(max_fp_len+4),
					age=age_fmt.upper(),
				).rstrip()

			al_id_save = None
			for mmid in mmids:
				if mmid.type == 'mmgen':
					if al_id_save and al_id_save != mmid.obj.al_id:
						yield ''
					al_id_save = mmid.obj.al_id
					mmid_disp = mmid
				else:
					if al_id_save:
						yield ''
						al_id_save = None
					mmid_disp = 'Non-MMGen'
				e = self[mmid]
				yield fs.format(
					mid=MMGenID.fmtc(mmid_disp,width=max_mmid_len,color=True),
					addr=(e['addr'].fmt(color=True,width=addr_width) if showbtcaddrs else None),
					cmt=e['lbl'].comment.fmt(width=max_cmt_width,color=True,nullrepl='-'),
					amt=e['amt'].fmt('4.{}'.format(max(max_fp_len,3)),color=True),
					age=self.age_disp(mmid,age_fmt) if show_age and hasattr(mmid,'confs') else '-'
					).rstrip()

			yield '\nTOTAL: {} {}'.format(
				self.total.hl(color=True),
				self.proto.dcoin )

		return '\n'.join(gen_output())
