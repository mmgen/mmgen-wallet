#!/usr/bin/env python3
"""
test.unit_tests_d.ut_msg: message signing unit tests for the MMGen suite
"""

import os

from test.include.common import silence,end_silence,restart_test_daemons,stop_test_daemons
from mmgen.opts import opt
from mmgen.util import msg,bmsg,pumsg
from mmgen.protocol import CoinProtocol,init_proto
from mmgen.msg import NewMsg,UnsignedMsg,SignedMsg,SignedOnlineMsg

def get_obj(coin,network):

	if coin == 'bch':
		addrlists = 'DEADBEEF:C:1-20 98831F3A:C:8,2 A091ABAA:L:111 A091ABAA:C:1'
	else:
		# A091ABAA = 98831F3A:5S
		addrlists = 'DEADBEEF:C:1-20 98831F3A:B:8,2 A091ABAA:S:10-11 A091ABAA:111 A091ABAA:C:1'

	return NewMsg(
		coin      = coin,
		network   = network,
		message   = '08/Jun/2021 Bitcoin Law Enacted by El Salvador Legislative Assembly',
		addrlists = addrlists )

async def run_test(network_id):

	coin,network = CoinProtocol.Base.parse_network_id(network_id)

	if not opt.verbose:
		silence()

	bmsg(f'\nTesting {coin.upper()} {network.upper()}:\n')

	restart_test_daemons(network_id)

	pumsg('\nTesting data creation:\n')

	m = get_obj(coin,network)

	tmpdir = os.path.join('test','trash2')

	os.makedirs(tmpdir,exist_ok=True)

	m.write_to_file(
		outdir        = tmpdir,
		ask_overwrite = False )

	pumsg('\nTesting signing:\n')

	m = UnsignedMsg( infile = os.path.join(tmpdir,get_obj(coin,network).filename) )
	await m.sign(wallet_files=['test/ref/98831F3A.mmwords'])

	m = SignedMsg( data=m.__dict__ )
	m.write_to_file(
		outdir        = tmpdir,
		ask_overwrite = False )

	pumsg('\nTesting display:\n')

	m = SignedOnlineMsg( infile = os.path.join(tmpdir,get_obj(coin,network).signed_filename) )

	msg(m.format())

	pumsg('\nTesting single address display:\n')
	msg(m.format('A091ABAA:111'))

	pumsg('\nTesting verification:\n')
	await m.verify(summary=opt.verbose)

	pumsg('\nTesting single address verification:\n')
	await m.verify('A091ABAA:111',summary=opt.verbose)

	stop_test_daemons(network_id)

	msg('\n')

	if not opt.verbose:
		end_silence()

	return True

class unit_tests:

	altcoin_deps = ('ltc','bch')

	def btc(self,name,ut):
		return run_test('btc')

	def btc_tn(self,name,ut):
		return run_test('btc_tn')

	def btc_rt(self,name,ut):
		return run_test('btc_rt')

	def ltc(self,name,ut):
		return run_test('ltc')

	def bch(self,name,ut):
		return run_test('bch')
