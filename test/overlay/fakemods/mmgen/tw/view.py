import os as overlay_fake_os
from . import view_orig as overlay_fake_orig_mod

from .view_orig import *

overlay_fake_orig_mod.CUR_HOME  = '\n[CUR_HOME]\n'
overlay_fake_orig_mod.CUR_UP    = lambda n: f'\n[CUR_UP({n})]\n'
overlay_fake_orig_mod.CUR_DOWN  = lambda n: f'\n[CUR_DOWN({n})]\n'
overlay_fake_orig_mod.ERASE_ALL = '\n[ERASE_ALL]\n'

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:
		# add a minute to each successive time value
		time_iter = (1862651471 + (i*60) for i in range(1000000))

	TwView.date_formatter = {
		'days':      lambda rpc, secs: (next(overlay_fake_data.time_iter) - secs) // 86400,
		'date':      lambda rpc, secs: '{}-{:02}-{:02}'.format(
			*time.gmtime(next(overlay_fake_data.time_iter))[:3])[2:],
		'date_time': lambda rpc, secs: '{}-{:02}-{:02} {:02}:{:02}'.format(
			*time.gmtime(next(overlay_fake_data.time_iter))[:5]),
	}

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	# 1831006505 (09 Jan 2028) = projected time of block 1000000
	TwView.date_formatter['days'] = lambda rpc, secs: (2178144000 - secs) // 86400 # 9 Jan 2039 00:00:00
