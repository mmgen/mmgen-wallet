import os as overlay_fake_os
from .util2_orig import *

if overlay_fake_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):

	class overlay_fake_data:
		format_elapsed_hr = format_elapsed_hr
		format_elapsed_days_hr = format_elapsed_days_hr

	def format_elapsed_hr(t, now=None, cached={}):
		return overlay_fake_data.format_elapsed_hr(t, now=2204622671, cached=cached) # 11 Nov 2039 11:11:11

	def format_elapsed_days_hr(t, now=None, cached={}):
		return overlay_fake_data.format_elapsed_days_hr(t, now=2204622671, cached=cached)
