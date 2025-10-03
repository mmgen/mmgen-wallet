#!/usr/bin/env python3

import os
from collections import namedtuple
from decimal import Decimal

from mmgen.cfg import Config
from mmgen.util import pp_fmt, ymsg
from mmgen.proto.btc.common import hash160
from mmgen.proto.cosmos.tx.protobuf import RawTx
from mmgen.proto.rune.tx.protobuf import (
	RuneTx,
	build_tx,
	build_swap_tx,
	tx_info,
	send_tx_parms,
	deposit_tx_parms,
	swap_tx_parms)

from ..include.common import vmsg, qmsg, silence, end_silence

test_cfg = Config({'coin': 'rune', 'test_suite': True})

_pv = namedtuple('parse_vector', ['fn', 'txid', 'parms', 'null_fee'], defaults=[None])

parse_vectors = [
	_pv(
		'mainnet-tx-msgsend1.binpb',
		'36f91982c1911fe1aa66b44eed60e29175e5b8ae3301feef9158b7617779b00e',
		send_tx_parms(
			'thor1t60f02r8jvzjrhtnjgfj4ne6rs5wjnejwmj7fh',
			'thor166n4w5039meulfa3p6ydg60ve6ueac7tlt0jws',
			'12613.15290000',
			8000000,
			45060,
			302033,
			pubkey = '02f9cbb8409443ccf043f26d8f91c2550d2578ecc49bb3ad89d4e21a7882bf1e23',
			signature = 'd44b2e0c7546c5fae24a2c829757f49cce1bb29553f7e1a2f87c1ac2f1c46e22' # r
			'509d765fc605d85e8967639864622ebc7c39a1a93fc20cf0fe5d703c4aa3636d')), # s
	_pv(
		'mainnet-tx-msgdeposit1.binpb',
		'1089bbd54746bbc6a40e264d3ce8085561978739094c9c5aac59c569b4c28ba9',
		deposit_tx_parms(
			'THOR', 'RUNE', 'RUNE',
			'thor1lukwlve7hayy66qrdkp4k7sh0emjqwergy7tl3',
			'299.23861844',
			600000000,
			125632,
			348388,
			decimals = 8,
			memo = '=:LTC~LTC:thor1lukwlve7hayy66qrdkp4k7sh0emjqwergy7tl3:605926421/0/1',
			pubkey = '03da157f891abfe7822efb91f59667aa6cc6c3768a7e280caeb9ae243c969eb3e7',
			signature = '869399bcc2ccb9c9c286bdf214439ad132221cb8206547ceb012e06efbc3ff3e' # r
			'0ecc1ba4106702fb5b60cd7a8b94193ea71af5e6e860d978c49a6a63d97e4ded')), # s
	_pv(
		'mainnet-tx-msgdeposit2.binpb',
		'44f45b91e97558e63a11758ac3c186196b9b46f6331f32eff1256888ea879b62',
		deposit_tx_parms(
			'ETH', 'USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7', 'USDT',
			'thor1xxncvuptvmgcl5ep7rry3xehtw97jsg9uyv6rn',
			'500.00000000',
			50000000,
			88176,
			104625,
			decimals = None,
			synth = False,
			trade = True,
			memo = '=:AVAX~AVAX:thor1xxncvuptvmgcl5ep7rry3xehtw97jsg9uyv6rn:2113883178',
			pubkey = '02a6e97e3f20809511500d8895117d4344badda9e6af4216d41b10a105d1070254',
			signature = 'b0673ab89781199d35b94051f26db30996f055abd71804d67fe4bdf33934bdb9' # r
			'30d830675d398c6d042328ef681bf1a23e856ed0ab33d948ea149489400db953'), # s
		null_fee = True),
	_pv(
		'mainnet-tx-msgdeposit3.binpb',
		'02d2fb2f2e5ac00ad4a31c37ffc43b72963f93598f8b3c8f4d3932c2e950b459',
		deposit_tx_parms(
			'ETH', 'USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48', 'USDC',
			'thor1lukwlve7hayy66qrdkp4k7sh0emjqwergy7tl3',
			'2425.75973697',
			600000000,
			125632,
			375988,
			decimals = 8,
			synth = None,
			trade = True,
			memo = '=:THOR.RUNE:thor1lukwlve7hayy66qrdkp4k7sh0emjqwergy7tl3:127025748855/0/1',
			pubkey = '03da157f891abfe7822efb91f59667aa6cc6c3768a7e280caeb9ae243c969eb3e7',
			signature = 'be8324f6a1535b971d63715532e2e42ee3c35c05b81ed9b6bccd9a1765688eca'
			'4ca00a66119b07c5168c6c78e22299becc82d5f311ee79ae9183776b0dff3269'))
]

_bv = namedtuple('build_vector', ['txid', 'txid2', 'parms', 'null_fee'], defaults=[None])

build_vectors = [
	_bv(
		'3939612d0ddc55fd4d1c6ef118d1b2085a6655cb57d55ac9efd658467e039e0c',
		'e783ced14909a9e2a21c99b6b3b66fb38ba3bdf985876bb8d6cea02813d603a9',
		send_tx_parms(
			'thor1tx3nm6xfynq3re5ehtm6530z0pah9qjeu0r9nd',
			'thor1j5u6vlr8kzt76fe7896hsmurkhgn68j0z4qa6w',
			'123.456789',
			8000000,
			12345,
			37,
			wifkey = 'L5nWojqqMLq7wh3CfhxUNYQ38acABD6sUao9dfb8i5B5wSefCJXe')),
	_bv(
		'0d41e0ee40cd18a991cd8f0ef0e60e4c5bea898c53d54e00b6dddc0c9ce7edb7',
		'444e026fe5d0988da602dc22f0ff6172c080f1d2e2d66012d86f4afd314b78d6',
		deposit_tx_parms(
			'THOR', 'RUNE', 'RUNE',
			'thor18ug6p4zs5dsy0m3u69gf5md5ssdg8hqkk8aya4',
			'123.456789',
			8000000,
			12345,
			37,
			decimals = 8,
			memo = '=:MEMO',
			wifkey = 'Ky9bSjPUD35uUaY3JReXiESivnfxV6rLMsW1wTFyvVZwYXpX95vF'))
]

swap_build_vectors = [
	_bv(
		'0d41e0ee40cd18a991cd8f0ef0e60e4c5bea898c53d54e00b6dddc0c9ce7edb7',
		'444e026fe5d0988da602dc22f0ff6172c080f1d2e2d66012d86f4afd314b78d6',
		swap_tx_parms(
			'thor18ug6p4zs5dsy0m3u69gf5md5ssdg8hqkk8aya4',
			'123.456789',
			8000000,
			12345,
			37,
			memo = '=:MEMO',
			wifkey = 'Ky9bSjPUD35uUaY3JReXiESivnfxV6rLMsW1wTFyvVZwYXpX95vF'))
]

def test_tx(src, cfg, vec):

	proto = cfg._proto
	parms = vec.parms._replace(amt=Decimal(vec.parms.amt))
	if parms.pubkey:
		parms = parms._replace(
			pubkey = bytes.fromhex(parms.pubkey),
			signature = bytes.fromhex(parms.signature))

	assert src in ('parse', 'build', 'swapbuild')

	match src:
		case 'parse':
			tx_in = open(os.path.join('test/ref/thorchain', vec.fn), 'br').read()
			tx = RuneTx.loads(tx_in)
			if not parms.from_addr:
				ymsg(f'Warning: missing test vector data for {vec.fn}')
			assert bytes(tx) == tx_in
		case 'build':
			tx = build_tx(cfg, proto, parms, null_fee=vec.null_fee)
		case 'swapbuild':
			tx = build_swap_tx(cfg, proto, parms)

	vmsg(pp_fmt(tx))

	msg_type = 'MsgSend' if tx.body.messages[0].id == '/types.MsgSend' else 'MsgDeposit'

	vmsg('\n  TX info:\n    ' + '\n    '.join(tx_info(tx, proto)) + '\n')

	tx.verify_sig(proto, parms.account_number)

	pubkey = tx.authInfo.signerInfos[0].publicKey.key.data
	vec_txid2 = getattr(vec, 'txid2', None)
	assert hash160(pubkey) == getattr(
		tx.body.messages[0].body,
		'fromAddress' if msg_type == 'MsgSend' else 'signer')
	if tx.txid not in (vec.txid, vec_txid2):
		raise ValueError(f'{tx.txid} not in ({vec.txid}, {vec_txid2})')
	if tx.txid == vec_txid2:
		qmsg('')
		ymsg('Warning: non-standard TxID produced')

	if src == 'parse' and parms.from_addr:
		built_tx = build_tx(cfg, proto, parms, null_fee=vec.null_fee)
		addr_from_pubkey = proto.encode_addr_bech32x(hash160(pubkey))
		assert addr_from_pubkey == parms.from_addr
		assert bytes(built_tx) == tx_in
		raw_tx = RawTx(bytes(tx.body), bytes(tx.authInfo), tx.signatures)
		assert bytes(raw_tx) == bytes(RawTx.loads(tx_in))
		assert bytes(raw_tx) == bytes(tx.raw)
		assert tx_in == bytes(tx)

class unit_tests:

	def txparse(self, name, ut, desc='transaction parsing and signature verification'):
		for vec in parse_vectors:
			test_tx('parse', test_cfg, vec)
		return True

	def txbuild(self, name, ut, desc='transaction building and signing (MsgSend, MsgDeposit)'):
		for vec in build_vectors:
			test_tx('build', test_cfg, vec)
		return True

	def swaptxbuild(self, name, ut, desc='transaction building and signing (Swap TX)'):
		for vec in swap_build_vectors:
			test_tx('swapbuild', test_cfg, vec)
		return True

	def rpc(self, name, ut, desc='remote RPC operations'):
		import sys, asyncio
		from mmgen.rpc import rpc_init
		from ..cmdtest_d.httpd.thornode.rpc import ThornodeRPCServer

		silence()
		regtest_cfg = Config({'coin': 'rune', 'regtest': True, 'test_suite': True})
		end_silence()

		thornode_server = ThornodeRPCServer(test_cfg)
		thornode_server.start()

		addr = 'thor1lukwlve7hayy66qrdkp4k7sh0emjqwergy7tl3'
		txhash = 'abcdef01' * 8
		txbytes = open('test/ref/thorchain/mainnet-tx-msgsend1.binpb', 'rb').read()

		async def main():

			rpc = await rpc_init(regtest_cfg)

			res = rpc.get_account_info(addr)
			assert res['address'] == addr
			assert res['account_number']
			assert res['sequence']

			res = rpc.get_tx_info(txhash)
			assert res['hash'] == txhash.upper()

			res = rpc.tx_op(txbytes.hex(), op='check_tx')
			assert res['code'] == 0

		asyncio.run(main())
		return True
