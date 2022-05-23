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
tool/rpc.py: JSON/RPC routines for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base,options_annot_str
from ..tw.common import TwCommon

class tool_cmd(tool_cmd_base):
	"tracking wallet commands using the JSON-RPC interface"

	need_proto = True
	need_amt = True

	async def daemon_version(self):
		"print coin daemon version"
		from ..rpc import rpc_init
		r = await rpc_init( self.proto, ignore_daemon_version=True )
		return f'{r.daemon.coind_name} version {r.daemon_version} ({r.daemon_version_str})'

	async def getbalance(self,minconf=1,quiet=False,pager=False):
		"list confirmed/unconfirmed, spendable/unspendable balances in tracking wallet"
		from ..tw.bal import TwGetBalance
		return (await TwGetBalance(self.proto,minconf,quiet)).format()

	async def listaddress(self,
			mmgen_addr:str,
			minconf     = 1,
			pager       = False,
			showempty   = True,
			showbtcaddr = True,
			age_fmt: options_annot_str(TwCommon.age_fmts) = 'confs' ):
		"list the specified MMGen address and its balance"

		return await self.listaddresses(
			mmgen_addrs  = mmgen_addr,
			minconf      = minconf,
			pager        = pager,
			showempty    = showempty,
			showbtcaddrs = showbtcaddr,
			age_fmt      = age_fmt )

	async def listaddresses(self,
			mmgen_addrs:'(range or list)' = '',
			minconf      = 1,
			showempty    = False,
			pager        = False,
			showbtcaddrs = True,
			all_labels   = False,
			sort: options_annot_str(['reverse','age']) = '',
			age_fmt: options_annot_str(TwCommon.age_fmts) = 'confs' ):
		"list MMGen addresses and their balances"

		show_age = bool(age_fmt)

		if sort:
			sort = set(sort.split(','))
			sort_params = {'reverse','age'}
			if not sort.issubset( sort_params ):
				from ..util import die
				die(1,"The sort option takes the following parameters: '{}'".format( "','".join(sort_params) ))

		usr_addr_list = []
		if mmgen_addrs:
			a = mmgen_addrs.rsplit(':',1)
			if len(a) != 2:
				from ..util import die
				die(1,
					f'{mmgen_addrs}: invalid address list argument ' +
					'(must be in form <seed ID>:[<type>:]<idx list>)' )
			from ..addr import MMGenID
			from ..addrlist import AddrIdxList
			usr_addr_list = [MMGenID(self.proto,f'{a[0]}:{i}') for i in AddrIdxList(a[1])]

		from ..tw.addrs import TwAddrList
		al = await TwAddrList( self.proto, usr_addr_list, minconf, showempty, showbtcaddrs, all_labels )
		if not al:
			from ..util import die
			die(0,('No tracked addresses with balances!','No tracked addresses!')[showempty])
		return await al.format( showbtcaddrs, sort, show_age, age_fmt or 'confs' )

	async def twops(self,
			obj,pager,reverse,wide,sort,age_fmt,show_mmid,wide_show_confs,interactive):

		obj.reverse = reverse
		obj.age_fmt = age_fmt
		obj.show_mmid = show_mmid

		await obj.get_data(sort_key=sort,reverse_sort=reverse)

		if interactive:
			await obj.view_and_sort()
			return True
		elif wide:
			return await obj.format_for_printing( color=True, show_confs=wide_show_confs )
		else:
			return await obj.format_for_display()

	async def twview(self,
			pager           = False,
			reverse         = False,
			wide            = False,
			minconf         = 1,
			sort            = 'age',
			age_fmt: options_annot_str(TwCommon.age_fmts) = 'confs',
			show_mmid       = True,
			wide_show_confs = True,
			interactive     = False ):
		"view tracking wallet unspent outputs"

		from ..tw.unspent import TwUnspentOutputs
		obj = await TwUnspentOutputs(self.proto,minconf=minconf)
		ret = await self.twops(
			obj,pager,reverse,wide,sort,age_fmt,show_mmid,wide_show_confs,interactive)
		del obj.wallet
		return ret

	async def add_label(self,mmgen_or_coin_addr:str,label:str):
		"add descriptive label for address in tracking wallet"
		from ..tw.ctl import TrackingWallet
		await (await TrackingWallet(self.proto,mode='w')).add_label( mmgen_or_coin_addr, label, on_fail='raise' )
		return True

	async def remove_label(self,mmgen_or_coin_addr:str):
		"remove descriptive label for address in tracking wallet"
		await self.add_label( mmgen_or_coin_addr, '' )
		return True

	async def remove_address(self,mmgen_or_coin_addr:str):
		"remove an address from tracking wallet"
		from ..tw.ctl import TrackingWallet
		ret = await (await TrackingWallet(self.proto,mode='w')).remove_address(mmgen_or_coin_addr) # returns None on failure
		if ret:
			from ..util import msg
			msg(f'Address {ret!r} deleted from tracking wallet')
		return ret
