#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>

"""
tool_api_test.py: test the MMGen suite tool API
"""

import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))))
sys.path[0] = os.curdir

def check_equal(a,b):
	assert a == b, f'{a} != {b}'

def msg(*args,**kwargs):
	print(*args,**kwargs,file=sys.stdout)

def init_coin(t,coinsym,network,addrtype,triplet):
	t.init_coin(coinsym,network)
	t.addrtype = addrtype
	check_equal(type(t.addrtype).__name__,'MMGenAddrType')
	check_equal(f'{t.coin} {t.proto.cls_name} {t.addrtype}', triplet)
	msg('\ncoin/proto/type:',triplet)

def run_test():
	key_bytes = bytes.fromhex('deadbeef' * 8)

	from mmgen.tool import tool_api
	tool = tool_api()

	tool.coins
	tool.print_addrtypes()

	check_equal(f'{tool.coin} {tool.proto.cls_name} {tool.addrtype}', 'BTC Bitcoin L' )

	tool.usr_randchars     # getter
	tool.usr_randchars = 0 # setter
	check_equal(tool.usr_randchars,0)

	init_coin(tool,'xmr','mainnet','M','XMR Monero M')
	msg('\n'.join(tool.randpair()))

	init_coin(tool,'etc','mainnet','E','ETC EthereumClassic E')
	msg('\n'.join(tool.randpair()))

	init_coin(tool,'ltc','regtest','bech32','LTC LitecoinRegtest B')

	wif,addr = tool.randpair()
	from mmgen.obj import PrivKey,CoinAddr
	msg('wif:',PrivKey(proto=tool.proto,wif=wif).wif)
	msg('addr:',CoinAddr(proto=tool.proto,addr=addr))

	wif = PrivKey(proto=tool.proto,s=key_bytes,compressed=True,pubkey_type='std').wif
	addr = tool.wif2addr(wif)
	msg('wif:',PrivKey(proto=tool.proto,wif=wif).wif)
	msg('addr:',CoinAddr(proto=tool.proto,addr=addr))

	addr_chk = tool.privhex2addr(key_bytes.hex())

	check_equal(addr,addr_chk)
	check_equal(wif,'cV3ZRqf8PhyfiFwtJfkvGu2qmBsazE1wXoA2A16S3nixb3BTvvVx')
	check_equal(addr,'rltc1qvmqas4maw7lg9clqu6kqu9zq9cluvllnz4kj9y')

	init_coin(tool,'zec','mainnet','Z','ZEC Zcash Z')

	wif = PrivKey(proto=tool.proto,s=key_bytes,compressed=True,pubkey_type='zcash_z').wif
	addr = tool.wif2addr(wif)
	msg('wif:',wif)
	msg('addr:',CoinAddr(proto=tool.proto,addr=addr))

	addr_chk = tool.privhex2addr(key_bytes.hex())
	wif_chk = PrivKey(proto=tool.proto,wif=wif).wif

	check_equal(addr,addr_chk)
	check_equal(wif,wif_chk)
	check_equal(
		addr,
		'zchFELwBxqsAubsLQ8yZgPCDDGukjXJssgCbiTPwFNmFwn9haLnDatzfhLdZzJT4PcU4o2yr92B52UFirUzEdF6ZYM2gBkM' )

run_test()
