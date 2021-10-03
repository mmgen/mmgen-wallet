from .crypto_orig import *

if os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):
	get_random_orig = get_random
	add_user_random_orig = add_user_random

	fake_rand_h = sha256('.'.join(sys.argv).encode())
	def fake_urandom(n):

		def gen(rounds):
			for i in range(rounds):
				fake_rand_h.update(b'foo')
				yield fake_rand_h.digest()

		return b''.join(gen(int(n/32)+1))[:n]

	def get_random(length):
		return fake_urandom(len(get_random_orig(length)))

	def add_user_random(rand_bytes,desc):
		return fake_urandom(len(add_user_random_orig(rand_bytes,desc)))
