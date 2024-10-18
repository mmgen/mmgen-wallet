import os as overlay_fake_os
from .util_orig import *

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:
		make_timestamp = make_timestamp
		make_timestr = make_timestr
		time_iter = (1862651471 + (i*60) for i in range(1000000)) # 9 Jan 2029 11:11:11

	def make_timestamp(secs=None):
		return overlay_fake_data.make_timestamp(next(overlay_fake_data.time_iter))

	def make_timestr(secs=None):
		return overlay_fake_data.make_timestr(next(overlay_fake_data.time_iter))
