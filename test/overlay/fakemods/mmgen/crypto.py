import os as overlay_fake_os
from .crypto_orig import *

class overlay_fake_Crypto:

	def get_aes_ctr_pyaes(self, key, iv):
		import pyaes
		class MyAES(pyaes.AESModeOfOperationCTR):
			update = pyaes.AESModeOfOperationCTR.encrypt
			@staticmethod
			def finalize():
				return b''
		return MyAES(key, pyaes.Counter(int.from_bytes(iv)))

Crypto.aes_backends = ('cryptography', 'pyaes')
Crypto.get_aes_ctr_pyaes = overlay_fake_Crypto.get_aes_ctr_pyaes

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	overlay_fake_get_random_orig = Crypto.get_random
	overlay_fake_add_user_random_orig = Crypto.add_user_random

	from .test import fake_urandom as overlay_fake_urandom

	Crypto.get_random = lambda self, length: overlay_fake_urandom(
		len(overlay_fake_get_random_orig(self, length)))

	Crypto.add_user_random = lambda self, rand_bytes, *, desc, osrand_bytes=32: overlay_fake_urandom(
		len(overlay_fake_add_user_random_orig(self, rand_bytes, desc=desc, osrand_bytes=osrand_bytes)))
