import os as overlay_fake_os
from .util_orig import *

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:
		make_timestamp = make_timestamp
		make_timestr = make_timestr

	def make_timestamp(secs=None):
		return overlay_fake_data.make_timestamp(1321009871)

	def make_timestr(secs=None):
		return overlay_fake_data.make_timestr(1321009871)
