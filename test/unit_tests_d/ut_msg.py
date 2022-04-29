#!/usr/bin/env python3
"""
test.unit_tests_d.ut_msg: message signing unit tests for the MMGen suite
"""

import os

from test.include.common import silence,end_silence,restart_test_daemons,stop_test_daemons
from mmgen.opts import opt
from mmgen.util import msg,bmsg,pumsg
from mmgen.protocol import CoinProtocol
from mmgen.msg import NewMsg,UnsignedMsg,SignedMsg,SignedOnlineMsg,ExportedMsgSigs
from mmgen.addr import MMGenID

def get_obj(coin,network,msghash_type):

	if coin == 'bch':
		addrlists = 'DEADBEEF:C:1-20 98831F3A:C:8,2 A091ABAA:L:111 A091ABAA:C:1'
	elif coin == 'eth':
		addrlists = 'DEADBEEF:E:1-20 98831F3A:E:8,2 A091ABAA:E:111'
	else:
		# A091ABAA = 98831F3A:5S
		addrlists = 'DEADBEEF:C:1-20 98831F3A:B:8,2 A091ABAA:S:10-11 A091ABAA:111 A091ABAA:C:1'

	return NewMsg(
		coin      = coin,
		network   = network,
		message   = '08/Jun/2021 Bitcoin Law Enacted by El Salvador Legislative Assembly',
		addrlists = addrlists,
		msghash_type = msghash_type )

async def run_test(network_id,msghash_type='raw'):

	coin,network = CoinProtocol.Base.parse_network_id(network_id)

	if not opt.verbose:
		silence()

	bmsg(f'\nTesting {coin.upper()} {network.upper()}:\n')

	restart_test_daemons(network_id)

	pumsg('\nTesting data creation:\n')

	m = get_obj(coin,network,msghash_type)

	tmpdir = os.path.join('test','trash2')

	os.makedirs(tmpdir,exist_ok=True)

	m.write_to_file(
		outdir        = tmpdir,
		ask_overwrite = False )

	pumsg('\nTesting signing:\n')

	m = UnsignedMsg( infile = os.path.join(tmpdir,get_obj(coin,network,msghash_type).filename) )
	await m.sign(wallet_files=['test/ref/98831F3A.mmwords'])

	m = SignedMsg( data=m.__dict__ )
	m.write_to_file(
		outdir        = tmpdir,
		ask_overwrite = False )

	pumsg('\nTesting display:\n')

	m = SignedOnlineMsg( infile = os.path.join(tmpdir,get_obj(coin,network,msghash_type).signed_filename) )

	msg(m.format())

	single_addr = 'A091ABAA:E:111' if m.proto.base_proto == 'Ethereum' else 'A091ABAA:111'
	single_addr_coin = m.sigs[MMGenID(m.proto,single_addr)]['addr']

	pumsg('\nTesting single address display:\n')
	msg(m.format(single_addr))

	pumsg('\nTesting verification:\n')
	await m.verify(summary=opt.verbose)

	pumsg('\nTesting single address verification:\n')
	await m.verify(single_addr,summary=opt.verbose)

	pumsg('\nTesting JSON dump for export:\n')
	msg( m.get_json_for_export() )

	pumsg('\nTesting single address JSON dump for export:\n')
	msg( m.get_json_for_export(single_addr) )

	from mmgen.fileutil import write_data_to_file
	exported_sigs = os.path.join(tmpdir,'signatures.json')
	write_data_to_file(
		outfile = exported_sigs,
		data    = m.get_json_for_export(),
		desc    = 'signature data',
		ask_overwrite = False )

	m = ExportedMsgSigs( infile=exported_sigs )

	pumsg('\nTesting verification (exported data):\n')
	await m.verify(summary=opt.verbose)

	pumsg('\nTesting single address verification (exported data):\n')
	await m.verify(single_addr_coin,summary=opt.verbose)

	pumsg('\nTesting display (exported data):\n')
	msg(m.format())

	pumsg('\nTesting single address display (exported data):\n')
	msg(m.format(single_addr_coin))

	stop_test_daemons(network_id)

	msg('\n')

	if not opt.verbose:
		end_silence()

	return True

class unit_tests:

	altcoin_deps = ('ltc','bch','eth','eth_raw')

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

	def eth(self,name,ut):
		return run_test('eth',msghash_type='eth_sign')

	def eth_raw(self,name,ut):
		return run_test('eth')
