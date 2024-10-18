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
proto.btc.misc: miscellaneous functions for Bitcoin base protocol
"""

from ...util import msg, msg_r

async def scantxoutset(cfg, rpc, descriptor_list):

	import asyncio

	async def do_scan():
		return await rpc.call(
			'scantxoutset',
			'start',
			descriptor_list,
			timeout = 720) # call may take several minutes to complete

	async def do_status():

		CR = '\n' if cfg.test_suite else '\r'
		sleep_secs = 0.1 if cfg.test_suite else 2
		m = f'{CR}Scanning UTXO set: '
		msg_r(m + '0% completed ')

		while True:
			await asyncio.sleep(sleep_secs)
			res = await rpc.call('scantxoutset', 'status')
			if res:
				msg_r(m + f'{res["progress"]}% completed ')
			if task1.done():
				msg(m + '100% completed')
				return

	res = await rpc.call('scantxoutset', 'status')
	if res and res.get('progress'):
		msg_r('Aborting scan in progress...')
		await rpc.call('scantxoutset', 'abort')
		await asyncio.sleep(1)
		msg('done')

	if rpc.backend.name == 'aiohttp':
		task1 = asyncio.create_task(do_scan())
		task2 = asyncio.create_task(do_status())
		ret = await task1
		await task2
	else:
		msg_r('Scanning UTXO set, this could take several minutes...')
		ret = await do_scan()
		msg('done')

	return ret
