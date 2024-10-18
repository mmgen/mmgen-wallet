#!/usr/bin/env python3

"""
test.modtest_d.ut_scrypt: password hashing unit test for the MMGen suite
"""

from mmgen.util import msg, msg_r

from ..include.common import cfg, qmsg, vmsg, omsg_r, silence, end_silence

class unit_test:

	def run_test(self, name, ut):
		import time

		msg_r('Testing password hashing...')
		qmsg('')

		from mmgen.crypto import Crypto
		crypto = Crypto(cfg)

		salt = bytes.fromhex('f00f' * 16)

		presets = {
			'1': '64898d01ffcea1252c17411e7bd6c12d00191ee8ddcbf95420e5de8f37a7a1cb',
			'2': '625d0c59fcbcf85eca51b4337d3a4952e554c7c95fe32f4199ad0e9e9370e279',
			'3': 'b30a5cf0e606515be4a983cc4a1a4c21e04806f19aaa0ad354a353c83aecd3ee',
			'4': 'a3a1b99393734510b68adf2c2cfdc627a2bc3281913d8ea6fbb677d39781a9fa',
			'5': '0c7e1a672738cee49cf0ff6f3208190ca418e741835fd6995ce9558cc19f3f04',
			'6': '91f9d1c9baf3948433dab58dcc912d96035392c1db21ede96d2f369e025ab06d',
			'7': 'fcb2cd05268de43b0d2d45f78a56e5d446b0bd2d3b57bdbc77cc17a42942f1bd'
		}

		pws = (
			('',      'cc8d99ce7365d8a9d2422d71ce330e130b2cade46a8cc0459a3f83e1a6ac3d30'),
			('foo',   'f0e2cce1d9980edf2373a2070ad3560c2506faf9bc50704a1bc5cdb3c7f63f3b'),
			('φυβαρ', '64898d01ffcea1252c17411e7bd6c12d00191ee8ddcbf95420e5de8f37a7a1cb')
		)

		def test_passwords():
			for pw_base, res in pws:
				for pw in (pw_base, pw_base.encode()):
					pw_disp = "'"+pw+"'" if isinstance(pw, str) else "b'"+pw.decode()+"'"
					if cfg.quiet:
						omsg_r('.')
					else:
						msg_r(f'\n  password {pw_disp:9} ')
					ret = crypto.scrypt_hash_passphrase(pw, salt, '1').hex()
					assert ret == res, ret

		def test_presets(do_presets):
			for hp in do_presets:
				hp = str(hp)
				res = presets[hp]
				pw = 'φυβαρ'
				if cfg.quiet:
					omsg_r('.')
				else:
					msg_r(f'\n  {hp!r:3}: {crypto.hash_presets[hp]!r:12}  ')
				st = time.time()
				ret = crypto.scrypt_hash_passphrase(pw, salt, hp).hex()
				t = time.time() - st
				vmsg('' if cfg.test_suite_deterministic else f'  {t:0.4f} secs')
				assert ret == res, ret

		if cfg.quiet:
			silence()

		cfg.force_standalone_scrypt_module = False
		vmsg('Passwords (auto module selection):')
		test_passwords()
		vmsg('Hash presets (auto module selection):')
		test_presets((1, 2, 3, 4) if cfg.fast else (1, 2, 3, 4, 5, 6, 7))

		cfg.force_standalone_scrypt_module = True
		vmsg('Passwords (force standalone scrypt module):')
		test_passwords()
		vmsg('Hash presets (force standalone scrypt module):')
		test_presets((1, 2, 3))

		if cfg.quiet:
			end_silence()

		msg('OK')
		return True
