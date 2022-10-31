import os as overlay_fake_os
from .crypto_orig import *

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:
		get_random = get_random
		add_user_random = add_user_random
		from .test import fake_urandom as urandom

	def get_random(length):
		return overlay_fake_data.urandom(len(overlay_fake_data.get_random(length)))

	def add_user_random(rand_bytes,desc):
		return overlay_fake_data.urandom(len(overlay_fake_data.add_user_random(rand_bytes,desc)))
