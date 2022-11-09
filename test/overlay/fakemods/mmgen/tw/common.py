import os as overlay_fake_os
from .common_orig import *

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:
		# add a minute to each successive time value
		time_iter = (1321009871 + (i*60) for i in range(1000000))

	TwCommon.date_formatter = {
		'days':      lambda rpc,secs: (next(overlay_fake_data.time_iter) - secs) // 86400,
		'date':      lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(next(overlay_fake_data.time_iter))[:3])[2:],
		'date_time': lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(next(overlay_fake_data.time_iter))[:5]),
	}

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	# 1831006505 (09 Jan 2028) = projected time of block 1000000
	TwCommon.date_formatter['days'] = lambda rpc,secs: (1831006505 - secs) // 86400
