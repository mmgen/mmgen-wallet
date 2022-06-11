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
base_proto.bitcoin.twctl: Bitcoin base protocol tracking wallet control class
"""

from ....globalvars import g
from ....tw.ctl import TrackingWallet
from ....util import msg,msg_r,rmsg,vmsg,die,suf,fmt_list,write_mode

class BitcoinTrackingWallet(TrackingWallet):

	def init_empty(self):
		self.data = { 'coin': self.proto.coin, 'addresses': {} }

	def upgrade_wallet_maybe(self):
		pass

	async def rpc_get_balance(self,addr):
		raise NotImplementedError('not implemented')

	@write_mode
	async def import_address(self,addr,label): # rescan is True by default, so set to False
		return await self.rpc.call('importaddress',addr,label,False)

	@write_mode
	def batch_import_address(self,arg_list):   # rescan is True by default, so set to False
		return self.rpc.batch_call('importaddress',[a+(False,) for a in arg_list])

	@write_mode
	async def remove_address(self,addr):
		raise NotImplementedError(f'address removal not implemented for coin {self.proto.coin}')

	@write_mode
	async def set_label(self,coinaddr,lbl):
		args = self.rpc.daemon.set_label_args( self.rpc, coinaddr, lbl )
		try:
			return await self.rpc.call(*args)
		except Exception as e:
			rmsg(e.args[0])
			return False

	@write_mode
	async def rescan_blockchain(self,start,stop):

		start = start or 0
		endless = stop == None
		CR = '\n' if g.test_suite else '\r'

		if not ( start >= 0 and (stop if stop is not None else start) >= start ):
			die(1,f'{start} {stop}: invalid range')

		async def do_scan(chunks,tip):
			res = None
			for a,b in chunks:
				msg_r(f'{CR}Scanning blocks {a}-{b} ')
				res = await self.rpc.call('rescanblockchain',a,b,timeout=7200)
				if res['start_height'] != a or res['stop_height'] != b:
					die(1,f'\nAn error occurred in block range {a}-{b}')
			msg('')
			return b if res else tip

		def gen_chunks(start,stop,tip):
			n = start
			if endless:
				stop = tip
			elif stop > tip:
				die(1,f'{stop}: stop value is higher than chain tip')

			while n <= stop:
				yield ( n, min(n+99,stop) )
				n += 100

		last_block = await do_scan(gen_chunks(start,stop,self.rpc.blockcount),self.rpc.blockcount)

		if endless:
			tip = await self.rpc.call('getblockcount')
			while last_block < tip:
				last_block = await do_scan(gen_chunks(last_block+1,tip),tip)
				tip = await self.rpc.call('getblockcount')

		msg('Done')

	@write_mode
	async def rescan_address(self,addrspec):
		res = await self.resolve_address(addrspec,None)
		if not res:
			return False
		return await self.rescan_addresses([res.coinaddr])

	@write_mode
	async def rescan_addresses(self,coin_addrs):

		import asyncio

		async def do_scan():
			return await self.rpc.call(
				'scantxoutset',
				'start',
				[f'addr({a})' for a in coin_addrs],
				timeout = 720 ) # call may take several minutes to complete

		async def do_status():
			m = f'{CR}Scanning UTXO set: '
			msg_r(m)
			while True:
				await asyncio.sleep(2)
				res = await self.rpc.call('scantxoutset','status')
				if res:
					msg_r(m + f'{res["progress"]}% completed ')
				if task1.done():
					msg('')
					return

		CR = '\r'

		if self.rpc.backend.name == 'aiohttp':
			task1 = asyncio.create_task( do_scan() )
			task2 = asyncio.create_task( do_status() )
			res = await task1
			await task2
		else:
			msg_r(f'Scanning UTXO set, this could take several minutes...')
			res = await do_scan()
			msg('done')

		if not res['success']:
			msg('UTXO scanning failed or was interrupted')
			return False
		elif res['unspents']:
			blocks = sorted({ i['height'] for i in res['unspents'] })
			msg('Found {} unspent output{} in {} block{}'.format(
				len(res['unspents']),
				suf(res['unspents']),
				len(blocks),
				suf(blocks) ))
			vmsg(f'Blocks to rescan: {fmt_list(blocks,fmt="bare")}')
			for n,block in enumerate(blocks):
				msg_r(f'{CR}Rescanning block: {block} ({n+1}/{len(blocks)})')
				# httplib seems to require fresh connection here, so specify timeout
				await self.rpc.call('rescanblockchain',block,block,timeout=60)
			msg(f'\nAddress balance{suf(coin_addrs)} updated successfully')
			return True
		else:
			msg('Address has no balance' if len(coin_addrs) == 1 else
				'Addresses have no balances' )
			return True
