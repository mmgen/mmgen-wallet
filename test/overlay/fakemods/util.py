from .util_orig import *

if os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):
	make_timestamp_orig = make_timestamp
	make_timestr_orig = make_timestr

	def make_timestamp(secs=None):
		return make_timestamp_orig(1321009871)

	def make_timestr(secs=None):
		return make_timestr_orig(1321009871)
