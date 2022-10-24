import os as overlay_fake_os
from .crypto_orig import *

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:

		import sys
		from hashlib import sha256
		rand_h = sha256('.'.join(sys.argv).encode())

		get_random = get_random
		add_user_random = add_user_random

		def urandom(n):

			def gen(rounds):
				for i in range(rounds):
					overlay_fake_data.rand_h.update(b'foo')
					yield overlay_fake_data.rand_h.digest()

			return b''.join(gen(int(n/32)+1))[:n]

	def get_random(length):
		return overlay_fake_data.urandom(len(overlay_fake_data.get_random(length)))

	def add_user_random(rand_bytes,desc):
		return overlay_fake_data.urandom(len(overlay_fake_data.add_user_random(rand_bytes,desc)))
