#!/usr/bin/env python3

"""
test.modtest_d.ut_cashaddr: unit test for the BCH cashaddr module
"""

altcoin_dep = True

from collections import namedtuple

from mmgen.proto.bch.cashaddr import cashaddr_parse_addr, cashaddr_decode_addr, cashaddr_encode_addr
from mmgen.addr import CoinAddr

from ..include.common import cfg, vmsg

from mmgen.protocol import init_proto
proto = init_proto(cfg, 'bch')

# Source: https://upgradespecs.bitcoincashnode.org/cashaddr
alias_data = """
1BpEi6DfDAUFd7GtittLSdBeYJvcoaVggu  bitcoincash:qpm2qsznhks23z7629mms6s4cwef74vcwvy22gdx6a
1KXrWXciRDZUpQwQmuM1DbwsKDLYAYsVLR  bitcoincash:qr95sy3j9xwd2ap32xkykttr4cvcu7as4y0qverfuy
16w1D5WRVKJuZUsSRzdLp9w3YGcgoxDXb   bitcoincash:qqq3728yw0y47sqn6l2na30mcw6zm78dzqre909m2r
3CWFddi6m4ndiGyKqzYvsFYagqDLPVMTzC  bitcoincash:ppm2qsznhks23z7629mms6s4cwef74vcwvn0h829pq
3LDsS579y7sruadqu11beEJoTjdFiFCdX4  bitcoincash:pr95sy3j9xwd2ap32xkykttr4cvcu7as4yc93ky28e
31nwvkZwyPdgzjBJZXfDmSWsC4ZLKpYyUw  bitcoincash:pqq3728yw0y47sqn6l2na30mcw6zm78dzq5ucqzc37
"""

vec_data = """
F5BF48B397DAE70BE82B3CCA4793F8EB2B6CDAC9
20 0  bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2
20 1  bchtest:pr6m7j9njldwwzlg9v7v53unlr4jkmx6eyvwc0uz5t
20 1  pref:pr6m7j9njldwwzlg9v7v53unlr4jkmx6ey65nvtks5
20 15 prefix:0r6m7j9njldwwzlg9v7v53unlr4jkmx6ey3qnjwsrf

7ADBF6C17084BC86C1706827B41A56F5CA32865925E946EA
24 0  bitcoincash:q9adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2ws4mr9g0
24 1  bchtest:p9adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2u94tsynr
24 1  pref:p9adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2khlwwk5v
24 15 prefix:09adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2p29kc2lp

3A84F9CF51AAE98A3BB3A78BF16A6183790B18719126325BFC0C075B
28 0  bitcoincash:qgagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkcw59jxxuz
28 1  bchtest:pgagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkcvs7md7wt
28 1  pref:pgagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkcrsr6gzkn
28 15 prefix:0gagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkc5djw8s9g

3173EF6623C6B48FFD1A3DCC0CC6489B0A07BB47A37F47CFEF4FE69DE825C060
32 0  bitcoincash:qvch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxq5nlegake
32 1  bchtest:pvch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxq7fqng6m6
32 1  pref:pvch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxq4k9m7qf9
32 15 prefix:0vch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxqsh6jgp6w

C07138323E00FA4FC122D3B85B9628EA810B3F381706385E289B0B25631197D194B5C238BEB136FB
40 0  bitcoincash:qnq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklv39gr3uvz
40 1  bchtest:pnq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklvmgm6ynej
40 1  pref:pnq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklv0vx5z0w3
40 15 prefix:0nq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklvwsvctzqy

E361CA9A7F99107C17A622E047E3745D3E19CF804ED63C5C40C6BA763696B98241223D8CE62AD48D863F4CB18C930E4C
48 0  bitcoincash:qh3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqex2w82sl
48 1  bchtest:ph3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqnzf7mt6x
48 1  pref:ph3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqjntdfcwg
48 15 prefix:0h3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqakcssnmn

D9FA7C4C6EF56DC4FF423BAAE6D495DBFF663D034A72D1DC7D52CBFE7D1E6858F9D523AC0A7A5C34077638E4DD1A701BD017842789982041
56 0  bitcoincash:qmvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqscw8jd03f
56 1  bchtest:pmvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqs6kgdsg2g
56 1  pref:pmvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqsammyqffl
56 15 prefix:0mvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqsgjrqpnw8

D0F346310D5513D9E01E299978624BA883E6BDA8F4C60883C10F28C2967E67EC77ECC7EEEAEAFC6DA89FAD72D11AC961E164678B868AEEEC5F2C1DA08884175B
64 0  bitcoincash:qlg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96mtky5sv5w
64 1  bchtest:plg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96mc773cwez
64 1  pref:plg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96mg7pj3lh8
64 15 prefix:0lg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96ms92w6845
"""

class unit_tests:

	@property
	def vectors(self):
		t = namedtuple('vectors', ['size', 'type', 'addr', 'data'])
		def gen():
			for a in vec_data.splitlines():
				if a:
					d = a.split()
					if len(d) == 1:
						data = d[0].lower()
					else:
						yield t(int(d[0]), int(d[1]), d[2], data)
		return list(gen())

	@property
	def aliases(self):
		t = namedtuple('aliases', ['legacy', 'cashaddr'])
		return [t(*a.split()) for a in alias_data.splitlines() if a]

	def encode(self, name, ut, desc='low-level address encoding'):
		data = None
		for v in self.vectors:
			if not data or data != v.data:
				data = v.data
				vmsg(f'\n{data}')
			vmsg(f'    {v.addr}')
			ret = cashaddr_encode_addr(v.type, v.size, cashaddr_parse_addr(v.addr).pfx, bytes.fromhex(v.data))
			assert ret.addr == v.addr
		return True

	def decode(self, name, ut, desc='low-level address decoding'):
		data = None
		for v in self.vectors:
			if not data or data != v.data:
				data = v.data
				vmsg(f'\n{data}')
			vmsg(f'    {v.addr}')
			ret = cashaddr_decode_addr(v.addr)
			assert ret.bytes.hex() == v.data
		return True

	def coinaddr(self, name, ut, desc='CoinAddr class'):
		for e in self.aliases:
			for addr in (
					e.cashaddr.upper(),
					e.cashaddr,
					e.cashaddr.split(':')[1],
					e.legacy,
				):
				a = CoinAddr(proto, addr)
				vmsg(addr)
				assert e.legacy == a.views[1]
				assert e.cashaddr == a.proto.cashaddr_pfx + ':' + a.views[0]
			vmsg('')
		return True

	def errors(self, name, ut, desc='error handling'):
		# could do these in objtest.py:
		def bad1(): a = CoinAddr(proto, self.aliases[0].cashaddr.replace('g', 'G'))
		def bad2(): a = CoinAddr(proto, 'x' + self.aliases[0].cashaddr)
		def bad3(): a = CoinAddr(proto, self.aliases[0].cashaddr[:-1])
		def bad4(): a = CoinAddr(proto, self.aliases[0].cashaddr[:-1]+'i')
		def bad5(): a = CoinAddr(proto, self.aliases[0].cashaddr[:-1]+'x')

		ut.process_bad_data((
			('case',     'ObjectInitError', 'mixed case',     bad1),
			('prefix',   'ObjectInitError', 'invalid prefix', bad2),
			('data',     'ObjectInitError', 'too short',      bad3),
			('b32 char', 'ObjectInitError', 'substring',      bad4),
			('chksum',   'ObjectInitError', 'checksum',       bad5),
		))
		return True
