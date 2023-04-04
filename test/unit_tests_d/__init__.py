#!/usr/bin/env python3

"""
test.unit_tests_d.__init__: shared data for unit tests for the MMGen suite
"""

import sys,os

from mmgen.cfg import gv
from ..include.common import cfg

class unit_tests_base:

	def _silence(self):
		if not cfg.verbose:
			self.stdout = sys.stdout
			self.stderr = sys.stderr
			sys.stdout = sys.stderr = gv.stdout = gv.stderr = open(os.devnull,'w')

	def _end_silence(self):
		if not cfg.verbose:
			sys.stdout = gv.stdout = self.stdout
			sys.stderr = gv.stderr = self.stderr
