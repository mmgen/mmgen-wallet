#!/usr/bin/env python3

"""
test.modtest_d.ut_addrparse: address parsing tests for the MMGen suite
"""

from mmgen.color import yellow, cyan
from mmgen.util import msg, msg_r, pp_fmt

from ..include.common import cfg, vmsg

vectors = {
	'btc_mainnet': [
		{'std': '1C5VPtgq9xQ6AcTgMAR3J6GDrs72HC4pS1'},
		{'std': '3AhjTiWHhVJAi1s5CfKMcLzYps12x3gZhg'},
		{'std': 'bc1q6pqnfwwakuuejpm9w52ds342f9d5u36v0qnz7c'}
	],
	'ltc_mainnet': [
		{'std': 'LUbHQNYoy23RByq4dKQotLA4ugk9FhpAMT'},
		{'std': 'MCoZrHYPqYKqvpiwyzzqf3EPxF5no6puEf'},
		{'std': 'ltc1qvmqas4maw7lg9clqu6kqu9zq9cluvllnst5pxs'}
	],
	'xmr_mainnet': [
		{ # ut_xmrseed.vectors[0]:
		'std': '42ey1afDFnn4886T7196doS9GPMzexD9gXpsZJDwVjeRVdFCSoHnv7KPbBeGpzJBzHRCAs9UxqeoyFQMYbqSWYTfJJQAWDm',
		# https://github.com/monero-project/monero/tests/functional_tests/integrated_address.py
		'int': '4CMe2PUhs4J4886T7196doS9GPMzexD9gXpsZJDwVjeRVdFCSoHnv7KPbBeGpzJBzHRCAs9UxqeoyFQMYbqSWYTfSbLRB61BQVATzerHGj',
		'id':  '0123456789abcdef'
		}, {
		'std': '46r4nYSevkfBUMhuykdK3gQ98XDqDTYW1hNLaXNvjpsJaSbNtdXh1sKMsdVgqkaihChAzEy29zEDPMR3NHQvGoZCLGwTerK',
		'int': '4GYjoMG9Y2BBUMhuykdK3gQ98XDqDTYW1hNLaXNvjpsJaSbNtdXh1sKMsdVgqkaihChAzEy29zEDPMR3NHQvGoZCVSs1ZojwrDCGS5rUuo',
		'id':  '1122334455667788'
		}
	],
	'zec_mainnet': [
		{'std': 't1KQYLBvjpmcQuATommo6gx2QTQDLPikB8Q'},
		{'std': 'zceQDpyNwek7dKqF5ZuFGj7YrNVxh7X1aPkrVxDLVxWSiZAFDEuy5C7XNV8VhyZ3ghTPQ61xjCGiyLT3wqpiN1Yi6mdmaCq'},
	],
	'eth_mainnet': [
		{'std': '7e5f4552091a69125d5dfcb7b8c2659029395bdf'},
	],
}

def test_network(proto, addrs):

	def check_equal(a, b):
		assert a == b, f'{a.hex()} != {b.hex()}'

	def check_bytes(addr):
		if addr.parsed.ver_bytes is not None:
			check_equal(
				addr.parsed.ver_bytes,
				proto.addr_fmt_to_ver_bytes.get(addr.addr_fmt))
		check_equal(
			addr.parsed.data + ((addr.parsed.payment_id or b'') if proto.coin == 'XMR' else b''),
			addr.bytes)

	def fmt_addr_data(addr):
		return pp_fmt({k:(v.hex() if isinstance(v, bytes) else v) for k, v in addr.parsed._asdict().items()})

	def print_info(addr):
		vmsg('\n{}\n{}\n{}'.format(yellow(addr.addr_fmt), cyan(addr), fmt_addr_data(addr)))

	msg_r(f'Testing {proto.coin} address parsing...')
	vmsg('')

	from mmgen.addr import CoinAddr

	for addr in addrs:
		a1 = CoinAddr(proto, addr['std'])
		print_info(a1)
		check_bytes(a1)
		assert not hasattr(a1.parsed, 'payment_id') or a1.parsed.payment_id is None

		if 'int' in addr:
			a2 = CoinAddr(proto, addr['int'])
			print_info(a2)
			check_bytes(a2)
			check_equal(a1.parsed.data, a2.parsed.data)
			check_equal(a2.parsed.payment_id, bytes.fromhex(addr['id']))

	msg('OK')
	vmsg('')


class unit_test:

	def run_test(self, name, ut):

		from mmgen.protocol import init_proto

		for net_id, addrs in vectors.items():
			coin, network = net_id.split('_')
			if cfg.no_altcoin_deps and coin != 'btc':
				continue
			test_network(
				init_proto(cfg, coin, network=network),
				addrs)

		return True
