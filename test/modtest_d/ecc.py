#!/usr/bin/env python3

"""
test.modtest_d.ecc: elliptic curve unit test for the MMGen suite
"""

from mmgen.proto.secp256k1.secp256k1 import (
	pubkey_gen,
	pubkey_tweak_add,
	pubkey_check,
	sign_msghash,
	pubkey_recover,
	verify_sig)

from ..include.common import vmsg
from ..include.ecc import pubkey_tweak_add_pyecdsa, sign_msghash_pyecdsa, verify_sig_pyecdsa
from mmgen.protocol import CoinProtocol

secp256k1_group_order = CoinProtocol.Secp256k1.secp256k1_group_order

class unit_tests:

	def sig_ops(self, name, ut):
		vmsg('  Creating and verifying signatures and recovering public keys:')
		for mh, pk in (
				(1,                  1),
				(123456789 * 2**222, 12345),
				(123456789 * 2**222, 2**256 - 2**129 - 987654321),
				(9999999,            2**233),
				(12345,              1234 * 2**240),
			):
			msghash = mh.to_bytes(32, 'big')
			privkey = pk.to_bytes(32, 'big')
			vmsg(f'\n   msg:     {msghash.hex()}')
			vmsg(f'   privkey: {privkey.hex()}')
			pubkey = pubkey_gen(privkey, 1)
			sig, recid = sign_msghash(msghash, privkey)
			sig_chk = sign_msghash_pyecdsa(msghash, privkey)
			if sig != sig_chk:
				import time
				from mmgen.util import ymsg
				ymsg(f'Warning: signature ({sig.hex()}) doesn’t match reference value ({sig_chk.hex()})!')
				time.sleep(1)
			vmsg(f'   recid:   {recid}')
			assert recid in (0, 1)
			assert verify_sig(sig, msghash, pubkey) == 1, 'signature verification failed (secp256k1)'
			assert verify_sig_pyecdsa(sig, msghash, pubkey) == 1, 'signature verification failed (ecdsa)'
			pubkey_rec = pubkey_recover(msghash, sig, recid, True)
			assert pubkey == pubkey_rec, f'{pubkey.hex()} != {pubkey_rec.hex()}'
		return True

	def sig_errors(self, name, ut):
		vmsg('  Testing error handling for signature ops')

		msghash = bytes.fromhex('deadbeef' * 8)
		privkey = bytes.fromhex('beadcafe' * 8)
		pubkey = pubkey_gen(privkey, 1)
		sig, recid = sign_msghash(msghash, privkey)

		def sign1(): sign_msghash(1, bytes(32))
		def sign2(): sign_msghash(b'\xff' + bytes(32), bytes(32))
		def sign3(): sign_msghash(bytes(32), bytes(32))

		def verify1(): verify_sig(1, 2, 3)
		def verify2(): verify_sig(bytes(64), bytes(32), bytes(33))
		def verify3(): assert verify_sig(bytes([99]) + sig[1:], msghash, pubkey) == 1, 'bad signature'
		def verify4(): assert verify_sig(sig, msghash, pubkey) == 0, 'good signature'
		def verify5(): verify_sig(sig, msghash + bytes([201]), pubkey)
		def verify6(): verify_sig(sig + bytes([66]), msghash, pubkey)

		def recov1(): pubkey_recover(1, 2, 3)
		def recov2(): pubkey_recover(msghash, sig, 8, True)
		def recov3(): pubkey_recover(msghash, sig, -3, 1)
		def recov4(): pubkey_recover(msghash, bytes([77]) + sig, recid, 1)
		def recov5(): pubkey_recover(msghash + bytes([33]), sig, recid, 1)
		def recov6():
			assert pubkey_recover(msghash[:-1] + bytes([44]), sig, recid, 1) == pubkey, 'bad pubkey'
		def recov7():
			assert pubkey_recover(msghash, sig, recid, True) != pubkey, 'good pubkey'

		bad_data = (
			('sign: bad args',           'ValueError',     'Unable to parse',              sign1),
			('sign: bad msghash len',    'RuntimeError',   'hash length',                  sign2),
			('sign: privkey=0',          'ValueError',     'Private key not in allowable', sign3),
			('verify: bad args',         'ValueError',     'Unable to parse',              verify1),
			('verify: bad pubkey',       'RuntimeError',   'Failed to parse',              verify2),
			('verify: bad sig',          'AssertionError', 'bad signature',                verify3),
			('verify: good sig',         'AssertionError', 'good signature',               verify4),
			('verify: bad msghash len',  'RuntimeError',   'message hash length',          verify5),
			('verify: bad sig len',      'RuntimeError',   'Invalid signature length',     verify6),
			('recover: bad args',        'ValueError',     'Unable to parse',              recov1),
			('recover: bad recid',       'RuntimeError',   'Invalid recovery ID',          recov2),
			('recover: bad recid',       'RuntimeError',   'Invalid recovery ID',          recov3),
			('recover: bad sig len',     'RuntimeError',   'Invalid signature length',     recov4),
			('recover: bad msghash len', 'RuntimeError',   'message hash length',          recov5),
			('recover: bad pubkey',      'AssertionError', 'bad pubkey',                   recov6),
			('recover: bad pubkey',      'AssertionError', 'good pubkey',                  recov7),
		)

		ut.process_bad_data(bad_data, pfx='')
		return True

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
		vmsg('  Testing error handling for public key ops')

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
