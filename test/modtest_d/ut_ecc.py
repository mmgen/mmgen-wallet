#!/usr/bin/env python3

"""
test.modtest_d.ut_ecc: elliptic curve unit test for the MMGen suite
"""

from mmgen.proto.secp256k1.secp256k1 import pubkey_gen, pubkey_tweak_add, pubkey_check

from ..include.common import vmsg
from ..include.ecc import pubkey_tweak_add_pyecdsa
from mmgen.protocol import CoinProtocol

secp256k1_group_order = CoinProtocol.Secp256k1.secp256k1_group_order

class unit_tests:

	def pubkey_ops(self, name, ut):
		vmsg('  Generating pubkey, adding scalar 123456789 to pubkey:')
		pk_addend_bytes = int.to_bytes(123456789, length=32, byteorder='big')

		for privkey in (
				'beadcafe' * 8,
				f'{1:064x}',
				f'{secp256k1_group_order-1:x}',
			):
			vmsg(f'  privkey = 0x{privkey}')
			for compressed, length in ((False, 65), (True, 33)):
				vmsg(f'    {compressed=}')
				pubkey_bytes = pubkey_gen(bytes.fromhex(privkey), int(compressed))
				pubkey_check(pubkey_bytes)
				vmsg(f'      pubkey:  {pubkey_bytes.hex()}')

				res1 = pubkey_tweak_add(pubkey_bytes, pk_addend_bytes)
				pubkey_check(res1)
				vmsg(f'      tweaked: {res1.hex()}')

				res2 = pubkey_tweak_add_pyecdsa(pubkey_bytes, pk_addend_bytes)
				pubkey_check(res2)

				assert len(res1) == length
				assert res1 == res2

		return True

	def pubkey_errors(self, name, ut):

		def gen1(): pubkey_gen(bytes(32), 1)
		def gen2(): pubkey_gen(secp256k1_group_order.to_bytes(length=32, byteorder='big'), 1)
		def gen3(): pubkey_gen((secp256k1_group_order+1).to_bytes(length=32, byteorder='big'), 1)
		def gen4(): pubkey_gen(bytes.fromhex('ff'*32), 1)
		def gen5(): pubkey_gen(bytes.fromhex('ab'*31), 1)
		def gen6(): pubkey_gen(bytes.fromhex('ab'*33), 1)

		pubkey_bytes = pubkey_gen(bytes.fromhex('beadcafe'*8), 1)
		def tweak1(): pubkey_tweak_add(pubkey_bytes, bytes(32))
		def tweak2(): pubkey_tweak_add(bytes.fromhex('03'*64), int.to_bytes(1, length=32, byteorder='big'))

		def check1(): pubkey_check(bytes.fromhex('04'*33))
		def check2(): pubkey_check(bytes.fromhex('03'*65))
		def check3(): pubkey_check(bytes.fromhex('02'*65))
		def check4(): pubkey_check(bytes.fromhex('03'*64))
		def check5(): pubkey_check(b'')

		bad_data = (
			('privkey == 0',              'ValueError', 'Private key not in allowable range', gen1),
			('privkey == group order',    'ValueError', 'Private key not in allowable range', gen2),
			('privkey == group order+1',  'ValueError', 'Private key not in allowable range', gen3),
			('privkey == 2^256-1',        'ValueError', 'Private key not in allowable range', gen4),
			('len(privkey) == 31',        'ValueError', 'Private key length not 32 bytes',    gen5),
			('len(privkey) == 33',        'ValueError', 'Private key length not 32 bytes',    gen6),

			('tweak == 0',                'ValueError', 'Tweak not in allowable range',       tweak1),
			('pubkey length == 64',       'ValueError', 'Serialized public key length not',   tweak2),

			('invalid pubkey (33 bytes)', 'ValueError', 'Invalid first byte',                 check1),
			('invalid pubkey (65 bytes)', 'ValueError', 'Invalid first byte',                 check2),
			('invalid pubkey (65 bytes)', 'ValueError', 'Invalid first byte',                 check3),
			('pubkey length == 64',       'ValueError', 'Serialized public key length not',   check4),
			('pubkey length == 0',        'ValueError', 'Serialized public key length not',   check5),
		)

		ut.process_bad_data(bad_data, pfx='')
		return True
