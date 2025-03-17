#!/usr/bin/env python3

"""
test.modtest_d.gen: key/address generation unit tests for the MMGen suite
"""

from mmgen.color import blue
from mmgen.protocol import init_proto
from mmgen.key import PrivKey
from mmgen.addr import MMGenAddrType
from mmgen.addrgen import KeyGenerator, AddrGenerator
from mmgen.keygen import get_backends

from ..include.common import cfg, qmsg

# TODO: add viewkey checks
vectors = { # from tooltest2
	'btc': ((
		'5HwzecKMWD82ppJK3qMKpC7ohXXAwcyAN5VgdJ9PLFaAzpBG4sX',
		'1C5VPtgq9xQ6AcTgMAR3J6GDrs72HC4pS1',
		'legacy'
	), (
		'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm',
		'1Kz9fVSUMshzPejpzW9D95kScgA3rY6QxF',
		'compressed'
	), (
		'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm',
		'3AhjTiWHhVJAi1s5CfKMcLzYps12x3gZhg',
		'segwit'
	), (
		'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm',
		'bc1q6pqnfwwakuuejpm9w52ds342f9d5u36v0qnz7c',
		'bech32'),
	),
	'eth': ((
		'0000000000000000000000000000000000000000000000000000000000000001',
		'7e5f4552091a69125d5dfcb7b8c2659029395bdf',
		'ethereum',
		),),
	'xmr': ((
		'0000000000000000000000000000000000000000000000000000000000000001',
		'42nsXK8WbVGTNayQ6Kjw5UdgqbQY5KCCufdxdCgF7NgTfjC69Mna7DJSYyie77hZTQ8H92G2HwgFhgEUYnDzrnLnQdF28r3',
		'monero',
		),),
	'zec': ((
		'SKxny894fJe2rmZjeuoE6GVfNkWoXfPp8337VrLLNWG56FjqVUYR',
		'zceQDpyNwek7dKqF5ZuFGj7YrNVxh7X1aPkrVxDLVxWSiZAFDEuy5C7XNV8VhyZ3ghTPQ61xjCGiyLT3wqpiN1Yi6mdmaCq',
		'zcash_z',
		),),
}

def do_test(proto, wif, addr_chk, addr_type, internal_keccak):

	if internal_keccak:
		cfg.use_internal_keccak_module = True
		add_msg = ' (internal keccak module)'
	else:
		add_msg = ''

	at = MMGenAddrType(proto, addr_type)
	privkey = PrivKey(proto, wif=wif)

	for n, backend in enumerate(get_backends(at.pubkey_type)):

		kg = KeyGenerator(cfg, proto, at.pubkey_type, silent=n+1)
		qmsg(blue(f'  Testing backend {backend!r} for addr type {addr_type!r}{add_msg}'))

		data = kg.gen_data(privkey)

		for k, v in data._asdict().items():
			if v and k in ('pubkey', 'viewkey_bytes'):
				qmsg(f'    {k+":":19} {v.hex()}')

		ag = AddrGenerator( cfg, proto, addr_type)
		addr = ag.to_addr(data)
		qmsg(f'    addr:               {addr}\n')

		assert addr == addr_chk, f'{addr} != {addr_chk}'

	cfg.use_internal_keccak_module = False

def do_tests(coin, internal_keccak=False):
	proto = init_proto( cfg, coin)
	for wif, addr, addr_type in vectors[coin]:
		do_test(proto, wif, addr, addr_type, internal_keccak)
	return True

class unit_tests:

	altcoin_deps = ('eth', 'xmr', 'zec')

	def btc(self, name, ut):
		return do_tests('btc')

	def eth(self, name, ut):
		do_tests('eth')
		return do_tests('eth', internal_keccak=True)

	def xmr(self, name, ut):
		if not cfg.fast:
			do_tests('xmr')
		return do_tests('xmr', internal_keccak=True)

	def zec(self, name, ut):
		return do_tests('zec')
