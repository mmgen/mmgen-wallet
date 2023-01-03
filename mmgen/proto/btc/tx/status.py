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
proto.btc.tx.status: Bitcoin transaction status class
"""

import time

import mmgen.tx.status as TxBase
from ....opts import opt
from ....util import msg,suf,die,secs_to_dhms

class Status(TxBase.Status):

	async def display(self,usr_req=False):

		tx = self.tx

		class r(object):
			pass

		async def is_in_wallet():
			try:
				ret = await tx.rpc.icall(
					'gettransaction',
					txid              = tx.coin_txid,
					include_watchonly = True,
					verbose           = False )
			except:
				return False
			if ret.get('confirmations',0) > 0:
				r.confs = ret['confirmations']
				return True
			else:
				return False

		async def is_in_utxos():
			try:
				return 'txid' in await tx.rpc.call('getrawtransaction',tx.coin_txid,True)
			except:
				return False

		async def is_in_mempool():
			try:
				return 'height' in await tx.rpc.call('getmempoolentry',tx.coin_txid)
			except:
				return False

		async def is_replaced():
			if await is_in_mempool():
				return False
			try:
				ret = await tx.rpc.icall(
					'gettransaction',
					txid              = tx.coin_txid,
					include_watchonly = True,
					verbose           = False )
			except:
				return False
			else:
				if 'bip125-replaceable' in ret and ret.get('confirmations',1) <= 0:
					r.replacing_confs = -ret['confirmations']
					r.replacing_txs = ret['walletconflicts']
					return True
				else:
					return False

		if await is_in_mempool():
			if usr_req:
				d = await tx.rpc.icall(
					'gettransaction',
					txid              = tx.coin_txid,
					include_watchonly = True,
					verbose           = False )
				rep = ('' if d.get('bip125-replaceable') == 'yes' else 'NOT ') + 'replaceable'
				t = d['timereceived']
				if opt.quiet:
					msg('Transaction is in mempool')
				else:
					msg(f'TX status: in mempool, {rep}')
					msg('Sent {} ({} ago)'.format(
						time.strftime('%c',time.gmtime(t)),
						secs_to_dhms(int(time.time()-t))) )
			else:
				msg('Warning: transaction is in mempool!')
		elif await is_in_wallet():
			die(0,f'Transaction has {r.confs} confirmation{suf(r.confs)}')
		elif await is_in_utxos():
			die(4,'ERROR: transaction is in the blockchain (but not in the tracking wallet)!')
		elif await is_replaced():
			msg('Transaction has been replaced')
			msg('Replacement transaction ' + (
					f'has {r.replacing_confs} confirmation{suf(r.replacing_confs)}'
				if r.replacing_confs else
					'is in mempool' ) )
			if not opt.quiet:
				msg('Replacing transactions:')
				d = []
				for txid in r.replacing_txs:
					try:
						d.append(await tx.rpc.call('getmempoolentry',txid))
					except:
						d.append({})
				for txid,mp_entry in zip(r.replacing_txs,d):
					msg(f'  {txid}' + (' in mempool' if 'height' in mp_entry else '') )
			die(0,'')
