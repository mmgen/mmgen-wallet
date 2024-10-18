#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>

"""
test.misc.tool_api_test: test the MMGen suite tool API
"""

import sys
from mmgen.key import PrivKey
from mmgen.addr import CoinAddr

keys = [
	'118089d66b4a5853765e94923abdd5de4616c6e5118089d66b4a5853765e9492',
	'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef',
	]

def check_equal(a, b):
	assert a == b, f'{a} != {b}'

def msg(*args, **kwargs):
	print(*args, **kwargs, file=sys.stdout)

def init_coin(t, coinsym, network, addrtype):
	t.init_coin(coinsym, network)
	t.addrtype = addrtype
	check_equal(type(t.addrtype).__name__, 'MMGenAddrType')
	msg(f'\n{t.coin} {t.proto.network.capitalize()} {t.addrtype.name.upper()} ({t.addrtype})')

def test_randpair(t):
	wif, addr = t.randpair()
	wif_chk = PrivKey(proto=t.proto, wif=wif).wif
	check_equal(wif, wif_chk)
	msg('\n  === randwif ===')
	msg('  wif:', wif)
	msg('  addr:', CoinAddr(proto=t.proto, addr=addr))

def test_wif2addr(t, wif_chk, addr_chk, key_idx):
	key_bytes = bytes.fromhex(keys[key_idx])
	wif = PrivKey(
		proto       = t.proto,
		s           = key_bytes,
		compressed  = t.addrtype.compressed,
		pubkey_type = t.addrtype.pubkey_type).wif
	addr = t.wif2addr(wif)

	msg('\n  === wif2addr ===')
	msg('  wif:', PrivKey(proto=t.proto, wif=wif).wif)
	msg('  addr:', CoinAddr(proto=t.proto, addr=addr))

	addr_ph = t.privhex2addr(key_bytes.hex())

	check_equal(addr, addr_ph)
	check_equal(wif, wif_chk)
	check_equal(addr, addr_chk)

def test_triplet(tool, coin, network, addrtype, key_idx, wif_chk, addr_chk):
	init_coin(tool, coin, network, addrtype)
	test_randpair(tool)
	test_wif2addr(tool, wif_chk, addr_chk, key_idx)

def run_test():

	from mmgen.tool.api import tool_api
	tool = tool_api(cfg)

	tool.coins
	tool.print_addrtypes()

	tool.usr_randchars     # getter
	tool.usr_randchars = 0 # setter
	check_equal(tool.usr_randchars, 0)

	check_equal(f'{tool.coin} {tool.proto.cls_name} {tool.addrtype}', 'BTC mainnet L')

	# test vectors from tooltest2.py:

	test_triplet(tool, 'btc', 'mainnet', 'L', 0,
		'5HwzecKMWD82ppJK3qMKpC7ohXXAwcyAN5VgdJ9PLFaAzpBG4sX',
		'1C5VPtgq9xQ6AcTgMAR3J6GDrs72HC4pS1')

	test_triplet(tool, 'btc', 'mainnet', 'C', 0,
		'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm',
		'1Kz9fVSUMshzPejpzW9D95kScgA3rY6QxF')

	test_triplet(tool, 'btc', 'mainnet', 'segwit', 0,
		'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm',
		'3AhjTiWHhVJAi1s5CfKMcLzYps12x3gZhg')

	test_triplet(tool, 'btc', 'mainnet', 'B', 0,
		'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm',
		'bc1q6pqnfwwakuuejpm9w52ds342f9d5u36v0qnz7c')

	if not 'no_altcoin' in sys.argv:
		test_triplet(tool, 'ltc', 'regtest', 'bech32', 1,
			'cV3ZRqf8PhyfiFwtJfkvGu2qmBsazE1wXoA2A16S3nixb3BTvvVx',
			'rltc1qvmqas4maw7lg9clqu6kqu9zq9cluvllnz4kj9y')

		test_triplet(tool, 'xmr', 'mainnet', 'M', 1,
			'e8164dda6d42bd1e261a3406b2038dcbddadbeefdeadbeefdeadbeefdeadbe0f',
			'41i7saPWA53EoHenmJVRt34dubPxsXwoWMnw8AdMyx4mTD1svf7qYzcVjxxRfteLNdYrAxWUMmiPegFW9EfoNgXx7vDMExv')

		test_triplet(tool, 'etc', 'mainnet', 'E', 1,
			'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef',
			'c96aaa54e2d44c299564da76e1cd3184a2386b8d')

		test_triplet(tool, 'zec', 'mainnet', 'Z', 1,
			'SKxuS56e99jpCeD9mMQ5o63zoGPakNdM9HCvt4Vt2cypvRjCdvGJ',
			'zchFELwBxqsAubsLQ8yZgPCDDGukjXJssgCbiTPwFNmFwn9haLnDatzfhLdZzJT4PcU4o2yr92B52UFirUzEdF6ZYM2gBkM')

from mmgen.cfg import Config

cfg = Config(process_opts=True)

run_test()
