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
from ..tw.view import TwView
from ..tw.txhistory import TwTxHistory

class tool_cmd(tool_cmd_base):
	"tracking-wallet commands using the JSON-RPC interface"

	need_proto = True
	need_amt = True

	async def daemon_version(self):
		"print coin daemon version"
		from ..rpc import rpc_init
		r = await rpc_init( self.proto, ignore_daemon_version=True )
		return f'{r.daemon.coind_name} version {r.daemon_version} ({r.daemon_version_str})'

	async def getbalance(self,
			minconf: 'minimum number of confirmations' = 1,
			quiet:   'produce quieter output' = False,
			pager:   'send output to pager' = False ):
		"list confirmed/unconfirmed, spendable/unspendable balances in tracking wallet"
		from ..tw.bal import TwGetBalance
		return (await TwGetBalance(self.proto,minconf,quiet)).format()

	async def twops(self,
			obj,pager,reverse,detail,sort,age_fmt,interactive,
			**kwargs ):

		obj.reverse = reverse
		obj.age_fmt = age_fmt
		obj.interactive = interactive

		for k,v in kwargs.items():
			setattr(obj,k,v)

		await obj.get_data(sort_key=sort,reverse_sort=reverse)

		if interactive:
			await obj.view_filter_and_sort()
			return True
		else:
			return await obj.format('detail' if detail else 'squeezed')

	async def twview(self,
			pager:       'send output to pager' = False,
			reverse:     'reverse order of unspent outputs' = False,
			wide:        'display data in wide tabular format' = False,
			minconf:     'minimum number of confirmations' = 1,
			sort:        'unspent output sort order ' + options_annot_str(TwView.sort_funcs) = 'age',
			age_fmt:     'format for the Age/Date column ' + options_annot_str(TwView.age_fmts) = 'confs',
			interactive: 'enable interactive operation' = False,
			show_mmid:   'show MMGen IDs along with coin addresses' = True ):
		"view tracking wallet unspent outputs"

		from ..tw.unspent import TwUnspentOutputs
		obj = await TwUnspentOutputs(self.proto,minconf=minconf)
		ret = await self.twops(
			obj,pager,reverse,wide,sort,age_fmt,interactive,
			show_mmid = show_mmid )
		del obj.wallet
		return ret

	async def txhist(self,
			pager:       'send output to pager' = False,
			reverse:     'reverse order of transactions' = False,
			detail:      'produce detailed, non-tabular output' = False,
			sinceblock:  'display transactions starting from this block' = 0,
			sort:        'transaction sort order ' + options_annot_str(TwTxHistory.sort_funcs) = 'age',
			age_fmt:     'format for the Age/Date column ' + options_annot_str(TwView.age_fmts) = 'confs',
			interactive: 'enable interactive operation' = False ):
		"view transaction history of tracking wallet"

		obj = await TwTxHistory(self.proto,sinceblock=sinceblock)
		return await self.twops(
			obj,pager,reverse,detail,sort,age_fmt,interactive )

	async def listaddress(self,
			mmgen_addr:str,
			wide:         'display data in wide tabular format' = False,
			minconf:      'minimum number of confirmations' = 1,
			showcoinaddr: 'display coin address in addition to MMGen ID' = True,
			age_fmt:      'format for the Age/Date column ' + options_annot_str(TwView.age_fmts) = 'confs' ):
		"list the specified MMGen address in the tracking wallet and its balance"

		return await self.listaddresses(
			mmgen_addrs   = mmgen_addr,
			wide          = wide,
			minconf       = minconf,
			showcoinaddrs = showcoinaddr,
			age_fmt       = age_fmt )

	async def listaddresses(self,
			pager:        'send output to pager' = False,
			reverse:      'reverse order of unspent outputs' = False,
			wide:         'display data in wide tabular format' = False,
			minconf:      'minimum number of confirmations' = 1,
			sort:         'address sort order ' + options_annot_str(['reverse','mmid','addr','amt']) = '',
			age_fmt:      'format for the Age/Date column ' + options_annot_str(TwView.age_fmts) = 'confs',
			interactive:  'enable interactive operation' = False,
			mmgen_addrs:  'hyphenated range or comma-separated list of addresses' = '',
			showcoinaddrs:'display coin addresses in addition to MMGen IDs' = True,
			showempty:    'show addresses with no balances' = True,
			showused:     'show used addresses (tristate: 0=no, 1=yes, 2=all)' = 1,
			all_labels:   'show all addresses with labels' = False ):
		"list MMGen addresses in the tracking wallet and their balances"

		assert showused in (0,1,2), f"‘showused’ must have a value of 0, 1 or 2"

		from ..tw.addresses import TwAddresses
		obj = await TwAddresses(self.proto,minconf=minconf,mmgen_addrs=mmgen_addrs)
		return await self.twops(
			obj,pager,reverse,wide,sort,age_fmt,interactive,
			showcoinaddrs = showcoinaddrs,
			showempty     = showempty,
			showused      = showused,
			all_labels    = all_labels )

	async def add_label(self,mmgen_or_coin_addr:str,label:str):
		"add descriptive label for address in tracking wallet"
		from ..tw.ctl import TrackingWallet
		return await (await TrackingWallet(self.proto,mode='w')).set_comment(mmgen_or_coin_addr,label)

	async def remove_label(self,mmgen_or_coin_addr:str):
		"remove descriptive label for address in tracking wallet"
		await self.add_label( mmgen_or_coin_addr, '' )
		return True

	async def remove_address(self,mmgen_or_coin_addr:str):
		"remove an address from tracking wallet"
		from ..tw.ctl import TrackingWallet
		# returns None on failure:
		ret = await (await TrackingWallet(self.proto,mode='w')).remove_address(mmgen_or_coin_addr)
		if ret:
			from ..util import msg
			msg(f'Address {ret!r} deleted from tracking wallet')
		return ret

	async def resolve_address(self,mmgen_or_coin_addr:str):
		"resolve an MMGen address in the tracking wallet to a coin address or vice-versa"
		from ..tw.ctl import TrackingWallet
		ret = await (await TrackingWallet(self.proto,mode='w')).resolve_address( mmgen_or_coin_addr )
		if ret:
			from ..util import Msg
			from ..addr import is_coin_addr
			return ret.twmmid if is_coin_addr(self.proto,mmgen_or_coin_addr) else ret.coinaddr
		else:
			return False

	async def rescan_address(self,mmgen_or_coin_addr:str):
		"rescan an address in the tracking wallet to update its balance"
		from ..tw.ctl import TrackingWallet
		return await (await TrackingWallet(self.proto,mode='w')).rescan_address( mmgen_or_coin_addr )

	async def rescan_blockchain(self,
			start_block: int = None,
			stop_block: int  = None ):
		"""
		rescan the blockchain to update historical transactions in the tracking wallet

		NOTE:

		  The rescanning process typically takes several hours and may be interrupted
		  using Ctrl-C.  An interrupted rescan may be resumed using the ‘start_block’
		  parameter.
		"""
		from ..tw.ctl import TrackingWallet
		ret = await (await TrackingWallet(self.proto,mode='w')).rescan_blockchain(start_block,stop_block)
		return True

	async def twexport(self,include_amts=True,pretty=False):
		"""
		export a tracking wallet to JSON format

		NOTES:

		  If ‘include_amts’ is true (the default), Ethereum balances will be restored
		  from the dump upon import. For Bitcoin and forks, amount fields in the dump
		  are ignored.

		  If ‘pretty’ is true, JSON will be dumped in human-readable format to allow
		  for editing of comment fields.
		"""
		from ..tw.json import TwJSON
		await TwJSON.Export( self.proto, include_amts=include_amts, pretty=pretty )
		return True

	async def twimport(self,filename:str,ignore_checksum=False,batch=False):
		"""
		restore a tracking wallet from a JSON dump created by ‘twexport’

		NOTES:

		  If comment fields in the JSON dump have been edited, ‘ignore_checksum’ must
		  be set to true.

		  The restored tracking wallet will have correct balances but no record of
		  historical transactions.  These may be restored by running ‘mmgen-tool
		  rescan_blockchain’.
		"""
		from ..tw.json import TwJSON
		await TwJSON.Import( self.proto, filename, ignore_checksum=ignore_checksum, batch=batch )
		return True
